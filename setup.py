#!/usr/bin/env python
from distutils.core import setup, Extension
import os

setup(name="pyedm", version="1.1.4",
	packages=['pyedm'],
	package_data={'pyedm' : ['modules/*.py']},
	author="Glen Wright",
	author_email="Glen.Wright@lightsource.ca",
	url="http://www.lightsource.ca")

setup(name="edm", version="1.1.4", py_modules=['edm',],)
