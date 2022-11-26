"""Configuration file for Sphinx."""

# Python imports
import datetime

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "mischback.de"
author = "Mischback"
copyright = "{}, {}".format(datetime.datetime.now().year, author)

# This document contains the *master TOC*.
#
# It is not necessarily the ``index.rst``, so we can build the actual
# navigation logic without caring (too much) about ``sphinx``'s internal
# toc-related logic.
#
# Ref: https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-root_doc
root_doc = "sitemap"
