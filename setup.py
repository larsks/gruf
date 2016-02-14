from setuptools import setup, find_packages

setup(name='gruf',
      author='Lars Kellogg-Stedman',
      author_email='lars@oddbit.com',
      url='https://github.com/larsks/gruf',
      version='0.1',
      packages=find_packages(),
      package_data={'gruf': ['templates/*.h2']},
      entry_points={'console_scripts': ['gerrit = gruf.main:main',],})
