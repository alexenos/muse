"""
Visualizing simulation data should be beautiful, efficient, quick, and easy
"""
from setuptools import find_packages, setup

# TODO: make argcomplete an extra rather than a dependency
dependencies = [
    'argcomplete',
    'future',
    'h5py',
    'matplotlib',
    'pandas',
    'pyyaml',
    'seaborn',
    ]


setup(
    name='muse',
    version='0.2.1',
    url='',
    license='BSD',
    author='Dax Garner',
    author_email='dax.garner@fireflyspace.com',
    description='Visualizing simulation data should be beautiful, efficient, quick, and easy',
    long_description=__doc__,
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=dependencies,
    entry_points={
        'console_scripts': [
            'muse = muse.cli:main',
        ],
    },
)
