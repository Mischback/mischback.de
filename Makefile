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

# Content source file directory
BUILD_DIR := $(REPO_ROOT)/.build
CONTENT_DIR := $(REPO_ROOT)/content
THEME_DIR := $(REPO_ROOT)/theme/mischback

# The source files for the actual content
SRC_CONTENT := $(shell find $(CONTENT_DIR) -type f)
SRC_THEME := $(shell find $(THEME_DIR) -type f)

# Stamps
#
# Track certain things with artificial *stamps*.
STAMP_DIR := $(REPO_ROOT)/.make-stamps
STAMP_SPHINX := $(STAMP_DIR)/sphinx-build

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
dev/srv : $(STAMP_SPHINX)
	$(TOX_CMD) -q -e dev-serve
.PHONY : dev/srv

# Run ``Sphinx`` to build HTML output from reST sources
#
# This is the primary build recipe, as it will generate the HTML output by
# running ``Sphinx``. It is (obviously) dependent on a plethora of things,
# including the actual content source files and the theme files.
$(STAMP_SPHINX) : $(SRC_CONTENT) $(SRC_THEME)
	$(create_dir)
	$(MAKE) util/sphinx/build sphinx-build_options="-W --keep-going"
	touch $@

# Remove build artifacts
clean :
	rm -rf $(BUILD_DIR)
	rm -rf $(STAMP_SPHINX)
.PHONY : clean


# ##### Utility Stuff
#
# The following recipes are mainly used as shortcuts to run several tools.
# They are not directly related to the actual build process.

# Run ``black``
util/lint/black :
	$(MAKE) util/pre-commit pre-commit_id="black" pre-commit_files="--all-files"
.PHONY : util/lint/black

# Verify that all articles have the "keywords" meta value
util/lint/content/keywords :
	$(MAKE) util/pre-commit pre-commit_id="content_keywords" pre-commit_files="--all-files"
.PHONY : util/lint/content/keywords

# Verify that all articles have the "summary" meta value
util/lint/content/summary :
	$(MAKE) util/pre-commit pre-commit_id="content_summary" pre-commit_files="--all-files"
.PHONY : util/lint/content/summary

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

# Run ``prettier``
util/lint/prettier :
	$(MAKE) util/pre-commit pre-commit_id="prettier" pre-commit_files="--all-files"
.PHONY : util/lint/prettier

# Run ``Sphinx``'s linkcheck builder
util/lint/sphinx-linkcheck :
	$(MAKE) util/sphinx/build sphinx_builder="linkcheck"
.PHONY : util/lint/sphinx-linkcheck

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

# Run ``sphinx-build``
#
# This is the recipe that runs ``Sphinx``'s builders. It does provide mandatory
# settings / configuration values but does accept additional flags aswell.
# The actual *builder* to run is configured by ``sphinx_builder``.
#
# As of now, ``dirhtml`` builder is the default, as this builder is used to
# generate the HTML output. The ``linkcheck`` builder is used as an additional
# linter.
sphinx_builder ?= "dirhtml"
sphinx_config-dir ?= "./"
sphinx-build_options ?= ""
util/sphinx/build : conf.py requirements/sphinx.txt pyproject.toml $(TOX_VENV_INSTALLED)
	$(TOX_CMD) -q -e sphinx -- sphinx-build $(sphinx-build_options) -b $(sphinx_builder) -c $(sphinx_config-dir) $(CONTENT_DIR) $(BUILD_DIR)
.PHONY : util/sphinx/build

# (Re-) Generate the requirements files using pip-tools (``pip-compile``)
#
# ``pip-compile`` is run through a ``tox`` environment. The actual command is
# included in ``tox``'s configuration in ``pyproject.toml``. That's why that
# file is an additional prerequisite. This may lead to additional
# regenerations, but these will most likely not affect the generated files.
requirements/%.txt : requirements/%.in pyproject.toml $(TOX_VENV_INSTALLED)
	$(TOX_CMD) -q -e pip-tools -- $<


# ##### Internal utility stuff

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

# Create a directory as required by other recipes
create_dir = @mkdir -p $(@D)
