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
FONT_SRC_DIR := $(THEME_DIR)/_src/fonts
STYLE_DIR := $(REPO_ROOT)/theme/mischback/_src/style

# The source files for the actual content
SRC_CONTENT := $(shell find $(CONTENT_DIR) -type f)
# Ref: https://stackoverflow.com/a/69830768
SRC_THEME := $(shell find $(THEME_DIR) -type f -not \( -name "_src" -prune \))
SRC_STYLE := $(shell find $(STYLE_DIR) -type f)

# Stamps
#
# Track certain things with artificial *stamps*.
STAMP_DIR := $(REPO_ROOT)/.make-stamps
STAMP_SPHINX := $(STAMP_DIR)/sphinx-build
STAMP_PRE_FONTS := $(STAMP_DIR)/fonts-ready
STAMP_PRE_SASS := $(STAMP_DIR)/pre-sass
STAMP_POST := $(STAMP_DIR)/post-processing
STAMP_POST_PRETTIFY := $(STAMP_DIR)/post-prettify
STAMP_NODE_READY := $(STAMP_DIR)/node-ready

# Internal Python environments
#
# Actually this does only handle the setup of ``tox``, while the actual build
# scripts are executed through ``tox``'s environments.
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
dev/srv : $(STAMP_POST_PRETTIFY)
	$(TOX_CMD) -q -e sphinx -- python -m http.server 8082 --directory $(BUILD_DIR)
.PHONY : dev/srv

# Create the actual build
build : $(STAMP_POST)
.PHONY : build

# Run ``Sphinx`` to build HTML output from reST sources
#
# This is the primary build recipe, as it will generate the HTML output by
# running ``Sphinx``. It is (obviously) dependent on a plethora of things,
# including the actual content source files and the theme files.
$(STAMP_SPHINX) : $(SRC_CONTENT) $(SRC_THEME) $(STAMP_PRE_SASS)
	$(create_dir)
	echo $(RUNNING_CI)
	$(MAKE) util/sphinx/build sphinx-build_options="-W --keep-going"
	touch $@

# Prepare the fonts
#
# In order to optimize the fonts, the provided glyphs may be reduced
# significantly.
#
# FIXME: #34
$(STAMP_PRE_FONTS) : $(FONT_SRC_DIR)/Mona-Sans.woff2 $(FONT_SRC_DIR)/CrimsonPro-Regular.woff2 $(FONT_SRC_DIR)/hack-regular-subset.woff2 $(FONT_SRC_DIR)/hack-bold-subset.woff2
	$(create_dir)
	# TODO: Should require just subsetting!
	#       License issues! See https://github.com/github/mona-sans/issues/19
	cp $(FONT_SRC_DIR)/Mona-Sans.woff2 $(THEME_DIR)/static/fonts/MonaSans.woff2
	# TODO: Apply subsetting! Might have license issues aswell!
	cp $(FONT_SRC_DIR)/CrimsonPro-Regular.woff2 $(THEME_DIR)/static/fonts/CrimsonProRegular.woff2
	# TODO This is already a subsetted font. Evaluate again!
	cp $(FONT_SRC_DIR)/hack-regular-subset.woff2 $(THEME_DIR)/static/fonts/HackRegular.woff2
	cp $(FONT_SRC_DIR)/hack-bold-subset.woff2 $(THEME_DIR)/static/fonts/HackBold.woff2
	touch $@

# Meta target to track all required stylesheets
$(STAMP_PRE_SASS) : $(THEME_DIR)/static/style.css
	$(create_dir)
	touch $@

# Compile SASS sources to an actual stylesheet
#
# FIXME: #49
$(THEME_DIR)/static/%.css : $(STYLE_DIR)/%.scss $(SRC_STYLE) $(STAMP_PRE_FONTS) $(STAMP_NODE_READY)
	$(create_dir)
	npx sass --embed-sources --stop-on-error --verbose $< $@

$(STAMP_POST) : $(STAMP_POST_PRETTIFY)
	$(create_dir)
	touch $@

# Prettify the (HTML) build artifacts
#
# See ``util/prettify-html.py`` for implementation details. As of now this is a
# wrapper around ``tidylib``.
$(STAMP_POST_PRETTIFY) : $(STAMP_SPHINX)
	$(create_dir)
	$(MAKE) util/post-processing post-processing_cmd="{toxinidir}/util/prettify-html.py $(BUILD_DIR)"
	touch $@

# Remove build artifacts
clean :
	rm -rf $(BUILD_DIR)
	rm -rf $(STAMP_PRE_SASS)
	rm -rf $(STAMP_SPHINX)
	rm -rf $(STAMP_POST)
	rm -rf $(STAMP_POST_PRETTIFY)
	rm -rf $(THEME_DIR)/static/style.css
	rm -rf $(THEME_DIR)/static/style.css.map
.PHONY : clean

# Remove build environments
full-clean : clean
	rm -rf $(STAMP_DIR)
	rm -rf $(REPO_ROOT)/node_modules
	rm -rf $(REPO_ROOT)/.npm
	rm -rf $(REPO_ROOT)/.tox
	rm -rf $(REPO_ROOT)/.tox-venv
.PHONY : full-clean


# ##### Utility Stuff
#
# The following recipes are mainly used as shortcuts to run several tools.
# They are not directly related to the actual build process.

# Run a prepared ``tree`` command
tree :
	tree --dirsfirst -I "node_modules|requirements|LICENSE|package-lock.json|README.md"
.PHONY : tree

util/responsive-image :
	$(MAKE) util/image-processing image-processing_cmd="{toxinidir}/util/process-image.py responsive --source ./_imp/source/foo.jpg --destination ./_imp/out --required-ssim 0.97 --format png --png-compression 9 --format jpg --jpeg-compression 50 --format webp --webp-compression 45 --format avif --avif-compression 40 --size small 128 --size medium 256 --size big 512"
.PHONY : util/responsive-image

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

# Run ``stylelint``
util/lint/stylelint :
	$(MAKE) util/pre-commit pre-commit_id="stylelint" pre-commit_files="--all-files"
.PHONY : util/lint/stylelint


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

# Run commands in the ``image-processing`` environment.
image-processing_cmd ?= ""
util/image-processing : requirements/image-processing.txt pyproject.toml $(TOX_VENV_INSTALLED)
	$(TOX_CMD) -q -e image-processing -- $(image-processing_cmd)
.PHONY : util/image-processing

# Run commands in the ``pre-processing`` environment.
pre-processing_cmd ?= ""
util/pre-processing : requirements/pre-processing.txt pyproject.toml $(TOX_VENV_INSTALLED)
	$(TOX_CMD) -q -e pre-processing -- $(pre-processing_cmd)
.PHONY : util/pre-processing

# Run commands in the ``post-processing`` environment.
post-processing_cmd ?= ""
util/post-processing : requirements/post-processing.txt pyproject.toml $(TOX_VENV_INSTALLED)
	$(TOX_CMD) -q -e post-processing -- $(post-processing_cmd)
.PHONY : util/post-processing

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

# Install the required NodeJS packages
#
# Uses npm's ``ci`` to create the required NodeJS environment. It (re-) uses
# a local cache for npm in order to speed up builds during CI.
#
# https://stackoverflow.com/a/58187176
$(STAMP_NODE_READY) : package.json package-lock.json
	npm ci --cache .npm --prefer-offline
	touch $@

# Create a directory as required by other recipes
create_dir = @mkdir -p $(@D)
