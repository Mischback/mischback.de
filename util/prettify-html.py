#!/usr/bin/env python3

"""Prettify the HTML output from Sphinx."""


# Python imports
import argparse


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
    inputs = parse_args()
    print(inputs.build_dir)


if __name__ == "__main__":
    main()
