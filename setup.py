#!/usr/bin/env python
# coding: utf8

import os

from setuptools import setup, find_packages

# if there's a converted readme, use it, otherwise fall back to markdown
if os.path.exists('README.rst'):
    readme_path = 'README.rst'
else:
    readme_path = 'README.md'

# avoid importing the module
exec(open('eventtools/_version.py').read())

setup(
    name='django-eventtools',
    version=__version__,
    description='Recurring event tools for django',
    long_description=open(readme_path).read(),
    author='Greg Brown',
    author_email='greg@gregbrown.co.nz',
    url='https://github.com/gregplaysguitar/django-eventtools',
    packages=find_packages(exclude=('tests', )),
    license='BSD License',
    zip_safe=False,
    platforms='any',
    install_requires=['Django>=3.2', 'python-dateutil>=2.8.2'],
    python_requires='>=3.9',
    include_package_data=True,
    package_data={'eventtools': ['py.typed']},
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Framework :: Django',
        'Framework :: Django :: 3.2',
        'Framework :: Django :: 4.2',
        'Framework :: Django :: 5.0',
    ],
)
