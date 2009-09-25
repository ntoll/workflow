import os
from distutils.core import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='django-workflow',
    version='0.1.0',
    description="A lightweight workflow engine application for Django based web-applications.",
    long_description=read('README.txt'),
    author='Nicholas H.Tollervey',
    author_email='ntoll@ntoll.org',
    license='BSD',
    url='http://github.com/ntoll/workflow',
    packages=[
        'workflow',
        'workflow.unit_tests'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    package_data = {
        'workflow': [
            'fixtures/*.json',
            'templates/graphviz/*.dot',
        ]
    },
    zip_safe=False, # required to convince setuptools/easy_install to unzip the package data
)
