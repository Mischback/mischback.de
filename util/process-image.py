#!/usr/bin/env python3

"""Process a source image to create the required responsive versions."""


# Python imports
import argparse


def parse_args():
    """Parse the command line arguments.

    The function sets up the ``ArgumentParser`` and returns the parsed
    arguments for further processing.
    """
    # create the main parser
    parser = argparse.ArgumentParser(description="Create required responsive images")

    # create a subparser for commands
    subparser = parser.add_subparsers(
        dest="command", required=True, help="The command to be run"
    )

    # create the parser for ``resize`` command
    resize = subparser.add_parser("resize")
    resize.add_argument(
        "--source", action="store", type=str, required=True, help="The source file"
    )
    resize.add_argument(
        "--destination",
        action="store",
        type=str,
        required=True,
        help="Path to the destination directory",
    )
    resize.add_argument(
        "--size",
        action="append",
        nargs=2,
        required=True,
        help="A combination of semantic name and a width in pixels",
    )
    resize.add_argument(
        "--format", action="append", help="The desired target format(s)"
    )

    # create the parser for ``compress`` command
    compress = subparser.add_parser("compress")
    compress.add_argument(
        "--source", action="store", type=str, required=True, help="The source file"
    )
    compress.add_argument(
        "--format", action="append", help="The desired target format(s)"
    )

    return parser.parse_args()


def compress():  # noqa D103
    print("[DEBUG] command: compress")


def resize(sizes):  # noqa D103
    print("[DEBUG] command: resize")
    print("[DEBUG] sizes: {}".format(sizes))

    # TODO: create the pipelines for resizing, based on ``args.size``, writing
    #       the files to a *temporary directory* in a lossless format without
    #       any compression.

    # TODO: call ``compress()`` with the desired formats.


def main():
    """Execute the processing."""
    # get the arguments
    args = parse_args()

    print("[DEBUG] args: {}".format(args))

    if args.command == "resize":
        resize(args.size)
    elif args.command == "compress":
        compress()


if __name__ == "__main__":
    main()
