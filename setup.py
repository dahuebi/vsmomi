import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


with open('requirements.txt') as f:
    required = f.read().splitlines()

with open('test-requirements.txt') as f:
    required_for_tests = f.read().splitlines()

setup(
    name='vsmomi',
    version='0.0.1',
    author='Andreas Huber',
    author_email='andreas.huber@gmail.com',
    packages=['vsmomi'],
    package_dir={'vsmomi': 'vsmomi'},
    scripts=['bin/vs'],
    url='https://github.com/dahuebi/vsmomi',
    description='VMware vSphere CLI',
    long_description=read('README.md'),
    license='License :: OSI Approved :: Apache Software License',
    install_requires=required,
    platforms = ['Windows', 'Linux'],
    test_suite = 'tests',
    tests_require = required_for_tests,
)
