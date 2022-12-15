#!/usr/bin/env python3

"""Prettify the HTML output from Sphinx.

This script is a thin wrapper around ``tidylib`` as provided by
https://github.com/htacg/tidy-html5 . ``tidylib`` is used through
https://github.com/nijel/utidylib but must be installed on the system manually
(for Debian / debian-based systems this is done from the ``tidy`` package).

The script expects a single argument ``build_dir``, that is the directory with
the files to be processed. It will find all ``.html`` files in that directory
recursively (including all sub-directories) and process them.

Processing happens *in place*, meaning the existing files will be overwritten
with this script's outputs.
"""


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
            tmp = tidy.parseString(
                raw.read(),
                doctype="html5",
                indent="auto",
                indent_spaces=2,
                indent_attributes="no",
                sort_attributes="alpha",
                tidy_mark="no",
                wrap=0,
            )

        # tmp is of type Document and does provide a method ``get_errors()``
        # This might be the place to handle these errors in some smart way,
        # e.g. just print them to the console.
        # However: It is assumed, that any error here will lead to validation
        # errors in CI, so it might not be really relevant.
        # Reference: https://utidylib.readthedocs.io/en/latest/#tidy.Document

        with open(file, "w") as out:
            out.write(tmp.gettext())


if __name__ == "__main__":
    main()
