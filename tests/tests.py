import unittest
import datetime
from django.db.models.query import QuerySet
from django.contrib.auth.models import User
from preserialize import utils
from preserialize.serialize import serialize
from .models import Tag, Library, Hacker


class ModelSerializer(unittest.TestCase):
    def setUp(self):
        # Create 3 User instances
        u1 = User(id=1, username='ejohn', first_name='John', last_name='Resig',
                  is_active=True, is_superuser=True, is_staff=True,
                  last_login=datetime.datetime.strptime('2010-03-03 17:40:41', '%Y-%m-%d %H:%M:%S'),
                  password='!', email='',
                  date_joined=datetime.datetime.strptime('2009-05-16 15:52:40', '%Y-%m-%d %H:%M:%S'),
        )
        u1.save()

        u2 = User(id=2, username='jashkenas', first_name='Jeremy', last_name='Ashkenas',
                  is_active=True, is_superuser=False, is_staff=True,
                  last_login=datetime.datetime.strptime('2010-03-03 17:40:41', '%Y-%m-%d %H:%M:%S'),
                  password='!', email='',
                  date_joined=datetime.datetime.strptime('2009-05-16 15:52:40', '%Y-%m-%d %H:%M:%S'),
        )
        u2.save()

        u3 = User(id=3, username='holovaty', first_name='Adrian', last_name='Holovaty',
                  is_active=False, is_superuser=True, is_staff=True,
                  last_login=datetime.datetime.strptime('2010-03-03 17:40:41', '%Y-%m-%d %H:%M:%S'),
                  password='!', email='',
                  date_joined=datetime.datetime.strptime('2009-05-16 15:52:40', '%Y-%m-%d %H:%M:%S'),
        )
        u3.save()

        # Create 4 Tag instances
        tag1 = Tag(id=1, name='javascript')
        tag1.save()

        tag2 = Tag(id=2, name='dom')
        tag2.save()

        tag3 = Tag(id=3, name='python')
        tag3.save()

        tag4 = Tag(id=4, name='django')
        tag4.save()

        # Create 4 Library instances
        lib1 = Library(id=1, name='jQuery',
                       url='https://github.com/jquery/jquery',
                       language='javascript'
        )
        lib1.save()
        lib1.tags.add(tag1)
        lib1.tags.add(tag2)

        lib2 = Library(id=2, name='Backbone',
                       url='https://github.com/documentcloud/backbone',
                       language='javascript',
        )
        lib2.save()
        lib2.tags.add(tag1)

        lib3 = Library(id=3, name='CoffeeScript',
                       url='https://github.com/jashkenas/coffee-script',
                       language='coffeescript',
        )
        lib3.save()
        lib3.tags.add(tag1)

        lib4 = Library(id=4, name='Django',
                       url='https://github.com/django/django',
                       language='python',
        )
        lib4.save()
        lib4.tags.add(tag3, tag4)

        # Create 3 Hacker instances
        hacker1 = Hacker(user=User.objects.get(id=1), website='http://ejohn.org')
        hacker1.save()
        hacker1.libraries.add(lib1)

        hacker2 = Hacker(user=User.objects.get(id=2), website='https://github.com/jashkenas',)
        hacker2.save()
        hacker2.libraries.add(lib2, lib3)

        hacker3 = Hacker(user=User.objects.get(id=3), website='http://holovaty.com')
        hacker3.save()
        hacker3.libraries.add(lib4)

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
