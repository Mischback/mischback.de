"""Provide *responsive images* for HTML-based output."""


# Python imports
import logging
import logging.config

# Sphinx imports
from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.environment.collectors import EnvironmentCollector
from sphinx.util import FilenameUniqDict

EXTENSION_LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "console_output": {
            "format": "[%(levelname)s] [%(name)s:%(lineno)d] %(message)s",
        },
    },
    "handlers": {
        "default": {
            "level": "DEBUG",
            "formatter": "console_output",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "": {
            "handlers": ["default"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}

# FIXME: Development only! The desired setup integrates into Sphinx's logging
#        system!
#        ``from sphinx.util import logging`` and remove the configuration of
#        ``logging`` here!
logging.config.dictConfig(EXTENSION_LOGGING)

# get a module-level logger
logger = logging.getLogger(__name__)


class ResponsiveImageCollector(EnvironmentCollector):  # noqa D101
    def clear_doc(self, app, env, docname):  # noqa D102
        env.responsive_images.purge_doc(docname)

    def merge_other(self, app, env, docnames, other):  # noqa D102
        env.responsive_images.merge_other(docnames, other.responsive_images)

    def process_doc(self, app, doctree):  # noqa D102
        logger.debug("ResponsiveImageCollector.process_doc()")


def integrate_into_build_process(app):
    """Integrate the extension into Sphinx's build process.

    The extension is developed with HTML output in mind, providing the required
    markup for *responsive images*. It has no purpose for other output formats,
    so the setup of the extension is done here, as this function is executed
    when the builder has been determined.

    This function is meant to be attached to Sphinx's ``builder-inited`` event.
    See :func:`setup`.
    """
    # Only intgegrate the extension if this is an HTML build
    logger.debug("Detecting builder: %r", app.builder)
    if not isinstance(app.builder, StandaloneHTMLBuilder):
        logger.info("Detected a non-HTML builder. Skipping extension setup!")
        return

    # Setup the specific ``EnvironmentCollector`` for the responsive image sources
    if not hasattr(app.env, "responsive_images"):
        app.env.responsive_images = FilenameUniqDict()
    app.add_env_collector(ResponsiveImageCollector)


def setup(app):
    """Register the extension with Sphinx.

    This function is required by Sphinx's extension interface, see
    https://www.sphinx-doc.org/en/master/development/tutorials/helloworld.html#writing-the-extension
    for reference.
    """
    # When the builder is set up, we can determine if we're running an HTML
    # build. Only in this case, all other magic of this extension needs to be
    # applied.
    app.connect("builder-inited", integrate_into_build_process)

    return {
        "version": "0.0.1",
        "env-version": "1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
