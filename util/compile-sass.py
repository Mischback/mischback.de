#!/usr/bin/env python3

"""Compile SASS sources to the actual stylesheet.

This script uses ``libsass``'s Python bindings to compile SASS sources to
actual deployable stylesheets.

The script expects two mandatory arguments, the ``source`` file and the desired
``target`` file.

Optionally, this script might be run with ``--debug`` (``-d``) to activate
*debug messages*.
"""


# Python imports
import argparse
import logging
import logging.config
import os
import sys

# external imports
import sass

# get a module-level logger
logger = logging.getLogger()

# provide a default config for Python's logging
LOGGING_DEFAULT_CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "console_output": {
            "format": "[%(levelname)s] %(message)s",
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
            "level": "INFO",
            "propagate": True,
        },
    },
}


def parse_args():
    """Parse the command line arguments.

    The function sets up the ``ArgumentParser`` and returns the parsed
    arguments for further processing.
    """
    logger.debug("Setting up ArgumentParser")

    parser = argparse.ArgumentParser(description="Compile SASS sources")

    # mandatory arguments
    parser.add_argument("source", action="store", help="The source file to be compiled")
    parser.add_argument("target", action="store", help="The desired output filename")

    # optional arguments
    parser.add_argument(
        "-c", "--compressed", action="store_true", help="Generate compressed CSS output"
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Enable debug messages"
    )

    return parser.parse_args()


def main():
    """Perform the actual compilation."""
    logger.debug("Running main()")

    # get the arguments
    args = parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("DEBUG messages enabled")

    # Determine the output style
    #
    # libsass accepts "compact", "compressed", "expanded" and "nested".
    # Ref: https://sass.github.io/libsass-python/sass.html#sass.OUTPUT_STYLES
    #
    # By default, the script uses "expanded", but may be switched to
    # "compressed" using the ``-c`` flag.
    out_style = "expanded"
    src_comments = True
    if args.compressed:
        logger.debug("Compression activated!")
        out_style = "compressed"
        src_comments = False

    # Ensure that paths are absolute.
    #
    # Note: When using this script from the project's Makefile, all paths are
    # already absolute.
    source = os.path.abspath(args.source)
    logger.debug("source: %r", source)

    target = os.path.abspath(args.target)
    logger.debug("target: %r", target)

    try:
        # TODO: Is sourcemap support required?!
        #       Ref: https://sass.github.io/libsass-python/sass.html#sass.compile
        tmp = sass.compile(
            filename=source, output_style=out_style, source_comments=src_comments
        )
    except IOError as e:
        logger.critical("Could not read source file '%s'!", source)
        logger.info(e, exc_info=False)  # noqa: G200
        sys.exit(1)
    except sass.CompileError as e:
        logger.critical("Could not compile '%s'!", source)
        logger.info(e, exc_info=False)  # noqa: G200
        sys.exit(1)

    with open(target, "w") as output:
        output.write(tmp)

    logger.debug("Compilation of '%s' successful!", source)
    logger.info("Wrote output file '%s'", target)
    sys.exit(0)


if __name__ == "__main__":
    logging.config.dictConfig(LOGGING_DEFAULT_CONFIG)
    main()
