# SPDX-FileCopyrightText: 2022 Mischback
# SPDX-License-Identifier: MIT
# SPDX-FileType: SOURCE


# ### INTERNAL SETTINGS

# The absolute path to the repository.
#
# This assumes that this ``Makefile`` is placed in the root of the repository.
# REPO_ROOT does not contain a trailing ``/``
#
# Ref: https://stackoverflow.com/a/324782
# Ref: https://stackoverflow.com/a/2547973
# Ref: https://stackoverflow.com/a/73450593
REPO_ROOT := $(patsubst %/, %, $(dir $(abspath $(lastword $(MAKEFILE_LIST)))))

# Internal Python environments
TOX_VENV_DIR := $(REPO_ROOT)/.tox-venv
TOX_VENV_CREATED := $(TOX_VENV_DIR)/pyvenv.cfg
TOX_VENV_INSTALLED := $(TOX_VENV_DIR)/packages.txt
TOX_CMD := $(TOX_VENV_DIR)/bin/tox

# ``pre-commit`` is used to run several code-quality tools automatically.
#
# ``pre-commit`` is run through ``tox`` aswell, see ``tox``'s ``util``
# environment.
PRE_COMMIT_READY := .git/hooks/pre-commit

# ``make``-specific settings
.SILENT :
.DELETE_ON_ERROR :
MAKEFLAGS += --no-print-directory
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules


# ### RECIPES

# Build and serve the actual generated website
dev/srv : build/sphinx
	$(TOX_CMD) -q -e build-serve
.PHONY : dev/srv

# Run ``sphinx`` to create the actual release files
build/sphinx : requirements/build-sphinx.txt
	$(TOX_CMD) -e build-sphinx
.PHONY : build/sphinx

# Run ``black``
util/lint/black :
	$(MAKE) util/pre-commit pre-commit_id="black" pre-commit_files="--all-files"
.PHONY : util/lint/black

# Run ``curlylint``
util/lint/curlylint :
	$(MAKE) util/pre-commit pre-commit_id="curlylint" pre-commit_files="--all-files"
.PHONY : util/lint/curlylint

# Run ``djlint``
util/lint/djlint :
	$(MAKE) util/pre-commit pre-commit_id="djlint-jinja" pre-commit_files="--all-files"
.PHONY : util/lint/djlint

# Run ``doc8``
util/lint/doc8 :
	$(MAKE) util/pre-commit pre-commit_id="doc8" pre-commit_files="--all-files"
.PHONY : util/lint/doc8

# Run ``flake8``
util/lint/flake8 :
	$(MAKE) util/pre-commit pre-commit_id="flake8" pre-commit_files="--all-files"
.PHONY : util/lint/flake8

# Run ``isort``
util/lint/isort :
	$(MAKE) util/pre-commit pre-commit_id="isort" pre-commit_files="--all-files"
.PHONY : util/lint/isort

# Run ``sphinx-lint``
util/lint/sphinx-lint :
	$(MAKE) util/pre-commit pre-commit_id="sphinx-lint" pre-commit_files="--all-files"
.PHONY : util/lint/sphinx-lint

# Run ``pre-commit``
#
# This is the actual recipe that runs ``pre-commit``. It is used by other
# recipes, that will set the required ``pre-commit_id`` and
# ``pre-commit_files`` variables.
pre-commit_id ?= ""
pre-commit_files ?= ""
util/pre-commit : $(PRE_COMMIT_READY)
	$(TOX_CMD) -q -e pre-commit -- pre-commit run $(pre-commit_files) $(pre-commit_id)
.PHONY : util/pre-commit

# (Re-) Generate the requirements files using pip-tools (``pip-compile``)
#
# ``pip-compile`` is run through a ``tox`` environment. The actual command is
# included in ``tox``'s configuration in ``pyproject.toml``. That's why that
# file is an additional prerequisite. This may lead to additional
# regenerations, but these will most likely not affect the generated files.
requirements/%.txt : requirements/%.in pyproject.toml $(TOX_VENV_INSTALLED)
	$(TOX_CMD) -q -e pip-tools -- $<

# Internal utility stuff

# Create the virtual environment for running tox
$(TOX_VENV_CREATED) :
	/usr/bin/env python3 -m venv $(TOX_VENV_DIR)

# Install the required packages in tox's virtual environment
$(TOX_VENV_INSTALLED) : $(TOX_VENV_CREATED)
	$(TOX_VENV_DIR)/bin/pip install -r requirements/tox.txt
	$(TOX_VENV_DIR)/bin/pip freeze > $@

# Install the pre-commit hooks
$(PRE_COMMIT_READY) : | $(TOX_VENV_INSTALLED)
	$(TOX_CMD) -e pre-commit -- pre-commit install
