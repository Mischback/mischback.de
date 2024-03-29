#!/usr/bin/env python3

"""Process a source image to create the required responsive versions."""


# Python imports
import argparse
import logging
import logging.config
import math
from pathlib import Path

# external imports
import pyvips
from skimage.metrics import structural_similarity as ssim

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
            "level": "INFO",
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
        choices=["compress", "responsive"],
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
        "--size",
        nargs=2,
        dest="sizes",
        action="append",
        required=False,
        help="The desired output size(s)",
    )
    parser.add_argument(
        "--format",
        dest="formats",
        choices=[TFORMAT_JPG, TFORMAT_PNG, TFORMAT_WEBP, TFORMAT_AVIF],
        action="append",
        type=str,
        required=True,
        help="The desired output format(s)",
    )
    parser.add_argument(
        "--required-ssim",
        action="store",
        type=float,
        required=False,
        help="The required structural similarity",
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
        dest="jpeg_interlace",
        action="store_false",
        required=False,
        help="Don't use interlace mode for JPEGs",
    )
    parser.add_argument(
        "--png-compression",
        action="store",
        type=int,
        choices=range(0, 10),
        default=DEF_PNG_COMPRESSION,
        required=False,
        help="The compression factor for PNG (default: {})".format(DEF_PNG_COMPRESSION),
    )
    parser.add_argument(
        "--png-no-interlace",
        dest="png_interlace",
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
        dest="webp_lossless",
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
        dest="avif_lossless",
        action="store",
        default=DEF_AVIF_LOSSLESS,
        help="Force lossless-mode for AVIF compression",
    )

    return parser.parse_args()


