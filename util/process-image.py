#!/usr/bin/env python3

"""Process a source image to create the required responsive versions."""


# Python imports
import argparse
from pathlib import Path

# external imports
import pyvips

TFORMAT_JPG = "jpg"
TFORMAT_PNG = "png"
TFORMAT_WEBP = "webp"
TFORMAT_AVIF = "avif"


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
        choices=[TFORMAT_JPG, TFORMAT_PNG, TFORMAT_WEBP, TFORMAT_AVIF],
        action="append",
        type=str,
        required=True,
        help="The desired output format(s)",
    )

    return parser.parse_args()


def _compress_jpg(img, dest):
    print("[DEBUG] _compress_jpg()")
    print("[DEBUG] img:  {}".format(img))
    print("[DEBUG] dest: {}".format(dest))

    return img.jpegsave(dest, Q=100, optimize_coding=True, strip=True)


def _compress(img, dest_dir, target_format):
    """Apply compression to an image.

    Parameters
    ----------
    img :
        The image to be compressed, provided as ``libvips`` Image object.
    dest_dir : str
        The directory to place the output file(s) into.
    target_format : str
        The desired output format.
    """
    print("[DEBUG] _compress()")
    print("[DEBUG] img:           {}".format(img))
    print("[DEBUG] dest_dir:      {}".format(dest_dir))
    print("[DEBUG] target_format: {}".format(target_format))

    dest = Path(dest_dir, Path(img.filename).stem).with_suffix(
        ".{}".format(target_format.lower())
    )
    print("[DEBUG] dest:          {}".format(dest))

    # TODO: Implement the actual compression calls in dedicated functions
    if target_format == TFORMAT_JPG:
        return _compress_jpg(img, dest)
    elif target_format == TFORMAT_PNG:
        pass
    elif target_format == TFORMAT_WEBP:
        pass
    elif target_format == TFORMAT_AVIF:
        pass
    else:
        print("[ERROR] Unknown target format!")


def cmd_compress(source, dest_dir, target_formats):
    """Provide the compression mode of operation.

    The compression and disk I/O is implemented by ``_compress()``,this
    function just picks up the source file and then calls the actual payload.

    Parameters
    ----------
    source : str
        The path to and filename of the source file.
    dest_dir : str
        The directory to place the output file(s) into.
    target_formats : list
        A list of ``str`` of desired target formats.
    """
    print("[DEBUG] cmd_compress()")
    print("[DEBUG] source:         {}".format(source))
    print("[DEBUG] dest_dir:       {}".format(dest_dir))
    print("[DEBUG] target_formats: {}".format(target_formats))

    # open the source for/with ``libvips``
    img = pyvips.Image.new_from_file(source)

    for t in target_formats:
        _compress(img, dest_dir, t)


def main():
    """Execute the processing."""
    # get the arguments
    args = parse_args()

    print("[DEBUG] args: {}".format(args))

    if args.command == "compress":
        cmd_compress(args.source, args.destination, args.format)


if __name__ == "__main__":
    main()
