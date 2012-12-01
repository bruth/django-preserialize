import unittest
import datetime
from django.db import models
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
            'website': u'http://ejohn.org',
            'user': {
                'username': u'ejohn',
                'first_name': u'John',
                'last_name': u'Resig',
                'is_active': True,
                'email': u'',
                'is_superuser': True,
                'is_staff': True,
                'last_login': datetime.datetime(2010, 3, 3, 17, 40, 41),
                'password': u'!',
                'id': 1,
                'date_joined': datetime.datetime(2009, 5, 16, 15, 52, 40),
                'user_permissions': [],
                'groups': [],
            },
            'libraries': [{
                'url': u'https://github.com/jquery/jquery',
                'name': u'jQuery',
                'id': 1,
                'language': u'javascript',
                'tags': [{
                    'id': 1,
                    'name': u'javascript'
                }, {
                    'id': 2,
                    'name': u'dom'
                }]
            }]
        }, {
            'website': u'https://github.com/jashkenas',
            'user': {
                'username': u'jashkenas',
                'first_name': u'Jeremy',
                'last_name': u'Ashkenas',
                'is_active': True,
                'email': u'',
                'is_superuser': False,
                'is_staff': True,
                'last_login': datetime.datetime(2010, 3, 3, 17, 40, 41),
                'password': u'!',
                'id': 2,
                'date_joined': datetime.datetime(2009, 5, 16, 15, 52, 40),
                'user_permissions': [],
                'groups': [],
            },
            'libraries': [{
                'url': u'https://github.com/documentcloud/backbone',
                'name': u'Backbone',
                'id': 2,
                'language': u'javascript',
                'tags': [{
                    'id': 1,
                    'name': u'javascript'
                }]
            }, {
                'url': u'https://github.com/jashkenas/coffee-script',
                'name': u'CoffeeScript',
                'id': 3,
                'language': u'coffeescript',
                'tags': [{
                    'id': 1,
                    'name': u'javascript'
                }]
            }]
        }, {
            'website': u'http://holovaty.com',
            'user': {
                'username': u'holovaty',
                'first_name': u'Adrian',
                'last_name': u'Holovaty',
                'is_active': False,
                'email': u'',
                'is_superuser': True,
                'is_staff': True,
                'last_login': datetime.datetime(2010, 3, 3, 17, 40, 41),
                'password': u'!',
                'id': 3,
                'date_joined': datetime.datetime(2009, 5, 16, 15, 52, 40),
                'user_permissions': [],
                'groups': [],
            },
            'libraries': [{
                'url': u'https://github.com/django/django',
                'name': u'Django',
                'id': 4,
                'language': u'python',
                'tags': [{
                    'id': 3,
                    'name': u'python'
                }, {
                    'id': 4,
                    'name': u'django'
                }]
            }]
        }])

    def test_fields(self):
        obj = serialize(self.hackers, fields=['website'], values_list=True)
        self.assertEqual(obj, [
            u'http://ejohn.org',
            u'https://github.com/jashkenas',
            u'http://holovaty.com',
        ])

    def test_related(self):
        template = {
            'fields': [':pk', 'website', 'user', 'libraries'],
            'related': {
                'user': {
                    'exclude': ['groups', 'password', 'user_permissions'],
                    'merge': True,
                    'key_prefix': '%(accessor)s_',
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
            'website': u'http://ejohn.org',
            'user_id': 1,
            'user_is_active': True,
            'user_is_staff': True,
            'user_first_name': u'John',
            'user_last_name': u'Resig',
            'user_username': u'ejohn',
            'libraries': [u'jQuery'],
            'user_date_joined': datetime.datetime(2009, 5, 16, 15, 52, 40),
            'user_last_login': datetime.datetime(2010, 3, 3, 17, 40, 41),
            'user_email': u''
        }, {
            'user_is_superuser': False,
            'website': u'https://github.com/jashkenas',
            'user_id': 2,
            'user_is_active': True,
            'user_is_staff': True,
            'user_first_name': u'Jeremy',
            'user_last_name': u'Ashkenas',
            'user_username': u'jashkenas',
            'libraries': [u'Backbone', u'CoffeeScript'],
            'user_date_joined': datetime.datetime(2009, 5, 16, 15, 52, 40),
            'user_last_login': datetime.datetime(2010, 3, 3, 17, 40, 41),
            'user_email': u''
        }, {
            'user_is_superuser': True,
            'website': u'http://holovaty.com',
            'user_id': 3,
            'user_is_active': False,
            'user_is_staff': True,
            'user_first_name': u'Adrian',
            'user_last_name': u'Holovaty',
            'user_username': u'holovaty',
            'libraries': [u'Django'],
            'user_date_joined': datetime.datetime(2009, 5, 16, 15, 52, 40),
            'user_last_login': datetime.datetime(2010, 3, 3, 17, 40, 41),
            'user_email': u''
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
            'name': u'javascript',
            'libraries': [{
                'url': u'https://github.com/jquery/jquery',
                'name': u'jQuery',
                'id': 1,
                'language': u'javascript',
            }, {
                'url': u'https://github.com/documentcloud/backbone',
                'name': u'Backbone',
                'id': 2,
                'language': u'javascript',
            }, {
                'url': u'https://github.com/jashkenas/coffee-script',
                'name': u'CoffeeScript',
                'id': 3,
                'language': u'coffeescript',
            }],
            'id': 1
        }, {
            'name': u'dom',
            'libraries': [{
                'url': u'https://github.com/jquery/jquery',
                'name': u'jQuery',
                'id': 1,
                'language': u'javascript',
            }],
            'id': 2
        }, {
            'name': u'python',
            'libraries': [{
                'url': u'https://github.com/django/django',
                'name': u'Django',
                'id': 4,
                'language': u'python',
            }],
            'id': 3,
        }, {
            'name': u'django',
            'libraries': [{
                'url': u'https://github.com/django/django',
                'name': u'Django',
                'id': 4,
                'language': u'python',
            }],
            'id': 4
        }])

    def test_mixed_obj(self):
        obj = serialize({'leet_hacker': self.hackers[0]}, camelcase=True,
                related={'leet_hacker': {'fields': ['signature']}})
        self.assertEqual(obj, {'leetHacker': {'signature': 'John Resig  <>  http://ejohn.org'}})

    def test_allow_missing(self):
        obj = serialize({}, fields=['foo', 'bar', 'baz'], allow_missing=True)
        self.assertEqual(obj, {'foo': None, 'bar': None, 'baz': None})
