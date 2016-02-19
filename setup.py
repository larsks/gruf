from setuptools import setup, find_packages
from gruf import __version__

with open('requirements.txt') as fd:
    requires = fd.read().splitlines()

setup(name='gruf',
      author='Lars Kellogg-Stedman',
      author_email='lars@oddbit.com',
      url='https://github.com/larsks/gruf',
      version=__version__,
      packages=find_packages(),
      install_requires=requires,
      package_data={'gruf': [
          'templates/*.j2',
          'templates/*/*.j2']},
      entry_points={'console_scripts': ['gruf = gruf.main:main',],})
