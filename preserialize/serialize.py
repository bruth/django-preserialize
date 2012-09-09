from django.db import models
from django.db.models.query import QuerySet
from .utils import get_field_value, parse_selectors, convert_to_camel


def model_to_dict(obj, fields, **options):
    """Takes a model object or queryset and converts it into a native object
    given the list of attributes either local or related to the object.
    """
    obj_dict = {}
    related = options.get('related', {})
    key_map = options.get('key_map', {})
    camelcase = options['camelcase']
    prefix = options.get('key_prefix', '')

    for alias in fields:
        actual = key_map.get(alias, alias)
        # Create the key that will be used in the output dict
        key = camelcase(prefix + alias)

        # Get the field value. Use the mapped value to the actually property or
        # method name. `value` may be a number of things, so the various types
        # are checked below.
        value = get_field_value(obj, actual)

        # Related objects, perform some checks on their options
        if isinstance(value, (models.Model, QuerySet)):
            rel_options = related.get(actual, {})
            # Propagate `camelcase` option by default
            rel_options.setdefault('camelcase', camelcase)

            rel_prefix = rel_options.get('key_prefix', '')

            # If the `key_prefix` follows the below template, generate the
            # `key_prefix` for the related object
            if rel_prefix and '%(accessor)s' in rel_prefix:
                rel_options['key_prefix'] = rel_prefix % {'accessor': alias}

            if isinstance(value, models.Model):
                # Recursve, get the dict representation
                rel_obj_dict = serialize(value, **rel_options)

                # Check if this object should be merged into the parent object,
                # otherwise nest it under the accessor name
                if rel_options.get('merge', False):
                    obj_dict.update(rel_obj_dict)
                else:
                    obj_dict[key] = rel_obj_dict
            else:
                obj_dict[key] = serialize(value, **rel_options)
        else:
            obj_dict[key] = value

    return obj_dict


def queryset_to_list(queryset, fields, **options):
    # If the `select_related` option is defined, update the `QuerySet`
    if 'select_related' in options:
        queryset = queryset.select_related(*options['select_related'])

    if options.get('values_list', False):
        # Flatten if only one field is being selected
        if len(fields) == 1:
            flat = options.get('flat', True)
            queryset = queryset.values_list(fields[0], flat=flat)
        else:
            queryset = queryset.values_list(*fields)
        return list(queryset)

    return map(lambda x: model_to_dict(x, fields, **options),
            queryset.iterator())

def serialize(obj, fields=None, exclude=None, **options):
    """Recursively attempts to find ``Model`` and ``QuerySet`` instances
    to convert them into their representative datastructure per their
    ``Resource`` (if one exists).
    """
    camelcase = options.get('camelcase', False)
    # Explicit check for boolean value since during recursion, the function
    # will be propagated (if unchanged)
    if camelcase is True:
        options['camelcase'] = convert_to_camel
    elif camelcase is False:
        options['camelcase'] = lambda x: x

    # Handle model instances
    if isinstance(obj, models.Model):
        fields = parse_selectors(obj.__class__, fields, exclude, **options)
        return model_to_dict(obj, fields, **options)

    # Handle querysets
    if isinstance(obj, QuerySet):
        fields = parse_selectors(obj.model, fields, exclude, **options)
        return queryset_to_list(obj, fields, **options)

    # Handle dict instances
    if isinstance(obj, dict):
        exclude = exclude or []
        if not fields:
            fields = obj.iterkeys()
        fields = [x for x in fields if x not in exclude]
        return model_to_dict(obj, fields, **options)

    # Handle other iterables
    if hasattr(obj, '__iter__'):
        return map(lambda x: serialize(x, fields, exclude, **options), obj)
