from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='covreports',
    version='0.1.0',
    description='Reporting for Codecov',
    long_description=long_description,
    url='https://github.com/codecov/report',
    author='Codecov',
    author_email='support@codecov.io',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=[
        "attrs==17.4.0",
        "colour==0.1.5",
        "coverage==4.5",
        "funcsigs==1.0.2",
        "mock==2.0.0",
        "pbr==3.1.1",
        "pluggy==0.6.0",
        "py==1.5.2",
        "pytest==3.4.0",
        "pytest-cov==2.5.1",
        "pytest-mock==1.7.1",
        "six==1.11.0",
        "pycrypto==2.6.1",
    ]
)
