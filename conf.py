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
from os.path import abspath, dirname, join

# Determine the absolute path of the repository's root
REPO_ROOT = dirname(abspath(__file__))


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
    # TODO: "sphinx.ext.graphviz"
    #       If there is a use-case for these diagrams.
    # TODO: "sphinx.ext.ifconfig"
    #       Conditional content. Most likely not required.
    # TODO: "sphinx.ext.intersphinx"
    #       If there is a use-case for this. Might better be realized using
    #       ``extlinks``.
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
root_doc = "aux/sitemap"

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
    "commit": ("https://github.com/Mischback/static-web/commit/%s", "%s"),
    "wikipedia": ("https://en.wikipedia.org/wiki/%s", "Wikipedia: %s"),
}

# Make ``sphinx.ext.extlinks`` emit warnings, if a shortcut is available.
extlinks_detect_hardcoded_links = True


# ### HTML configuration

# The custom theme is placed in a folder ``theme``
#
# https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-html_theme_path
html_theme_path = [join(REPO_ROOT, "theme")]

# The name of the custom theme
#
# https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-html_theme
html_theme = "mischback"

# Do **not** include the reST sources
#
# https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-html_copy_source
html_copy_source = False


# ### Internal plugin stuff
#
# ``Sphinx``'s configuration file actually works like an extension.


def activate_jinja2_debug_ext(app):
    """Activate Jinja2 debug extension.

    This function is intended to be connected to ``Sphinx``'s
    ``builder-inited`` event (see
    https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx-core-events)
    and will then navigate from the app to the ``jinja.Environment`` and call
    its ``add_extension()`` method.
    """
    if hasattr(app.builder, "templates"):
        app.builder.templates.environment.add_extension("jinja2.ext.debug")


def setup(app):
    """Use this ``conf.py`` as its project's own extension."""
    # Connect a custom handler to the ``builder-inited`` event.
    #
    # https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx-core-events
    app.connect("builder-inited", activate_jinja2_debug_ext)
