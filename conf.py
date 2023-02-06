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
import sys
from os.path import abspath, dirname, join

# Determine the absolute path of the repository's root
REPO_ROOT = dirname(abspath(__file__))

# Add the project-specific extensions directory to Python's path
sys.path.append(join(REPO_ROOT, "extensions"))


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


# ### General configuration

# Activate extensions.
#
# https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-extensions
#
# For a list of built-in extensions, see
# https://www.sphinx-doc.org/en/master/usage/extensions/index.html#built-in-extensions
extensions = [
    # Automatically generate labels for sections.
    #
    # https://www.sphinx-doc.org/en/master/usage/extensions/autosectionlabel.html
    "sphinx.ext.autosectionlabel",
    # Measures ``sphinx``'s processing, primarily for debugging.
    #
    # https://www.sphinx-doc.org/en/master/usage/extensions/duration.html
    "sphinx.ext.duration",
    # Shorter notation for external links.
    #
    # Not really sure, if this will be useful for this project, but it works
    # really well for my *real* documentation repositories.
    #
    # https://www.sphinx-doc.org/en/master/usage/extensions/extlinks.html
    "sphinx.ext.extlinks",
    # Provide 404 pages
    #
    # This automatically generates a valid 404 page.
    #
    # https://github.com/readthedocs/sphinx-notfound-page
    "notfound.extension",
    "mischback.content_tags",
    "mischback.sphinx_jinja2_debug",
    # "sphinx.ext.graphviz"
    # If there is a use-case for these diagrams.
    # "sphinx.ext.ifconfig"
    # Conditional content. Most likely not required.
    # "sphinx.ext.intersphinx"
    # If there is a use-case for this. Might better be realized using
    # ``extlinks``.
]


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

# Set the default domain.
#
# As ``sphinx`` is primarily intended for software documentation, the default
# domain may be used to define the primary programming language of a project.
# However, since this is just a website, disable the default domain. Hopefully
# this will also work out, while addressing different programming languages
# in different postings.
#
# https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-primary_domain
primary_domain = None

# Set the default highlight language.
#
# As ``sphinx`` was initially developed for Python projects, the default
# language is (a superset of) Python.
#
# The website will (most likely) address different programming languages, so
# the default language is set to pure text, requiring to be explicit while
# including source code.
#
# https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-highlight_language
highlight_language = "text"

# Define the minimum required version of ``sphinx``.
#
# This is most likely not relevant, as the project uses *requirements files*
# to define the required versions while setting up the ``tox`` environment
# to run ``sphinx``.
#
# https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-needs_sphinx
needs_sphinx = "4.5"

# Warn about all references where the target can not be found.
#
# This is equivalent to running ``sphinx-build -n``, but it should be the
# default for the project.
#
# Please note that by default, ``sphinx-build`` is run with ``-W``, meaning
# that all warnings will be treated as errors and thus, failing the build.
#
# https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-nitpicky
nitpicky = True


# ### Plugin configuration

# Prefix the automatically generated section labels with the document.
autosectionlabel_prefix_document = True

# The shortcuts for ``sphinx.ext.extlinks``.
extlinks = {
    "commit": ("https://github.com/Mischback/mischback.de/commit/%s", "%s"),
    "wikipedia": ("https://en.wikipedia.org/wiki/%s", "Wikipedia: %s"),
}

# Make ``sphinx.ext.extlinks`` emit warnings, if a shortcut is available.
extlinks_detect_hardcoded_links = True

notfound_urls_prefix = "/"
# ``notfound_template`` is not specified here, as Sphinx normally renders the
# file ``content/404.rst``, using the project's internal logic to determine the
# template to be used.


# ### HTML configuration

# The custom theme is placed in a folder ``theme``
#
# https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-html_theme_path
html_theme_path = [join(REPO_ROOT, "theme")]

# The name of the custom theme
#
# https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-html_theme
html_theme = "mischback"

html_theme_options = {
    "show_breadcrumbs": True,
}

# Do **not** include the reST sources
#
# https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-html_copy_source
html_copy_source = False

# Add permalinks to all headings and make them available with a custom icon.
html_permalinks = True
html_permalinks_icon = "#"
