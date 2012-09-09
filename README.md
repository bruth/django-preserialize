# django-preserialize

django-preserialize is a one-stop shop for ensuring an object is free of
`Model` and `QuerySet` instances. By default, all non-relational fields
will be included as well as the primary keys of local related fields.
The result will be simply `dict`s and `list`s.

_Have a better name? Give me a suggestion!_

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

## Options

Some fields may not be appropriate or relevent to include in the
response. To customize which fields get included or excluded, the
following arguments can be passed to ``serialize``:

* `fields` - A list of fields names to include. Method names can also be
specified that will be called when being serialized. Default is all local 
fields and local related fields. See also: `exclude`, `key_map`
* `exclude` - A list of fields names to exclude (this takes precedence
over fields). Default is `None`. See also: `fields`, `key_map`
* `related` - A dict of related object accessor and configs (see below) for
handling related object.
* `values_list` - This option only applies to `QuerySet`s. Returns a list of
lists with the field values (like Django's `ValuesListQuerySet`). Default 
is `False`.
* `flatten` - Applies only if `values_list` is `True` and one field is 
specified. If `True`, flattens out the list of lists into a single list of 
values. Default is `True`.
* `key_prefix` - A string to be use to prefix the dict keys. To enable 
dynamic prefixes, the prefix may contain `'%(accessor)s' which will be the 
class name for top-level objects or the accessor name for related objects. 
Default is `None`.
* `key_map` - A dictionary that maps the keys of the output dictionary to 
the actual field/method names referencing the data. Default is `None`.  See 
also: `fields`
* `camelcase` - Converts all keys to a camel-case equivalent. This is 
merely a convenience for conforming to language convention for consumers of 
this content, namely JavaScript. Default is `False`.

### Examples

```python
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
```

## Related Objects

Composite resources are common when dealing with data with tight
relationships. A user and their user profile is an example of this. It is 
inefficient for a client to have to make two separate requests for data 
that is typically always consumed together.

`serialize` supports the `related` keyword argument for defining options for
relational fields. The following additional attributes (to the above) may be
defined:

* `merge` - This option only applies to local `ForeignKey` or 
`OneToOneField`. This allows for merging this object's fields into the 
parent object.

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

**Define a `data_template` dict for each model that will be serialized.**

Defining a `data_template` enables reuse across different serialized
objects. Deconstructing the above example, we have:

```python
# Render a list of group names.. note that 'values_list'
# options is implied here since there is only one field
# specified. It is here to be explicit.
group_template = {
    'fields': ['name'],
    'values_list': True,
}

# User profiles are typically only wanted to be merge into
# User, so we can add the 'merge' option. Remember this simply
# gets ignored if 'UserProfile' is the top-level object being
# serialized.
profile_template = {
    'merge': True
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
# Now we can use Python's wonderful argument _unpacking_ syntax. Clean.
serialize(users, **user_template)
```

## Niceties

### Mixed Types

It is not always the case that a single model instance or queryset is the
source of data for a resource. `preserialize.serialize` also understands
`dict`s and any iterable of `dict`s. They will be treated similarly to the
model instances.

### Pseudo-selectors

The `fields` and `exclude` options understands four _pseudo-selectors_ which
can be used in place of typing out all of a model's field names (although
being explicit is always better).

- `:pk` - the primary key field of the model
- `:local` - all local fields on a model (including local foreign keys and
many-to-many fields)
- `:related` - all related fields (reverse foreign key and many-to-many)
- `:all` - a composite of all selectors above and thus any an all fields
on or related to a model

You can use them like this:

```python
# The two selectors here are actually the default, but defined
# for the example.
serialize(user, fields=[':pk', ':local'], exclude=['password'])
```

For those curious, try this:

```python
>>> from pprint import pprint
>>> from preserialize.utils import resolver
>>> pprint(resolver._get_fields(User))
{':all': {'date_joined': <django.db.models.fields.DateTimeField: date_joined>,
          'email': <django.db.models.fields.EmailField: email>,
          'first_name': <django.db.models.fields.CharField: first_name>,
          'groups': <django.db.models.fields.related.ManyToManyField: groups>,
          'id': <django.db.models.fields.AutoField: id>,
          'is_active': <django.db.models.fields.BooleanField: is_active>,
          'is_staff': <django.db.models.fields.BooleanField: is_staff>,
          'is_superuser': <django.db.models.fields.BooleanField: is_superuser>,
          'last_login': <django.db.models.fields.DateTimeField: last_login>,
          'last_name': <django.db.models.fields.CharField: last_name>,
          'logentry_set': <RelatedObject: admin:logentry related to user>,
          'password': <django.db.models.fields.CharField: password>,
          'user_permissions': <django.db.models.fields.related.ManyToManyField: user_permissions>,
          'username': <django.db.models.fields.CharField: username>},
 ':local': {'date_joined': <django.db.models.fields.DateTimeField: date_joined>,
            'email': <django.db.models.fields.EmailField: email>,
            'first_name': <django.db.models.fields.CharField: first_name>,
            'groups': <django.db.models.fields.related.ManyToManyField: groups>,
            'id': <django.db.models.fields.AutoField: id>,
            'is_active': <django.db.models.fields.BooleanField: is_active>,
            'is_staff': <django.db.models.fields.BooleanField: is_staff>,
            'is_superuser': <django.db.models.fields.BooleanField: is_superuser>,
            'last_login': <django.db.models.fields.DateTimeField: last_login>,
            'last_name': <django.db.models.fields.CharField: last_name>,
            'password': <django.db.models.fields.CharField: password>,
            'user_permissions': <django.db.models.fields.related.ManyToManyField: user_permissions>,
            'username': <django.db.models.fields.CharField: username>},
 ':pk': {'id': <django.db.models.fields.AutoField: id>},
 ':related': {'logentry_set': <RelatedObject: admin:logentry related to user>}
```

Note, in practice these selectors are not generally used.
