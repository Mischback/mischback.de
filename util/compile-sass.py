#!/usr/bin/env python3

"""Compile SASS sources to the actual stylesheet."""


# Python imports
import argparse
import os

# external imports
import sass


def parse_args():
    """Parse the command line arguments.

    The function sets up the ``ArgumentParser`` and returns the parsed
    arguments for further processing.
    """
    parser = argparse.ArgumentParser(description="Compile SASS sources")

    # mandatory arguments
    parser.add_argument("source", action="store", help="The source file to be compiled")
    parser.add_argument("target", action="store", help="The desired output filename")

    return parser.parse_args()


def main():
    """Perform the actual compilation."""
    # get the arguments
    args = parse_args()

    source = os.path.abspath(args.source)
    print("[DEBUG] source: {}".format(source))

    target = os.path.abspath(args.target)
    print("[DEBUG] target: {}".format(target))

    tmp = sass.compile(filename=source, output_style="expanded")

    with open(target, "w") as output:
        output.write(tmp)


if __name__ == "__main__":
    main()
