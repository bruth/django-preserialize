# django-preserialize

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

:    A list of fields names to include. Method names can also be specified that will be called when being serialized. Default is all local fields and local related fields. See also: `exclude`, `key_map`

**`exclude`**

:    A list of fields names to exclude (this takes precedence over fields). Default is `None`. See also: `fields`, `key_map`

**`related`**

:    A dict of related object accessors and configs (see below) for handling related objects.

**`values_list`**

:    This option only applies to `QuerySet`s. Returns a list of lists with the field values (like Django's `ValuesListQuerySet`). Default is `False`.

**`flatten`**

:    Applies only if `values_list` is `True` and one field is specified. If `True`, flattens out the list of lists into a single list of  values. Default is `True`.

**`key_prefix`**

:    A string to be use to prefix the dict keys. To enable dynamic prefixes, the prefix may contain `'%(accessor)s'` which will be the class name for top-level objects or the accessor name for related objects. Default is `None`.

**`key_map`**

:    A dictionary that maps the keys of the output dictionary to the actual field/method names referencing the data. Default is `None`. See also: `fields`

**`camelcase`**

:    Converts all keys to a camel-case equivalent. This is merely a convenience for conforming to language convention for consumers of this content, namely JavaScript. Default is `False`.

**`allow_missing`**

:   Allow for missing fields (rather than throwing an error) and fill in the value with `None`.

### Examples

```python
# The field names listed are after the mapping occurs
>>> serialize(user, fields=['username', 'full_name'], key_map={'full_name': 'get_full_name'}, camelcase=True)
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

:    This option only applies to local `ForeignKey` or `OneToOneField`. This allows for merging the related object's fields into the parent object.

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

:    The primary key field of the model

**`:local`**

:    All local fields on a model (including local foreign keys and
many-to-many fields)

**`:related`**

:    All related fields (reverse foreign key and many-to-many)

**`:all`**

:    A composite of all selectors above and thus any an all fields on or related to a model

You can use them like this:

```python
# The two selectors here are actually the default, but defined
# for the example.
serialize(user, fields=[':pk', ':local', 'foo'], exclude=['password'])
```
