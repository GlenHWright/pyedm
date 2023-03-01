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
	twine upload --repository testpypi dist/*

deploy:
	twine upload dist/*
