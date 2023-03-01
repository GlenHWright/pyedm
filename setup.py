#!/usr/bin/env python
from setuptools import setup
import os

long_description="epics-pyedm - Interpreter for EPICS Extensible Display Manager files\n\
        - reads .edl files\n\
        - allows basic editing of .edl files\n\
        - allows saving .edl and .jedl (json-based) files\n\
        - can be loaded as a module for embedded operation\n\
"
setup(name="epics-pyedm", version="2.1.0",
        description="EPICS EDM PyQt5 display tool",
        long_description=long_description,
        long_description_content_type="text/r-rst",
	packages=['pyedm'],
	package_data={'pyedm' : ['modules/*.py']},
	author="Glen Wright",
	author_email="Glen.Wright@lightsource.ca",
	url="https://www.lightsource.ca",
        python_requires='>=3.6',
        install_requires=[
            "pyepics>=3",
            "PyQt5",
            "numpy",
            "pyqtgraph"
            ]
        )

# OPTIONAL - allow python3 -m edm edmargs
#setup(name="edm", version="2.1.0", py_modules=['edm',],)
