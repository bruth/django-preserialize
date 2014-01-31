import unittest
import datetime
from django.db import models
from django.db.models.query import QuerySet
from django.contrib.auth.models import User
from preserialize import utils
from preserialize.serialize import serialize


# Some models..
class Tag(models.Model):
    name = models.CharField(max_length=20)


class Library(models.Model):
    name = models.CharField(max_length=30)
    url = models.URLField()
    language = models.CharField(max_length=20)
    tags = models.ManyToManyField(Tag, related_name='libraries')


class Hacker(models.Model):
    user = models.OneToOneField(User, related_name='profile', primary_key=True)
    website = models.URLField()
    libraries = models.ManyToManyField(Library, related_name='hackers')

    def signature(self):
        return '{0}  <{1}>  {2}'.format(self.user.get_full_name(),
                self.user.email, self.website)


class ModelSerializer(unittest.TestCase):
    def setUp(self):
        self.hackers = Hacker.objects.all()
        self.tags = Tag.objects.all()

    def test_resolver(self):
        self.assertEqual(utils.parse_selectors(Hacker, ['website']), ('website',))

    def test_default(self):
        obj = serialize(self.hackers)
        self.assertEqual(obj, [{
            'website': 'http://ejohn.org',
            'user': {
                'username': 'ejohn',
                'first_name': 'John',
                'last_name': 'Resig',
                'is_active': True,
                'email': '',
                'is_superuser': True,
                'is_staff': True,
                'last_login': datetime.datetime(2010, 3, 3, 17, 40, 41),
                'password': '!',
                'id': 1,
                'date_joined': datetime.datetime(2009, 5, 16, 15, 52, 40),
                'user_permissions': [],
                'groups': [],
            },
            'libraries': [{
                'url': 'https://github.com/jquery/jquery',
                'name': 'jQuery',
                'id': 1,
                'language': 'javascript',
                'tags': [{
                    'id': 1,
                    'name': 'javascript'
                }, {
                    'id': 2,
                    'name': 'dom'
                }]
            }]
        }, {
            'website': 'https://github.com/jashkenas',
            'user': {
                'username': 'jashkenas',
                'first_name': 'Jeremy',
                'last_name': 'Ashkenas',
                'is_active': True,
                'email': '',
                'is_superuser': False,
                'is_staff': True,
                'last_login': datetime.datetime(2010, 3, 3, 17, 40, 41),
                'password': '!',
                'id': 2,
                'date_joined': datetime.datetime(2009, 5, 16, 15, 52, 40),
                'user_permissions': [],
                'groups': [],
            },
            'libraries': [{
                'url': 'https://github.com/documentcloud/backbone',
                'name': 'Backbone',
                'id': 2,
                'language': 'javascript',
                'tags': [{
                    'id': 1,
                    'name': 'javascript'
                }]
            }, {
                'url': 'https://github.com/jashkenas/coffee-script',
                'name': 'CoffeeScript',
                'id': 3,
                'language': 'coffeescript',
                'tags': [{
                    'id': 1,
                    'name': 'javascript'
                }]
            }]
        }, {
            'website': 'http://holovaty.com',
            'user': {
                'username': 'holovaty',
                'first_name': 'Adrian',
                'last_name': 'Holovaty',
                'is_active': False,
                'email': '',
                'is_superuser': True,
                'is_staff': True,
                'last_login': datetime.datetime(2010, 3, 3, 17, 40, 41),
                'password': '!',
                'id': 3,
                'date_joined': datetime.datetime(2009, 5, 16, 15, 52, 40),
                'user_permissions': [],
                'groups': [],
            },
            'libraries': [{
                'url': 'https://github.com/django/django',
                'name': 'Django',
                'id': 4,
                'language': 'python',
                'tags': [{
                    'id': 3,
                    'name': 'python'
                }, {
                    'id': 4,
                    'name': 'django'
                }]
            }]
        }])

    def test_fields(self):
        obj = serialize(self.hackers, fields=['website'], values_list=True)
        self.assertEqual(obj, [
            'http://ejohn.org',
            'https://github.com/jashkenas',
            'http://holovaty.com',
        ])

    def test_related(self):
        template = {
            'fields': [':pk', 'website', 'user', 'libraries'],
            'related': {
                'user': {
                    'exclude': ['groups', 'password', 'user_permissions'],
                    'merge': True,
                    'prefix': '%(accessor)s_',
                },
                'libraries': {
                    'fields': ['name'],
                    'values_list': True,
                }
            },
        }
        obj = serialize(self.hackers, **template)
        self.assertEqual(obj, [{
            'user_is_superuser': True,
            'website': 'http://ejohn.org',
            'user_id': 1,
            'user_is_active': True,
            'user_is_staff': True,
            'user_first_name': 'John',
            'user_last_name': 'Resig',
            'user_username': 'ejohn',
            'libraries': ['jQuery'],
            'user_date_joined': datetime.datetime(2009, 5, 16, 15, 52, 40),
            'user_last_login': datetime.datetime(2010, 3, 3, 17, 40, 41),
            'user_email': ''
        }, {
            'user_is_superuser': False,
            'website': 'https://github.com/jashkenas',
            'user_id': 2,
            'user_is_active': True,
            'user_is_staff': True,
            'user_first_name': 'Jeremy',
            'user_last_name': 'Ashkenas',
            'user_username': 'jashkenas',
            'libraries': ['Backbone', 'CoffeeScript'],
            'user_date_joined': datetime.datetime(2009, 5, 16, 15, 52, 40),
            'user_last_login': datetime.datetime(2010, 3, 3, 17, 40, 41),
            'user_email': ''
        }, {
            'user_is_superuser': True,
            'website': 'http://holovaty.com',
            'user_id': 3,
            'user_is_active': False,
            'user_is_staff': True,
            'user_first_name': 'Adrian',
            'user_last_name': 'Holovaty',
            'user_username': 'holovaty',
            'libraries': ['Django'],
            'user_date_joined': datetime.datetime(2009, 5, 16, 15, 52, 40),
            'user_last_login': datetime.datetime(2010, 3, 3, 17, 40, 41),
            'user_email': ''
        }])

    def test_shorthand(self):
        data_template = {
            'fields': [':pk', 'name', 'libraries'],
            'related': {
                'libraries': {
                    'exclude': 'tags'
                }
            }
        }
        obj = serialize(self.tags, **data_template)
        self.assertEqual(obj, [{
            'name': 'javascript',
            'libraries': [{
                'url': 'https://github.com/jquery/jquery',
                'name': 'jQuery',
                'id': 1,
                'language': 'javascript',
            }, {
                'url': 'https://github.com/documentcloud/backbone',
                'name': 'Backbone',
                'id': 2,
                'language': 'javascript',
            }, {
                'url': 'https://github.com/jashkenas/coffee-script',
                'name': 'CoffeeScript',
                'id': 3,
                'language': 'coffeescript',
            }],
            'id': 1
        }, {
            'name': 'dom',
            'libraries': [{
                'url': 'https://github.com/jquery/jquery',
                'name': 'jQuery',
                'id': 1,
                'language': 'javascript',
            }],
            'id': 2
        }, {
            'name': 'python',
            'libraries': [{
                'url': 'https://github.com/django/django',
                'name': 'Django',
                'id': 4,
                'language': 'python',
            }],
            'id': 3,
        }, {
            'name': 'django',
            'libraries': [{
                'url': 'https://github.com/django/django',
                'name': 'Django',
                'id': 4,
                'language': 'python',
            }],
            'id': 4
        }])

    def test_mixed_obj(self):
        obj = serialize({'leet_hacker': self.hackers[0]}, camelcase=True,
                related={'leet_hacker': {'fields': ['signature'], 'flat': False}})
        self.assertEqual(obj, {'leetHacker': {'signature': 'John Resig  <>  http://ejohn.org'}})

    def test_allow_missing(self):
        obj = serialize({}, fields=['foo', 'bar', 'baz'], allow_missing=True)
        self.assertEqual(obj, {'foo': None, 'bar': None, 'baz': None})

    def test_prehook_shorthand(self):
        obj = serialize(self.hackers, prehook={'user__first_name': 'John'},
            fields=['user'], related={'user': {'fields': ['first_name']}})

        self.assertEqual(obj, [{
            'user': 'John',
        }])

    def test_prehook(self):
        def prehook(queryset):
            # Ensure this only applies to a QuerySet, acts as a no-op for
            # model instances
            if isinstance(queryset, QuerySet):
                queryset = queryset.filter(user__first_name='John')
            return queryset

        obj = serialize(self.hackers, prehook=prehook, fields=['user'],
            related={'user': {'fields': ['first_name']}})

        self.assertEqual(obj, [{
            'user': 'John',
        }])

    def test_posthook(self):
        def posthook(instance, attrs):
            attrs['foo'] = 1
            return attrs

        obj = serialize(self.hackers[0], posthook=posthook,
            fields=['user'], related={'user': {'fields': ['first_name']}})

        self.assertEqual(obj, {
            'foo': 1,
            'user': 'John',
        })
