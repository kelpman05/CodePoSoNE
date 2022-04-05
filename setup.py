#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['Click>=7.0', ]

setup_requirements = [ ]

test_requirements = [ ]

setup(
    author="sjtu",
    author_email='jie.zhu@huangloong.com',
    python_requires='>=3.5',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="A distributed consensus algorithm",
    entry_points={
        'console_scripts': [
            'distributed_consensus=distributed_consensus.cli:main',
        ],
    },
    install_requires=requirements,
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='distributed_consensus',
    name='distributed_consensus',
    packages=find_packages(include=['distributed_consensus', 'distributed_consensus.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/genzj/distributed_consensus',
    version='0.1.0',
    zip_safe=False,
)
