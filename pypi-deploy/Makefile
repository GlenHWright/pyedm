PYTHON=python3

.PHONY : build

always help:
	@echo "usage:"
	@echo "	make test"
	@echo "      deploys to testpypi"
	@echo "  make deploy"
	@echo "      deploys to pypi"

build: 
	$(PYTHON) -m build
test:
	python3 -m twine upload --repository testpypi dist/*

deploy:
	python3 -m twine upload dist/*
