#!/usr/bin/env python3

"""Process a source image to create the required responsive versions."""


# Python imports
import argparse


def parse_args():
    """Parse the command line arguments.

    The function sets up the ``ArgumentParser`` and returns the parsed
    arguments for further processing.
    """
    parser = argparse.ArgumentParser(
        description="Create required responsive images from source file"
    )

    # mandatory arguments
    parser.add_argument(
        "source_file", action="store", help="Path/name of the source file"
    )
    parser.add_argument(
        "destination_directory",
        action="store",
        help="Path to the destination directory",
    )

    return parser.parse_args()


def main():
    """Execute the processing."""
    # get the arguments
    args = parse_args()

    print("[DEBUG] args: {}".format(args))


if __name__ == "__main__":
    main()
