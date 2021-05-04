from setuptools import setup, find_packages
import os.path

current_dir = os.path.abspath(os.path.dirname(__file__))

setup(
    name='responder_commons',
    version='1.0.1',
    description='SOC responder utilities',
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Utilities',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],

    keywords='SOC services utils',
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    install_requires=[
        'requests == 2.22.0',
        'sqlalchemy == 1.3.13',
        'psycopg2-binary == 2.8.4',
        'python-benedict == 0.16.0'
    ],
)
