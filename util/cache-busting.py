#!/usr/bin/env python3

"""Custom script to perform cache busting for static assets."""

# Python imports
import argparse
import logging
import logging.config
from pathlib import Path

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


def parse_args():
    """Parse the command line arguments."""
    # create the main parser
    parser = argparse.ArgumentParser(
        description="Perform cache busting for static assets"
    )

    parser.add_argument(
        "--source",
        action="store",
        type=str,
        required=True,
        help="Path to the source directory",
    )

    parser.add_argument(
        "--asset",
        dest="assets",
        action="append",
        type=str,
        required=True,
        help="Relative path from source directory to an asset file",
    )

    return parser.parse_args()


def main():
    """Perform the cache busting when executing the script from command line."""
    args = parse_args()
    logger.debug("args: %r", args)

    source = Path(args.source)
    logger.debug("source: %r", source)

    assets = {Path(a) for a in args.assets}
    logger.debug("assets: %r", assets)


if __name__ == "__main__":
    # setup the logging module
    logging.config.dictConfig(LOGGING_DEFAULT_CONFIG)

    main()
