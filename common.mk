SHELL=/bin/bash

ifeq ($(shell which pandoc),)
$(error Please install pandoc using "apt-get install pandoc" or "brew install pandoc")
endif

ifeq ($(findstring Python 3.6, $(shell python --version 2>&1)),)
$(error Please run make commands from a Python 3.6 virtualenv)
endif
