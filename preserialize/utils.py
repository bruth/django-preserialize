import collections
from django.db import models
from django.db.models.fields import Field
from django.db.models import FieldDoesNotExist


PSEUDO_SELECTORS = (':all', ':pk', ':local', ':related')
DEFAULT_SELECTORS = (':pk', ':local')


def convert_to_camel(s):
    if '_' not in s:
        return s
    toks = s.split('_')
    return toks[0] + ''.join(x.title() for x in toks[1:] if x.upper() != x)


class ModelFieldResolver(object):
    cache = {}

    def _get_pk_field(self, model):
        fields = (model._meta.pk,)
        names = tuple([x.name for x in fields])

        return {
            ':pk': dict(list(zip(names, fields))),
        }

    def _get_all_related_objects(self, model):
        return [
            f for f in model._meta.get_fields()
            if (f.one_to_many or f.one_to_one)
            and f.auto_created and not f.concrete
        ]

    def _get_all_related_many_to_many_objects(self, model):
        return [
            f for f in model._meta.get_fields(include_hidden=True)
            if f.many_to_many and f.auto_created
        ]

    def _get_local_fields(self, model):
        "Return the names of all locally defined fields on the model class."
        local = [f for f in model._meta.fields]
        m2m = [f for f in model._meta.many_to_many]
        fields = local + m2m
        names = tuple([x.name for x in fields])

        return {
            ':local': dict(list(zip(names, fields))),
        }

    def _get_related_fields(self, model):
        "Returns the names of all related fields for model class."
        reverse_fk = self._get_all_related_objects(model)
        reverse_m2m = self._get_all_related_many_to_many_objects(model)

        fields = tuple(reverse_fk + reverse_m2m)
        names = tuple([x.get_accessor_name() for x in fields])

        return {
            ':related': dict(list(zip(names, fields))),
        }

    def _get_fields(self, model):
        if model not in self.cache:
            fields = {}
            fields.update(self._get_pk_field(model))
            fields.update(self._get_local_fields(model))
            fields.update(self._get_related_fields(model))

            all_ = {}
            for x in list(fields.values()):
                all_.update(x)

            fields[':all'] = all_

            self.cache[model] = fields

        return self.cache[model]

    def get_field(self, model, attr):
        fields = self._get_fields(model)

        # Alias to model fields
        if attr in PSEUDO_SELECTORS:
            return list(fields[attr].keys())

        # Assume a field or property
        return attr


resolver = ModelFieldResolver()


def parse_selectors(model, fields=None, exclude=None, key_map=None, **options):
    """Validates fields are valid and maps pseudo-fields to actual fields
    for a given model class.
    """
    fields = fields or DEFAULT_SELECTORS
    exclude = exclude or ()
    key_map = key_map or {}
    validated = []

    for alias in fields:
        # Map the output key name to the actual field/accessor name for
        # the model
        actual = key_map.get(alias, alias)

        # Validate the field exists
        cleaned = resolver.get_field(model, actual)

        if cleaned is None:
            raise AttributeError('The "{0}" attribute could not be found '
                                 'on the model "{1}"'.format(actual, model))

        # Mapped value, so use the original name listed in `fields`
        if type(cleaned) is list:
            validated.extend(cleaned)
        elif alias != actual:
            validated.append(alias)
        else:
            validated.append(cleaned)

    return tuple([x for x in validated if x not in exclude])


def get_field_value(obj, name, allow_missing=False):
    value = None

    if hasattr(obj, name):
        value = getattr(obj, name)

        # Check if the name of is field on the model and get the prep
        # value if it is a Field instance.
        if isinstance(obj, models.Model):
            try:
                field = obj._meta.get_field(name)

                if isinstance(field, Field) and field.__class__.__name__ \
                        not in ('JSONField',):
                    value = field.get_prep_value(value)
            except FieldDoesNotExist:
                pass

    elif hasattr(obj, '__getitem__') and name in obj:
        value = obj[name]

    elif not allow_missing:
        raise ValueError('{} has no attribute {}'.format(obj, name))

    # Handle a local many-to-many or a reverse foreign key
    if value.__class__.__name__ in ('RelatedManager', 'ManyRelatedManager',
                                    'GenericRelatedObjectManager'):
        value = value.all()

    # Check for callable
    elif isinstance(value, collections.Callable):
        value = value()

    return value
