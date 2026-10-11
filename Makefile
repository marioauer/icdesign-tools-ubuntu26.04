PYTHON ?= python3
OUT ?= $(CURDIR)/dist
JOBS ?= 2

.PHONY: build all list clean test
build:
	$(PYTHON) scripts/build.py --out "$(OUT)" --jobs "$(JOBS)"
all:
	$(PYTHON) scripts/build.py --all --out "$(OUT)" --jobs "$(JOBS)"
list:
	$(PYTHON) scripts/build.py --list
test:
	$(PYTHON) -m unittest discover -s tests
clean:
	rm -rf "$(OUT)" site
