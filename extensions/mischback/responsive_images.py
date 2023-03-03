"""Provide *responsive images* for HTML-based output."""


# Python imports
import logging
import logging.config

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
logging.config.dictConfig(EXTENSION_LOGGING)

# get a module-level logger
logger = logging.getLogger(__name__)


def setup(app):
    """Register the extension with Sphinx.

    This function is required by Sphinx's extension interface, see
    https://www.sphinx-doc.org/en/master/development/tutorials/helloworld.html#writing-the-extension
    for reference.
    """
    logger.debug("setup() for responsive_images extension")

    return {
        "version": "0.0.1",
        "env-version": "1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
