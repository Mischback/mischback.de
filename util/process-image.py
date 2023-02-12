#!/usr/bin/env python3

"""Process a source image to create the required responsive versions."""


# Python imports
import argparse
import logging
import logging.config
from pathlib import Path

# external imports
import pyvips

# get a module-level logger
logger = logging.getLogger()

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
        "": {
            "handlers": ["default"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}

# define some constants
TFORMAT_JPG = "jpg"
TFORMAT_PNG = "png"
TFORMAT_WEBP = "webp"
TFORMAT_AVIF = "avif"

DEF_JPEG_COMPRESSION = 75
DEF_JPEG_INTERLACE = True
DEF_PNG_COMPRESSION = 6
DEF_PNG_INTERLACE = True
DEF_WEBP_COMPRESSION = 75
DEF_WEBP_LOSSLESS = None
DEF_AVIF_COMPRESSION = 50
DEF_AVIF_LOSSLESS = None


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
    parser.add_argument(
        "--jpeg-compression",
        action="store",
        type=int,
        choices=range(0, 100),
        default=DEF_JPEG_COMPRESSION,
        required=False,
        help="The compression factor for JPEG (default: {})".format(
            DEF_JPEG_COMPRESSION
        ),
    )
    parser.add_argument(
        "--jpeg-no-interlace",
        action="store_false",
        required=False,
        help="Don't use interlace mode for JPEGs",
    )
    parser.add_argument(
        "--png-compression",
        action="store",
        type=int,
        choices=range(0, 9),
        default=DEF_PNG_COMPRESSION,
        required=False,
        help="The compression factor for PNG (default: {})".format(DEF_PNG_COMPRESSION),
    )
    parser.add_argument(
        "--png-no-interlace",
        action="store_false",
        required=False,
        help="Don't use interlace mode for PNGs",
    )
    parser.add_argument(
        "--webp-compression",
        action="store",
        type=int,
        choices=range(0, 100),
        default=DEF_WEBP_COMPRESSION,
        required=False,
        help="The compression factor for WebP (default: {})".format(
            DEF_WEBP_COMPRESSION
        ),
    )
    parser.add_argument(
        "--webp-force-lossless",
        action="store",
        default=DEF_WEBP_LOSSLESS,
        help="Force lossless-mode for WebP compression",
    )
    parser.add_argument(
        "--avif-compression",
        action="store",
        type=int,
        choices=range(0, 100),
        default=DEF_AVIF_COMPRESSION,
        required=False,
        help="The compression factor for AVIF (default: {})".format(
            DEF_AVIF_COMPRESSION
        ),
    )
    parser.add_argument(
        "--avif-force-lossless",
        action="store",
        default=DEF_AVIF_LOSSLESS,
        help="Force lossless-mode for AVIF compression",
    )

    return parser.parse_args()


def _compress_jpg(
    img, dest, compression_factor=DEF_JPEG_COMPRESSION, interlace=DEF_JPEG_INTERLACE
):
    """Apply JPEG compression and save the file to disk.

    This function exposes some JPEG compression settings, but other options are
    pre-defined and set aiming for minimal file sizes, at the cost of
    computation time.

    Parameters
    ----------
    img :
        The image to be compressed, provided as ``libvips`` Image object.
    dest : ``Path``
        The destination, the full path/filename (including the suffix) for the
        output file.
    compression_factor : int
        The JPEG compression factor (0-100; default: 75).
    interlace : bool
        Flag controlling the generation of progressive JPEGs (default: True).
    """
    logger.debug("_compress_jpg()")
    logger.debug("img: %r", img)
    logger.debug("dest: %s", dest)
    logger.debug("compression_factor: %d", compression_factor)
    logger.debug("interlace: %r", interlace)

    return img.jpegsave(
        dest,
        Q=compression_factor,
        profile="none",
        optimize_coding=True,
        interlace=interlace,
        strip=True,
        trellis_quant=True,
        overshoot_deringing=True,
        optimize_scans=True,
        quant_table=3,
    )


def _compress_png(
    img, dest, compression_factor=DEF_PNG_COMPRESSION, interlace=DEF_PNG_INTERLACE
):
    """Apply PNG compression and save the file to disk.

    This function exposes some PNG compression settings, but other options are
    pre-defined and set aiming for minimal file sizes, at the cost of
    computation time.

    Parameters
    ----------
    img :
        The image to be compressed, provided as ``libvips`` Image object.
    dest : ``Path``
        The destination, the full path/filename (including the suffix) for the
        output file.
    compression_factor : int
        The PNG compression factor (0-9; default: 6).
    interlace : bool
        Flag controlling the generation of interlaced PNG (default: True).
    """
    logger.debug("_compress_png()")
    logger.debug("img: %r", img)
    logger.debug("dest: %s", dest)
    logger.debug("compression_factor: %d", compression_factor)
    logger.debug("interlace: %r", interlace)

    return img.pngsave(
        dest,
        compression=compression_factor,
        interlace=interlace,
        profile="none",
        palette=False,
    )


def _compress_webp(
    img, dest, compression_factor=DEF_WEBP_COMPRESSION, lossless=DEF_WEBP_LOSSLESS
):
    """Apply WebP compression and save the file to disk.

    This function exposes some WebP compression settings, but other options are
    pre-defined and set aiming for minimal file sizes, at the cost of
    computation time.

    Parameters
    ----------
    img :
        The image to be compressed, provided as ``libvips`` Image object.
    dest : ``Path``
        The destination, the full path/filename (including the suffix) for the
        output file.
    compression_factor : int
        The WebP compression factor (0-100; default: 75).
    lossless : bool, None
        Flag controlling the *lossless* mode; if set to ``None``, this will be
        determined automatically, depending on the input file format, or - more
        specifically - if the input file format is a lossless format, the
        output will be lossless aswell.
    """
    logger.debug("_compress_webp()")
    logger.debug("img: %r", img)
    logger.debug("dest: %s", dest)
    logger.debug("compression_factor: %d", compression_factor)
    logger.debug("lossless: %r", lossless)

    if lossless is None:
        if img.get("vips-loader") == "jpegload":
            lossless = False
        else:
            lossless = True

    return img.webpsave(
        dest,
        Q=compression_factor,
        lossless=lossless,
        effort=6,
        strip=True,
        profile="none",
    )


def _compress_avif(
    img, dest, compression_factor=DEF_AVIF_COMPRESSION, lossless=DEF_AVIF_LOSSLESS
):
    """Apply Avif compression and save the file to disk.

    This function exposes some Avif compression settings, but other options are
    pre-defined and set aiming for minimal file sizes, at the cost of
    computation time.

    Parameters
    ----------
    img :
        The image to be compressed, provided as ``libvips`` Image object.
    dest : ``Path``
        The destination, the full path/filename (including the suffix) for the
        output file.
    compression_factor : int
        The Avif compression factor (0-100; default: 50).
    lossless : bool, None
        Flag controlling the *lossless* mode; if set to ``None``, this will be
        determined automatically, depending on the input file format, or - more
        specifically - if the input file format is a lossless format, the
        output will be lossless aswell.
    """
    logger.debug("_compress_avif()")
    logger.debug("img: %r", img)
    logger.debug("dest: %s", dest)
    logger.debug("compression_factor: %d", compression_factor)
    logger.debug("lossless: %r", lossless)

    if lossless is None:
        if img.get("vips-loader") == "jpegload":
            lossless = False
        else:
            lossless = True

    return img.heifsave(
        dest,
        Q=compression_factor,
        lossless=lossless,
        effort=9,
    )


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
    logger.debug("_compress()")
    logger.debug("img: %r", img)
    logger.debug("dest_dir: %s", dest_dir)
    logger.debug("target_format: %s", target_format)

    dest = Path(dest_dir, Path(img.filename).stem).with_suffix(
        ".{}".format(target_format.lower())
    )
    logger.debug("dest: %s", dest)

    if target_format == TFORMAT_JPG:
        return _compress_jpg(img, dest)
    elif target_format == TFORMAT_PNG:
        return _compress_png(img, dest)
    elif target_format == TFORMAT_WEBP:
        return _compress_webp(img, dest)
    elif target_format == TFORMAT_AVIF:
        return _compress_avif(img, dest)
    else:
        # FIXME: **real** error handling required!
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
    logger.debug("cmd_compress()")
    logger.debug("source: %s", source)
    logger.debug("dest_dir: %s", dest_dir)
    logger.debug("target_formats: %r", target_formats)

    # open the source for/with ``libvips``
    img = pyvips.Image.new_from_file(source)

    logger.info("Compressing %s into the following formats: %r", source, target_formats)

    for t in target_formats:
        _compress(img, dest_dir, t)


def main():
    """Execute the processing."""
    # get the arguments
    args = parse_args()

    logger.debug("args: %r", args)

    if args.command == "compress":
        cmd_compress(args.source, args.destination, args.format)


if __name__ == "__main__":
    # setup the logging module
    logging.config.dictConfig(LOGGING_DEFAULT_CONFIG)

    main()
