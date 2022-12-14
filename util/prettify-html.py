#!/usr/bin/env python3

"""Prettify the HTML output from Sphinx."""


# Python imports
import argparse
import glob
import os

# external imports
import tidy


def parse_args():
    """Parse the command line arguments.

    The function sets up the ``ArgumentParser`` and returns the parsed
    arguments for further processing.
    """
    parser = argparse.ArgumentParser(description="Prettify HTML files")

    # mandatory arguments
    parser.add_argument(
        "build_dir", action="store", help="Directory containing the build files"
    )

    return parser.parse_args()


def main():
    """Perform the prettification.

    This is the script's main function, performing the actual operations.
    """
    # get the arguments
    args = parse_args()

    # see https://stackoverflow.com/a/40755802
    build_dir = os.path.abspath(args.build_dir)
    for file in glob.iglob("{}/**/*.html".format(build_dir), recursive=True):
        with open(file, "r") as raw:
            tmp = raw.read()

        print(
            tidy.parseString(
                tmp,
                doctype="html5",
                indent="auto",
                indent_spaces=2,
                indent_attributes="no",
                sort_attributes="alpha",
                wrap=0,
            )
        )


if __name__ == "__main__":
    main()
