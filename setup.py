from setuptools import setup

setup(
    name='bongo_bgp',
    version='0.1',
    description='A framework for reacting to BGP routes',
    author='Kevin Benton',
    author_email='kevin@benton.pub',
    packages=['bongo_bgp'],
    install_requires=['netaddr'],
    entry_points={
        'console_scripts': ['bongo-route-processor = bongo_bgp.cli:main']
    }
)
