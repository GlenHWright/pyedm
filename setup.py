#!/usr/bin/env python
from setuptools import setup, Extension
import os

setup(name="pyedm", version="2.1.0",
	packages=['pyedm'],
	package_data={'pyedm' : ['modules/*.py']},
	author="Glen Wright",
	author_email="Glen.Wright@lightsource.ca",
	url="http://www.lightsource.ca")

setup(name="edm", version="2.1.0", py_modules=['edm',],)