def _compress_jpg(
    img,
    dest,
    required_ssim=None,
    compression_factor=DEF_JPEG_COMPRESSION,
    interlace=DEF_JPEG_INTERLACE,
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
    required_ssim : float
        The required value of (mean) structural similarity between the original
        (input, see ``img``) and the compressed version. Given in the range of
        [0, 1], recommended values are ``>0.97``. Default value is ``None``,
        skipping automatic calculation of compression factor.

        If specified, the ``compression_factor`` is used as the starting point
        of the automatic calculation and should be specified **lower** than the
        expected required compression factor and certainly lower than the
        default value of ``75``.
    compression_factor : int
        The JPEG compression factor (0-100; default: 75).
    interlace : bool
        Flag controlling the generation of progressive JPEGs (default: True).
    """
    logger.debug("_compress_jpg()")
    logger.debug("img: %r", img)
    logger.debug("dest: %s", dest)
    logger.debug("required_ssim: %r", required_ssim)
    logger.debug("compression_factor: %d", compression_factor)
    logger.debug("interlace: %r", interlace)

    if required_ssim is not None:
        original = img.numpy()
        mssim = 0
        candidate = ""

        while mssim <= required_ssim:
            # TODO: Put some more logic into the calculation of the *next*
            #       compression_factor, e.g. make it dependent on the value
            #       of ``mssim`` below and jump +5 or +10, depending on the
            #       deviation.
            compression_factor += 1

            # This might seem complex, but is only chaining different operations:
            #   1) use ``jpegsave_buffer`` to apply JPEG compression
            #   2) create a new ``Image`` from that buffer
            #   3) call ``numpy()`` on that image
            candidate = pyvips.Image.new_from_buffer(
                img.jpegsave_buffer(
                    Q=compression_factor,
                    profile="none",
                    optimize_coding=True,
                    interlace=interlace,
                    strip=True,
                    trellis_quant=True,
                    overshoot_deringing=True,
                    optimize_scans=True,
                    quant_table=3,
                ),
                "",
            ).numpy()

            # calculate the structural similarity
            mssim = ssim(original, candidate, win_size=3)

            logger.debug(
                "Checking compression %d: mssim: %f", compression_factor, mssim
            )

    logger.debug("Compressing JPEG with Q = %d", compression_factor)

    # at this point, the compression_factor is as high as possible, write the
    # file to disk!
    img.jpegsave(
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

    return dest


def _compress_png(
    img, dest, compression_factor=DEF_PNG_COMPRESSION, interlace=DEF_PNG_INTERLACE
):
    """Apply PNG compression and save the file to disk.

    This function exposes some PNG compression settings, but other options are
    pre-defined and set aiming for minimal file sizes, at the cost of
    computation time.

    The function does not implement any automatic calculation of the
    compression factor, as PNG is a lossless format. To generate the smallest
    possible PNG output, set ``compression_factor`` to its maximum.

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

    logger.debug("Compressing PNG with Q = %d", compression_factor)

    img.pngsave(
        dest,
        compression=compression_factor,
        interlace=interlace,
        profile="none",
        palette=False,
    )

    return dest


def _compress_webp(
    img,
    dest,
    required_ssim=None,
    compression_factor=DEF_WEBP_COMPRESSION,
    lossless=DEF_WEBP_LOSSLESS,
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
    required_ssim : float
        The required value of (mean) structural similarity between the original
        (input, see ``img``) and the compressed version. Given in the range of
        [0, 1], recommended values are ``>0.97``. Default value is ``None``,
        skipping automatic calculation of compression factor.

        If specified, the ``compression_factor`` is used as the starting point
        of the automatic calculation and should be specified **lower** than the
        expected required compression factor and certainly lower than the
        default value of ``75``.
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
    logger.debug("required_ssim: %r", required_ssim)
    logger.debug("compression_factor: %d", compression_factor)
    logger.debug("lossless: %r", lossless)

    if lossless is None:
        if img.get("vips-loader") == "jpegload":
            lossless = False
            logger.debug(
                "Detected lossy input file, automatically switching to lossy output!"
            )
        else:
            lossless = True
            logger.debug(
                "Detected lossless input file, automatically switching to lossless output!"
            )

    if required_ssim is not None:
        original = img.numpy()
        mssim = 0
        candidate = ""

        while mssim <= required_ssim:
            # TODO: Put some more logic into the calculation of the *next*
            #       compression_factor, e.g. make it dependent on the value
            #       of ``mssim`` below and jump +5 or +10, depending on the
            #       deviation.
            compression_factor += 1

            # This might seem complex, but is only chaining different operations:
            #   1) use ``webpsave_buffer`` to apply WebP compression
            #   2) create a new ``Image`` from that buffer
            #   3) call ``numpy()`` on that image
            candidate = pyvips.Image.new_from_buffer(
                img.webpsave_buffer(
                    Q=compression_factor,
                    lossless=lossless,
                    effort=6,
                    strip=True,
                    profile="none",
                ),
                "",
            ).numpy()

            # calculate the structural similarity
            mssim = ssim(original, candidate, win_size=3)

            logger.debug(
                "Checking compression %d: mssim: %f", compression_factor, mssim
            )

    logger.debug("Compressing WebP with Q = %d", compression_factor)

    # at this point, the compression_factor is as high as possible, write the
    # file to disk!
    img.webpsave(
        dest,
        Q=compression_factor,
        lossless=lossless,
        effort=6,
        strip=True,
        profile="none",
    )

    return dest


def _compress_avif(
    img,
    dest,
    required_ssim=None,
    compression_factor=DEF_AVIF_COMPRESSION,
    lossless=DEF_AVIF_LOSSLESS,
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
    required_ssim : float
        The required value of (mean) structural similarity between the original
        (input, see ``img``) and the compressed version. Given in the range of
        [0, 1], recommended values are ``>0.97``. Default value is ``None``,
        skipping automatic calculation of compression factor.

        If specified, the ``compression_factor`` is used as the starting point
        of the automatic calculation and should be specified **lower** than the
        expected required compression factor and certainly lower than the
        default value of ``50``.
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
    logger.debug("required_ssim: %r", required_ssim)
    logger.debug("compression_factor: %d", compression_factor)
    logger.debug("lossless: %r", lossless)

    if lossless is None:
        if img.get("vips-loader") == "jpegload":
            lossless = False
            logger.debug(
                "Detected lossy input file, automatically switching to lossy output!"
            )
        else:
            lossless = True
            logger.debug(
                "Detected lossless input file, automatically switching to lossless output!"
            )

    if required_ssim is not None:
        original = img.numpy()
        mssim = 0
        candidate = ""

        while mssim <= required_ssim:
            # TODO: Put some more logic into the calculation of the *next*
            #       compression_factor, e.g. make it dependent on the value
            #       of ``mssim`` below and jump +5 or +10, depending on the
            #       deviation.
            compression_factor += 1

            # This might seem complex, but is only chaining different operations:
            #   1) use ``heifsave_buffer`` to apply AVIF compression
            #   2) create a new ``Image`` from that buffer
            #   3) call ``numpy()`` on that image
            candidate = pyvips.Image.new_from_buffer(
                img.heifsave_buffer(
                    Q=compression_factor,
                    lossless=lossless,
                    effort=9,
                ),
                "",
            ).numpy()

            # calculate the structural similarity
            mssim = ssim(original, candidate, win_size=3)

            logger.debug(
                "Checking compression %d: mssim: %f", compression_factor, mssim
            )

    logger.debug("Compressing AVIF with Q = %d", compression_factor)

    # at this point, the compression_factor is as high as possible, write the
    # file to disk!
    img.heifsave(
        dest,
        Q=compression_factor,
        lossless=lossless,
        effort=9,
    )

    return dest


def _compress(
    img,
    target_format,
    args,
    override_stem=None,
):
    """Apply compression to an image.

    This function is the common interface to all specific compression
    functions. It evaluates the ``args`` parameters and applies the required
    ones to the speicifc compression functions.

    Parameters
    ----------
    img :
        The image to be compressed, provided as ``libvips`` Image object.
    target_format : str
        The desired output format.
    args : dict
        The argument dictionary, as provided by Python's ``argparse``.
    override_stem : str, None
        Override the *stem* of the output filename.
    """
    logger.debug("_compress()")
    logger.debug("img: %r", img)
    logger.debug("target_format: %s", target_format)
    logger.debug("args: %r", args)

    if override_stem is None:
        dest = Path(args.destination, Path(img.filename).stem).with_suffix(
            ".{}".format(target_format.lower())
        )
    else:
        dest = Path(args.destination, override_stem).with_suffix(
            ".{}".format(target_format.lower())
        )
    logger.debug("dest: %s", dest)

    if target_format == TFORMAT_JPG:
        return _compress_jpg(
            img,
            dest,
            required_ssim=args.required_ssim,
            compression_factor=args.jpeg_compression,
            interlace=args.jpeg_interlace,
        )
    elif target_format == TFORMAT_PNG:
        return _compress_png(
            img,
            dest,
            compression_factor=args.png_compression,
            interlace=args.png_interlace,
        )
    elif target_format == TFORMAT_WEBP:
        return _compress_webp(
            img,
            dest,
            required_ssim=args.required_ssim,
            compression_factor=args.webp_compression,
            lossless=args.webp_lossless,
        )
    elif target_format == TFORMAT_AVIF:
        return _compress_avif(
            img,
            dest,
            required_ssim=args.required_ssim,
            compression_factor=args.avif_compression,
            lossless=args.avif_lossless,
        )
    else:
        # Is real error handling required here?
        #
        # The argument parser should already ensure, that only *known* and
        # *accepted* target formats are provided. So, this point should
        # actually never be reached.
        logger.error("Unknown target format!")


def _resize(img, target_width):
    """Resize an image to a ``target_width``.

    Parameters
    ----------
    img :
        The image to be resized, provided as ``libvips`` Image object.
    target_width : int
        The desired width of the resized image.
    """
    logger.debug("_resize()")
    logger.debug("img: %r", img)
    logger.debug("target_width: %d", target_width)

    target_height = math.floor(img.height / (img.width / target_width))
    logger.info("Generating resized image (%d/%d)", target_width, target_height)

    return img.thumbnail_image(
        target_width,
        height=target_height,
        size="down",
        no_rotate=True,
        crop=True,
        linear=True,
    )


def cmd_compress(args):
    """Provide the compression mode of operation.

    The compression and disk I/O is implemented by ``_compress()`` and its
    related compression functions. This function just picks up the source file
    and then calls the actual payload.

    The specific arguments controlling the compression are passed through and
    are evaluated in ``_compress()``.

    Parameters
    ----------
    args : dict
        The argument dictionary, as provided by Python's ``argparse``.
    """
    logger.debug("cmd_compress()")

    # open the source for/with ``libvips``
    img = pyvips.Image.new_from_file(args.source)
    output = []

    logger.info(
        "Compressing %s into the following formats: %r", args.source, args.formats
    )

    for tformat in args.formats:
        output.append(_compress(img, tformat, args))

    return output


def cmd_responsive(args):
    """Provide the responsive mode of operation.

    This generates smaller versions of the *source* image, intended to be used
    with HTML ``srcset`` in ``<img>`` and ``<picture>`` elements.

    The resized images are automatically processed by the ``_compress()``
    function, which takes care of disk I/O.

    Parameters
    ----------
    args : dict
        The argument dictionary, as provided by Python's ``argparse``.
    """
    logger.debug("cmd_responsive()")

    # open the source for/with ``libvips``
    img = pyvips.Image.new_from_file(args.source)
    stem = Path(img.filename).stem
    output = []

    logger.info('Source file "%s" (%d x %d)', args.source, img.width, img.height)

    for tsize in args.sizes:
        logger.debug("tsize: %r", tsize)
        resized = _resize(img, int(tsize[1]))

        logger.debug("Resized: %r", resized)

        override_stem = "{}-{}".format(stem, tsize[0])

        for tformat in args.formats:
            output.append(
                _compress(resized, tformat, args, override_stem=override_stem)
            )

    return output


def main():
    """Execute the processing."""
    # get the arguments
    args = parse_args()

    logger.debug("args: %r", args)

    if args.command == "compress":
        output = cmd_compress(args)
    elif args.command == "responsive":
        output = cmd_responsive(args)

    print("The following files were generated:")
    for f in output:
        print("- {}".format(f))


if __name__ == "__main__":
    # setup the logging module
    logging.config.dictConfig(LOGGING_DEFAULT_CONFIG)

    main()
