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
#
# FIXME: $(SRC_THEME) should not include the source files that are meant to be
#        compiled to theme assets (e.g. the stylesheet)!
SRC_THEME := $(shell find $(THEME_DIR) -type f -not \( -name "_src" -prune \))
SRC_STYLE := $(shell find $(STYLE_DIR) -type f)

# Internal Settings
DEV_FLAG := dev
BUILD_MODE ?=

# Stamps
#
# Track certain things with artificial *stamps*.
STAMP_DIR := $(REPO_ROOT)/.make-stamps

# This stamp is **not** placed in the (internal) stamp directory. Instead, it
# is used to *tag* the build, providing the source commit SHA1 and the time of
# the build.
STAMP_BUILD_COMPLETED := $(BUILD_DIR)/build-source.txt
STAMP_CACHE_BUSTED := $(STAMP_DIR)/cache-busted
STAMP_HTML_PRETTIFIED := $(STAMP_DIR)/html-prettified
STAMP_NODE_READY := $(STAMP_DIR)/node-ready
STAMP_PRE_FONTS := $(STAMP_DIR)/fonts-ready
STAMP_SPHINX_COMPLETED := $(STAMP_DIR)/sphinx-completed
STAMP_STYLESHEET_MINIFIED := $(STAMP_DIR)/stylesheet-minified
STAMP_THEME_READY := $(STAMP_DIR)/theme-ready
STAMP_THEME_STYLES_READY := $(STAMP_DIR)/theme-styles-ready

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

# Create the actual build artifact.
build : $(STAMP_BUILD_COMPLETED)
.PHONY : build

# Build and serve in production mode.
srv/prod : | $(TOX_VENV_INSTALLED)
	$(MAKE) build && \
	$(TOX_CMD) -q -e sphinx -- python -m http.server 8082 --directory $(BUILD_DIR)
.PHONY : srv/prod

# Build and serve in development mode.
#
# In development mode some build steps are skipped, e.g. the minification of
# assets like the stylesheet. This speeds up the build process, but foremost
# it enables better developing/debugging.
srv/dev : | $(TOX_VENV_INSTALLED)
	BUILD_MODE=$(DEV_FLAG) \
	$(MAKE) build && \
	$(TOX_CMD) -q -e sphinx -- python -m http.server 8082 --directory $(BUILD_DIR)
.PHONY : srv/dev

# Finish the build process by adding the current source commit SHA1 and the
# current timestamp to a dedicated file in the $(BUILD_DIR).
$(STAMP_BUILD_COMPLETED) : $(STAMP_HTML_PRETTIFIED)
	$(create_dir)
	echo "BUILD_COMPLETED: $(BUILD_MODE)"
	echo "Commit: $(shell git rev-parse HEAD); Timestamp:  $(shell date --iso=seconds)" > $@

# Prettify the (HTML) build artifacts
#
# See ``util/prettify-html.py`` for implementation details. As of now this is a
# wrapper around ``tidylib``.
$(STAMP_HTML_PRETTIFIED) : $(STAMP_CACHE_BUSTED)
	$(create_dir)
	echo "HTML_PRETTIFIED: $(BUILD_MODE)"
	$(MAKE) util/post-processing post-processing_cmd="{toxinidir}/util/prettify-html.py $(BUILD_DIR)"
	touch $@

# Perform the Cache Busting.
#
# Cache Busting relies on the fact, that modified assets like the stylesheets
# will have a unique name by including a hash of the file's content in the
# filename.
$(STAMP_CACHE_BUSTED) : $(STAMP_SPHINX_COMPLETED) $(STAMP_STYLESHEET_MINIFIED) $(BUILD_DIR)/_static/sprite.svg
	$(create_dir)
	echo "CACHE_BUSTED: $(BUILD_MODE)"
ifeq ($(BUILD_MODE), $(DEV_FLAG))
	echo "[SKIPPED] Cache Busting is skipped in development mode"
else
	$(MAKE) util/post-processing post-processing_cmd="{toxinidir}/util/cache-busting.py --source $(BUILD_DIR) --asset _static/style.css --asset _static/sprite.svg"
endif
	touch $@

$(STAMP_STYLESHEET_MINIFIED) : $(BUILD_DIR)/_static/style.css $(STAMP_SPHINX_COMPLETED)
	$(create_dir)
	echo "STYLESHEET_MINIFIED: $(BUILD_MODE)"
ifeq ($(BUILD_MODE), $(DEV_FLAG))
	DEV_FLAG=$(DEV_FLAG) npx postcss -o $< $<
else
	npx postcss -o $< $<
endif
	touch $@

# Run ``Sphinx`` to build HTML output from reST sources
#
# This is the primary build recipe, as it will generate the HTML output by
# running ``Sphinx``. It is (obviously) dependent on a plethora of things,
# including the actual content source files and the theme files.
$(STAMP_SPHINX_COMPLETED) : $(SRC_CONTENT) $(STAMP_THEME_READY)
	$(create_dir)
	echo "SPHINX_COMPLETED: $(BUILD_MODE)"
	$(MAKE) util/sphinx/build sphinx-build_options="-W --keep-going"
	touch $@

