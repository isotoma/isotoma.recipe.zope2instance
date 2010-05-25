from setuptools import setup, find_packages

version = '0.0.2'

setup(
    name = 'isotoma.recipe.zope2instance',
    version = version,
    description = "Buildout recipes for create zope2instances",
    url = "http://pypi.python.org/pypi/isotoma.recipe.zope2instance",
    long_description = open("README.rst").read() + "\n" + \
                       open("CHANGES.txt").read(),
    classifiers = [
        "Framework :: Buildout",
        "Intended Audience :: System Administrators",
        "Operating System :: POSIX",
        "License :: OSI Approved :: Zope Public License",
    ],
    keywords = "buildout cron",
    author = "John Carr",
    author_email = "john.carr@isotoma.com",
    license="Apache Software License",
    packages = find_packages(exclude=['ez_setup']),
    package_data = {
        '': ['README.rst', 'CHANGES.txt'],
    },
    namespace_packages = ['isotoma', 'isotoma.recipe'],
    include_package_data = True,
    zip_safe = False,
    install_requires = [
        'setuptools',
        'zc.buildout',
        'zc.recipe.egg'
    ],
    entry_points = {
        "zc.buildout": [
            "default = isotoma.recipe.zope2instance:Recipe",
        ],
    }
)
