import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'

import django  # noqa

if django.__version__ >= (1, 7):
    django.setup()


from django.core import management  # noqa

management.call_command('test', 'tests')