# Track and create the additional assets of the theme.
#
# This is meant to trigger the creation of stylesheets and script files from
# source code
$(STAMP_THEME_READY) : $(STAMP_THEME_STYLES_READY) $(STAMP_PRE_FONTS) $(SRC_THEME)
	$(create_dir)
	echo "THEME_READY: $(BUILD_MODE)"
	touch $@

# Track and create the theme's stylesheets
#
# This is only a meta-target to collect the stylesheets. In fact it is desired
# to have exactly **one** stylesheet.
$(STAMP_THEME_STYLES_READY) : $(THEME_DIR)/static/style.css
	$(create_dir)
	echo "THEME_STYLES_READY: $(BUILD_MODE)"
	touch $@

# Prepare the fonts
#
# In order to optimize the fonts, the provided glyphs may be reduced
# significantly.
#
# FIXME: RENAME after implementing the new process! STAMP_THEME_FONTS_READY
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

# Compile SASS sources to an actual stylesheet
#
# During development, the sources are embedded into the stylesheet. For
# production a raw stylesheet is generated.
$(THEME_DIR)/static/%.css : $(STYLE_DIR)/%.scss $(SRC_STYLE) $(STAMP_PRE_FONTS) | $(STAMP_NODE_READY)
	$(create_dir)
	echo "build the stylesheet: $(BUILD_MODE)"
ifeq ($(BUILD_MODE), $(DEV_FLAG))
	npx sass --embed-sources --embed-source-map --stop-on-error --verbose $< $@
else
	npx sass --stop-on-error --verbose $< $@
endif

# Remove build artifacts
clean :
	rm -rf $(BUILD_DIR)
	rm -rf $(STAMP_CACHE_BUSTED)
	rm -rf $(STAMP_HTML_PRETTIFIED)
	rm -rf $(STAMP_PRE_FONTS)
	rm -rf $(STAMP_SPHINX_COMPLETED)
	rm -rf $(STAMP_THEME_READY)
	rm -rf $(STAMP_THEME_STYLES_READY)
	rm -rf $(THEME_DIR)/static/style.[BUSTING].css
	rm -rf $(THEME_DIR)/static/style.[BUSTING].css.map
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

responsive-image_src ?= ""
util/responsive-image :
	$(MAKE) util/image-processing image-processing_cmd="{toxinidir}/util/process-image.py responsive --source $(responsive-image_src) --destination ./content/img --required-ssim 0.97 --format jpg --jpeg-compression 50 --format webp --webp-compression 45 --format avif --avif-compression 40 --size 320 320 --size 480 480 --size 640 640 --size 960 960 --size 1280 1280 --size 1600 1600 --size 1920 1920"
.PHONY : util/responsive-image

# Run all linters through ``pre-commit``
util/lint/all : | $(STAMP_NODE_READY)
	$(MAKE) util/pre-commit pre-commit_files="--all-files"
.PHONY : util/lint/all

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
util/pre-commit : | $(PRE_COMMIT_READY)
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
util/sphinx/build : conf.py requirements/sphinx.txt pyproject.toml | $(TOX_VENV_INSTALLED)
	$(TOX_CMD) -q -e sphinx -- sphinx-build $(sphinx-build_options) -b $(sphinx_builder) -c $(sphinx_config-dir) $(CONTENT_DIR) $(BUILD_DIR)
.PHONY : util/sphinx/build

# Run commands in the ``image-processing`` environment.
image-processing_cmd ?= ""
util/image-processing : requirements/image-processing.txt pyproject.toml | $(TOX_VENV_INSTALLED)
	$(TOX_CMD) -q -e image-processing -- $(image-processing_cmd)
.PHONY : util/image-processing

# Run commands in the ``pre-processing`` environment.
pre-processing_cmd ?= ""
util/pre-processing : requirements/pre-processing.txt pyproject.toml | $(TOX_VENV_INSTALLED)
	$(TOX_CMD) -q -e pre-processing -- $(pre-processing_cmd)
.PHONY : util/pre-processing

# Run commands in the ``post-processing`` environment.
post-processing_cmd ?= ""
util/post-processing : requirements/post-processing.txt pyproject.toml | $(TOX_VENV_INSTALLED)
	$(TOX_CMD) -q -e post-processing -- $(post-processing_cmd)
.PHONY : util/post-processing

# (Re-) Generate the requirements files using pip-tools (``pip-compile``)
#
# ``pip-compile`` is run through a ``tox`` environment. The actual command is
# included in ``tox``'s configuration in ``pyproject.toml``. That's why that
# file is an additional prerequisite. This may lead to additional
# regenerations, but these will most likely not affect the generated files.
requirements/%.txt : requirements/%.in pyproject.toml | $(TOX_VENV_INSTALLED)
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
	$(create_dir)
	npm ci --cache .npm --prefer-offline
	touch $@

# Create a directory as required by other recipes
create_dir = @mkdir -p $(@D)
