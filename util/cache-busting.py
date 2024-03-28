#!/usr/bin/env python3

"""Custom script to perform cache busting for static assets."""

# Python imports
import logging
import logging.config

# get a module-level logger
logger = logging.getLogger(__name__)

LOGGING_DEFAULT_CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "console_output": {
            "format": "[%(levelname)s] %(name)s: %(message)s",
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
        __name__: {
            "handlers": ["default"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}


def main():
    """Perform the cache busting when executing the script from command line."""
    logger.info("foo")


if __name__ == "__main__":
    # setup the logging module
    logging.config.dictConfig(LOGGING_DEFAULT_CONFIG)

    main()
