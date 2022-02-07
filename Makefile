PYTHON=python

.PHONY : build install all

build:
	$(PYTHON) setup.py build

install:
	$(PYTHON) setup.py install

clean :
	/bin/rm -rf build

all: build install
