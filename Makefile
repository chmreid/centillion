include common.mk
MODULES=src/search src/doctypes tests

all: test


# Checks

lint:
	flake8 $(MODULES)

mypy:
	mypy --ignore-missing-imports --no-strict-optional $(MODULES)


# Tests

tests:=$(wildcard tests/test_*.py)

test: mypy lint
	@echo $(tests)
	pytest --cov=centillion -v tests

# A pattern rule that runs a single test script
$(tests): %.py : mypy lint
	pytest --cov=centillion -v $*.py

all_test:
	$(MAKE) CENTILLION_TEST_MODE="standalone" test
	$(MAKE) CENTILLION_TEST_MODE="integration" test

standalone_test:
	$(MAKE) CENTILLION_TEST_MODE="standalone" test

integration_test:
	$(MAKE) CENTILLION_TEST_MODE="integration" test


# Requirements

refresh_all_requirements:
	@echo -n '' >| requirements.txt
	@echo -n '' >| requirements-dev.txt
	@if [ $$(uname -s) == "Darwin" ]; then sleep 1; fi  # this is require because Darwin HFS+ only has second-resolution for timestamps.
	@touch requirements.txt.in requirements-dev.txt.in
	@$(MAKE) requirements.txt requirements-dev.txt

requirements.txt requirements-dev.txt : %.txt : %.txt.in
	[ ! -e .requirements-env ] || exit 1
	virtualenv -p $(shell which python3) .$<-env
	.$<-env/bin/pip install -r $@
	.$<-env/bin/pip install -r $<
	echo "# You should not edit this file directly.  Instead, you should edit $<." >| $@
	.$<-env/bin/pip freeze >> $@
	rm -rf .$<-env

requirements-dev.txt : requirements.txt.in

.PHONY: all lint mypy
.PHONY: refresh_all_requirements requirements.txt requirements-dev.txt test all_test integration_test standalone_test
