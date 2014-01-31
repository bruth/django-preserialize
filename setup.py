from setuptools import setup

kwargs = {
    'packages': ['preserialize'],
    'include_package_data': True,
    'install_requires': [
        'django',
    ],
    'test_suite': 'test_suite',
    'name': 'django-preserialize',
    'version': __import__('preserialize').get_version(),
    'author': 'Byron Ruth',
    'author_email': 'b@devel.io',
    'description': 'Pre-serialize model instances and querysets',
    'license': 'BSD',
    'keywords': 'serialize model queryset django',
    'url': 'https://github.com/bruth/django-preserialize/',
    'classifiers': [
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
    ],
}

setup(**kwargs)
