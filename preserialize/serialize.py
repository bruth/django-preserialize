import warnings
from django.db import models
from django.conf import settings
from django.db.models.query import QuerySet
from .utils import get_field_value, parse_selectors, convert_to_camel

PRESERIALIZE_OPTIONS = getattr(settings, 'PRESERIALIZE_OPTIONS', {})

DEFAULT_OPTIONS = {
    'aliases': {},
    'allow_missing': False,
    'camelcase': False,
    'prefix': '',
    'process': None,
    'values_list': False,
    'flat': True,
    'merge': False,
    'prehook': False,
    'posthook': False,
}


def _defaults(options):
    if 'key_map' in options and 'aliases' not in options:
        warnings.warn('The "key_map" option has been renamed to "aliases"',
                      DeprecationWarning)
        options['aliases'] = options.pop('key_map')

    if 'key_prefix' in options and 'prefix' not in options:
        warnings.warn('The "key_prefix" option has been renamed to "prefix"',
                      DeprecationWarning)
        options['prefix'] = options.pop('key_prefix')

    defaults = DEFAULT_OPTIONS.copy()

    # Update with settings-based options
    defaults.update(PRESERIALIZE_OPTIONS)

    # Update with current options
    defaults.update(options)

    if 'fields' not in defaults:
        defaults['fields'] = []

    if 'related' not in defaults:
        defaults['related'] = {}

    return defaults


def model_to_dict(instance, **options):
    "Takes a model instance and converts it into a dict."

    options = _defaults(options)
    attrs = {}

    if options['prehook']:
        if callable(options['prehook']):
            instance = options['prehook'](instance)
            if instance is None:
                return attrs

    # Items in the `fields` list are the output aliases, not the raw
    # accessors (field, method, property names)
    for alias in options['fields']:

        # Get the accessor for the object
        accessor = options['aliases'].get(alias, alias)

        # Create the key that will be used in the output dict
        key = options['prefix'] + alias

        # Optionally camelcase the key
        if options['camelcase']:
            key = convert_to_camel(key)

        # Get the field value. Use the mapped value to the actually property or
        # method name. `value` may be a number of things, so the various types
        # are checked below.
        value = get_field_value(instance, accessor,
                                allow_missing=options['allow_missing'])

        # Related objects, perform some checks on their options
        if isinstance(value, (models.Model, QuerySet)):
            _options = _defaults(options['related'].get(accessor, {}))

            # If the `prefix` follows the below template, generate the
            # `prefix` for the related object
            if '%(accessor)s' in _options['prefix']:
                _options['prefix'] = _options['prefix'] % {'accessor': alias}

            if isinstance(value, models.Model):
                if len(_options['fields']) == 1 and _options['flat'] \
                        and not _options['merge']:
                    value = serialize(value, **_options).values()[0]
                else:
                    # Recurse, get the dict representation
                    _attrs = serialize(value, **_options)

                    # Check if this object should be merged into the parent,
                    # otherwise nest it under the accessor name
                    if _options['merge']:
                        attrs.update(_attrs)
                        continue

                    value = _attrs
            else:
                value = serialize(value, **_options)

        attrs[key] = value

    # Apply post-hook to serialized attributes
    if options['posthook']:
        attrs = options['posthook'](instance, attrs)

    return attrs


def queryset_to_list(queryset, **options):
    options = _defaults(options)

    if options['prehook']:
        if callable(options['prehook']):
            queryset = options['prehook'](queryset)
            if queryset is None:
                return []
        else:
            queryset = queryset.filter(**options['prehook'])
        options['prehook'] = False

    # If the `select_related` option is defined, update the `QuerySet`
    if 'select_related' in options:
        queryset = queryset.select_related(*options['select_related'])

    if options['values_list']:
        fields = options['fields']

        # Flatten if only one field is being selected
        if len(fields) == 1:
            queryset = queryset.values_list(fields[0], flat=options['flat'])
        else:
            queryset = queryset.values_list(*fields)
        return list(queryset)

    return map(lambda x: model_to_dict(x, **options),
               queryset.iterator())


def serialize(obj, fields=None, exclude=None, **options):
    """Recursively attempts to find ``Model`` and ``QuerySet`` instances
    to convert them into their representative datastructure per their
    ``Resource`` (if one exists).
    """

    # Handle model instances
    if isinstance(obj, models.Model):
        fields = parse_selectors(obj.__class__, fields, exclude, **options)
        return model_to_dict(obj, fields=fields, **options)

    # Handle querysets
    if isinstance(obj, QuerySet):
        fields = parse_selectors(obj.model, fields, exclude, **options)
        return queryset_to_list(obj, fields=fields, **options)

    # Handle dict instances
    if isinstance(obj, dict):
        exclude = exclude or []
        if not fields:
            fields = obj.iterkeys()
        fields = [x for x in fields if x not in exclude]
        return model_to_dict(obj, fields=fields, **options)

    # Handle other iterables
    if hasattr(obj, '__iter__'):
        return map(lambda x: serialize(x, fields, exclude, **options), obj)

    return obj
