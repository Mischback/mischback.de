"""Configure Sphinx for the actual website.

This is the main configuration file. It will be used to build the static
website from the provided sources. It is obviously focused on building HTML
output, running the ``dirhtml`` builder (which allows for *pretty* urls without
filename suffixes).

The build command is included in ``pyproject.toml``. It is run from a dedicated
``tox`` environment (``build-sphinx``).

``Sphinx``'s configuration reference may be found here:
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

# Python imports
import datetime
import subprocess


def get_current_git_commit_hash():
    """Return the current commit's hash.

    https://stackoverflow.com/a/21901260
    """
    return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("ascii").strip()


# ### General project information
#
# This will most likely not show up in the real website, but for the sake of
# completeness...
#
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
project = "mischback.de"
author = "Mischback"
copyright = "{}, {}".format(datetime.datetime.now().year, author)
version = "0.0.1-alpha"
release = get_current_git_commit_hash()

# This document contains the *master TOC*.
#
# It is not necessarily the ``index.rst``, so we can build the actual
# navigation logic without caring (too much) about ``sphinx``'s internal
# toc-related logic.
#
# Do not mistake this for an actual ``sitemap.xml`` (as defined by
# https://www.sitemaps.org/). This document will create HTML output and is
# considered a human-readable (or better: human-consumable) version of a
# sitemap, more like a table of contents.
#
# https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-root_doc
root_doc = "sitemap"
