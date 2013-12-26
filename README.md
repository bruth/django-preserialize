# django-preserialize

[![Build Status](https://travis-ci.org/bruth/django-preserialize.png)](https://travis-ci.org/bruth/django-preserialize) [![Coverage Status](https://coveralls.io/repos/bruth/django-preserialize/badge.png?branch=master)](https://coveralls.io/r/bruth/django-preserialize?branch=master) [![Bitdeli Badge](https://d2weczhvl823v0.cloudfront.net/bruth/django-preserialize/trend.png)](https://bitdeli.com/free "Bitdeli Badge")

django-preserialize is a one-stop shop for ensuring an object is free of `Model` and `QuerySet` instances. By default, all non-relational fields will be included as well as the primary keys of local related fields. The resulting containers will simply be `dict`s and `list`s.

## Install

```bash
pip install django-preserialize
```

## Docs

A serialized user object might look like this:

```python
>>> from preserialize.serialize import serialize
>>> serialize(user)
{
    'date_joined': datetime.datetime(2009, 5, 16, 15, 52, 40),
    'email': u'jon@doe.com',
    'first_name': u'Jon',
    'groups': [5],
    'id': 1,
    'is_active': True,
    'is_staff': True,
    'is_superuser': True,
    'last_login': datetime.datetime(2012, 3, 3, 17, 40, 41, 927637),
    'last_name': u'Doe',
    'password': u'!',
    'user_permissions': [1, 2, 3],
    'username': u'jdoe'
}
```

This can then be passed off to a serializer/encoder, e.g. JSON, to turn
it into a string for the response body (or whatever else you want to do).

## Serialize Options

Some fields may not be appropriate or relevent to include as output.
To customize which fields get included or excluded, the
following arguments can be passed to ``serialize``:

**`fields`**

A list of fields names to include. Method names can also be specified that will be called when being serialized. Default is all local fields and local related fields. See also: `exclude`, `aliases`

**`exclude`**

A list of fields names to exclude (this takes precedence over fields). Default is `None`. See also: `fields`, `aliases`

**`related`**

A dict of related object accessors and configs (see below) for handling related objects.

**`values_list`**

This option only applies to `QuerySet`s. Returns a list of lists with the field values (like Django's `ValuesListQuerySet`). Default is `False`.

**`flat`**

Applies only if one field is specified in `fields`. If applied to a `QuerySet` and if `values_list` is `True` the values will be flattened out. If applied to a model instance, the single field value will used (in place of the dict). Note, if `merge` is true, this option has not effect. Default is `True`.

**`prefix`**

A string to be use to prefix the dict keys. To enable dynamic prefixes, the prefix may contain `'%(accessor)s'` which will be the class name for top-level objects or the accessor name for related objects. Default is `None`.

**`aliases`**

A dictionary that maps the keys of the output dictionary to the actual field/method names referencing the data. Default is `None`. See also: `fields`

**`camelcase`**

Converts all keys to a camel-case equivalent. This is merely a convenience for conforming to language convention for consumers of this content, namely JavaScript. Default is `False`.

**`allow_missing`**

Allow for missing fields (rather than throwing an error) and fill in the value with `None`.

### Hooks

Hooks enable altering the objects that are serialized at each level.

**`prehook`**



A function that takes and returns an object. For `QuerySet`s it can be used for filtering or annotating additional data to each model instance. For `Model` instances it can be prefetching additional data, swapping out an instance or whatever is necessary prior to serialization.

Since filtering `QuerySet`s is a common use case, a simple dict can be supplied instead of a function that will be passed to the `filter` method.

Here are two examples for filtering `posts` by the requesting user.

The shorthand method of using a `dict`:

```python
def view(request):
    template = {
        'related': {
            'posts': {
                'prehook': {'user': request.user},
            }
        }
    }
    ...
```

For applying conditional logic, a function can be used:

```python
from functools import partial

def filter_by_user(queryset, request):
    if not request.user.is_superuser:
        queryset = queryset.filter(user=request.user)
    return queryset

def view(request):
    template = {
        'related': {
            'posts': {
                'prehook': partial(filter_by_user, request=request)
            }
        }
    }
    ...
```

**`posthook`**

A function that takes the original model instance and the serialized attrs for post-processing. This is specifically useful for augmenting or modifying the data prior to being added to the large serialized data structure.

Even if the related object (like `posts` above) is a `QuerySet`, this hook is applied per object in the `QuerySet`. This is because it would rarely ever be necessary to process a list of objects as a whole since filtering can already be performed above (using the `prehook`) prior to serialization.

Here is an example of adding resource links to the output data based on the serialized attributes:

```python
from functools import partial
from django.core.urlresolvers import reverse

def add_resource_links(instance, attrs, request):
    uri = request.build_absolute_uri
    attrs['_links'] = {
        'self': {
            'href': uri(reverse('api:foo:bar', kwargs={'pk': attrs.id})),
        },
        ...
    }
    return attrs

template = {
    'posthook': partial(add_resource_links, request=request),
    ...
}
```

### Examples

```python
# The field names listed are after the mapping occurs
>>> serialize(user, fields=['username', 'full_name'], aliases={'full_name': 'get_full_name'}, camelcase=True)
{
    'fullName': u'Jon Doe',
    'username': u'jdoe'
}

>>> serialize(user, exclude=['password', 'groups', 'permissions'])
{
    'date_joined': datetime.datetime(2009, 5, 16, 15, 52, 40),
    'email': u'jon@doe.com',
    'first_name': u'Jon',
    'id': 1,
    'is_active': True,
    'is_staff': True,
    'is_superuser': True,
    'last_login': datetime.datetime(2012, 3, 3, 17, 40, 41, 927637),
    'last_name': u'Doe',
    'username': u'jdoe'
}

>>> serialize(user, fields=['foo', 'bar', 'baz'], allow_missing=True)
{
    'foo': None,
    'bar': None,
    'baz': None,
}
```

## Related Objects

Composite resources are common when dealing with data that have _tight_ relationships. A user and their user profile is an example of this. It is inefficient for a client to have to make two separate requests for data that is typically always consumed together.

`serialize` supports the `related` keyword argument for defining options for relational fields. The following additional argument (to the above) may be defined:

**`merge`**

This option only applies to local `ForeignKey` or `OneToOneField`. This allows for merging the related object's fields into the parent object.

```python
>>> serialize(user, related={'groups': {'fields': ['name']}, 'profile': {'merge': True}})
{
    'username': u'jdoe',
    'groups': [{
        'name': u'Managers'
    }]
    # profile attributes merged into the user
    'twitter': '@jdoe',
    'mobile': '123-456-7890',
    ...
}
```

## Conventions

**Define a template dict for each model that will be serialized.**

Defining a _template_ enables reuse across different serialized objects as well as increases readability and maintainability. Deconstructing the above example, we have:

```python
# Render a list of group names.. note that 'values_list'
# options is implied here since there is only one field
# specified. It is here to be explicit.
group_template = {
    'fields': ['name'],
    'values_list': True,
}

# User profiles are typically always wanted to be merged into
# User, so we can add the 'merge' option. Remember this simply
# gets ignored if 'UserProfile' is the top-level object being
# serialized.
profile_template = {
    `exclude`: ['user'],
    'merge': True,
}

# Users typically always include some related data (groups and their
# profile), so we can reference the above templates in this one.
user_template = {
    'exclude': ['password', 'user_permissions'],
    'related': {
        'groups': group_template,
        'profile': profile_template,
    }
}

# Everyone is the pool!
users = User.objects.all()
# Now we can use Python's wonderful argument _unpacking_ syntax.
# Clean.
serialize(users, **user_template)
```

## FAQ

### Does the serializer only understand model fields?

No. In fact it is smart about accessing the _field_. The following steps are taken when attempting to get the value:

1. Use `hasattr` to check if an attribute/property is present
2. If the object support `__getitem__`, check if the key is present

Assuming one of those two methods succeed, it will check if the value is callable and will call it (useful for methods). If the value is a `RelatedManager`, it will resolve the `QuerySet` and recursive downstream.

### Does the serializer only support model instances?

No. It is not always the case that a single model instance or queryset is the source of data for a resource. `serialize` also understands `dict`s and any iterable of `dict`s. They will be treated similarly to the model instances.

### My model has a ton of fields and I don't want to type them all out. What do I do?

The `fields` and `exclude` options understands four _pseudo-selectors_ which can be used in place of typing out all of a model's field names (although being explicit is typically better).

**`:pk`**

The primary key field of the model

**`:local`**

All local fields on a model (including local foreign keys and
many-to-many fields)

**`:related`**

All related fields (reverse foreign key and many-to-many)

**`:all`**

A composite of all selectors above and thus any an all fields on or related to a model

You can use them like this:

```python
# The two selectors here are actually the default, but defined
# for the example.
serialize(user, fields=[':pk', ':local', 'foo'], exclude=['password'])
```

## CHANGELOG

2013-05-01

- Update `posthook` to take the original instance as the first argument and the serialized data as the second argument
- Ensure the passed object is returned from `serialize` even if it does not qualify to be processed

2013-04-29

- Fix bug where the `flat` option was not respecting `merge`
    - If `merge` is set, it takes precedence over flat

2013-04-28

- Add `prehook` and `posthook` options
- Add support for `flat` option for model instances with a single field
- Rename `key_map` to `aliases` for clarity
- Rename `key_prefix` to `prefix`
    - It is implied the prefix applies to the keys since this a serialization
    utility
- Internal clean up
- Correct documentation regarding the `flat` option
    - It was incorrectly named `flatten`
