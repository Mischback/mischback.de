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

    parser.add_argument(
        "command",
        choices=["compress"],
        action="store",
        type=str,
        help="Determine the script's mode of operation",
    )
    parser.add_argument(
        "--source", action="store", type=str, required=True, help="The source file"
    )
    parser.add_argument(
        "--destination",
        action="store",
        type=str,
        required=True,
        help="Path to the destination directory",
    )
    parser.add_argument(
        "--format",
        choices=["jpg", "png", "webp", "avif"],
        action="append",
        type=str,
        required=True,
        help="The desired output format(s)",
    )

    return parser.parse_args()


def cmd_compress():  # noqa D103
    print("[DEBUG] command: compress")


def main():
    """Execute the processing."""
    # get the arguments
    args = parse_args()

    print("[DEBUG] args: {}".format(args))

    if args.command == "compress":
        cmd_compress()


if __name__ == "__main__":
    main()
