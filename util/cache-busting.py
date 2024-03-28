#!/usr/bin/env python3

"""Custom script to perform cache busting for static assets.

This script accepts a list of assets that require cache busting (parameter
``--asset``) and a source directory (``--source``). It will then hash the
assets' file contents, inject the hash into the filenames and then substitute
the original filename for all matching files in the source directory.
"""

# Python imports
import argparse
import hashlib
import logging
import logging.config
import re
from pathlib import Path

# get a module-level logger
logger = logging.getLogger(__name__)

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
        __name__: {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": True,
        },
    },
}


def sha256sum(filename):
    """Determine a hash of a file's content.

    The implementation should be quite memory-efficient and is directly fetched from
    https://stackoverflow.com/a/44873382 (please note: This is the implementation with
    compatibility to Python 3.8 (and above)).
    """
    h = hashlib.sha256()
    b = bytearray(128 * 1024)
    mv = memoryview(b)
    with open(filename, "rb", buffering=0) as f:
        while n := f.readinto(mv):
            h.update(mv[:n])
    return h.hexdigest()


class InvalidArgumentError(Exception):
    """Indicate invalid arguments."""


class BusterAsset:
    """A single asset that requires hashing/renaming.

    Parameters
    ----------
    rel_path : pathlib.Path
        The path to the asset as specified by the command line argument. This
        will be used as search pattern/needle for the substitution and to
        construct the substitute.
    source_dir : pathlib.Path
        The path to the source directory.
    """

    def __init__(self, rel_path, source_dir):
        self.original_rel_path = rel_path
        self.source_dir = source_dir

        self.original_source_path = source_dir.joinpath(rel_path)

    def process(self):
        """Process the asset file.

        1) Determine the hash of the file's content.
        2) Inject the hash into the filename.
        """
        self.file_hash = sha256sum(self.original_source_path)
        logger.debug("hash: %s (%s)", self.file_hash, self.original_rel_path)

        # FIXME: Make the length of the hash configurable!
        self.rel_path = Path(self.original_rel_path.parent).joinpath(
            Path(
                "{}-{}{}".format(
                    self.original_rel_path.stem,
                    self.file_hash[:10],
                    self.original_rel_path.suffix,
                )
            )
        )
        logger.debug("rel_path: %s (%s)", self.rel_path, self.original_rel_path)

        self.source_path = self.original_source_path.rename(
            self.source_dir.joinpath(self.rel_path)
        )
        logger.debug("source_path: %s (%s)", self.source_path, self.original_rel_path)

    def __str__(self):  # noqa D105
        return "{} ({})".format(self.original_rel_path, self.original_source_path)

    def __repr__(self):  # noqa D105
        return "BusterAsset(rel_path={})".format(self.original_rel_path)


def parse_args():
    """Parse the command line arguments."""
    # create the main parser
    parser = argparse.ArgumentParser(
        description="Perform cache busting for static assets"
    )

    parser.add_argument(
        "--source",
        action="store",
        type=str,
        required=True,
        help="Path to the source directory",
    )

    parser.add_argument(
        "--asset",
        dest="assets",
        action="append",
        type=str,
        required=True,
        help="Relative path from source directory to an asset file",
    )

    return parser.parse_args()


def buster(source_dir, asset_paths, pattern="**/*.html"):
    """Perform the cache busting.

    Cache Busting is performed in two steps:
    1) Processing assets by hashing their content and injecting the hash into
       their filename.
    2) Processing all files in ``source_dir`` as specified by ``pattern`` and
       replace references to assets with the (new) filename from step 1.

    Parameters
    ----------
    source_dir : pathlib.Path
    asset_paths : { pathlib.Path }
    pattern : str
        The pattern is used in a call to ``Path.glob()`` to find the source
        files that need processing. Default: ``"**/*.html"``.
    """
    if not source_dir.is_dir():
        raise InvalidArgumentError("'source' must be a directory")

    # determine the source files
    source_files = {f for f in source_dir.glob(pattern) if f.is_file()}
    logger.info(
        "Found %d files matching the pattern '%s' in source directory '%s'",
        len(source_files),
        pattern,
        source_dir,
    )
    logger.debug("source files: %r", source_files)

    # Step 1: Process the assets
    assets = []

    # build a list of assets
    for rel_path in asset_paths:
        source_path = source_dir.joinpath(rel_path)

        # assets **must not** be included in ``source_files``
        if source_path in source_files:
            logger.error("Asset '%s' is included in source files", rel_path)
            raise InvalidArgumentError("Assets must not be included in source files")

        assets.append(BusterAsset(rel_path, source_dir))

    # process the assets and prepare substitution in the source files
    substitutes = {}
    for a in assets:
        a.process()

        # add the asset to the dictionary of substitutes
        substitutes[str(a.original_rel_path)] = str(a.rel_path)

    # Step 2: Apply new asset paths to the source files

    # prepare the substitutions regular expression
    logger.debug("substitutes: %r", substitutes)
    subst_regex = re.compile("(%s)" % "|".join(map(re.escape, substitutes.keys())))

    # process the source files
    for f in source_files:
        logger.debug("processing '%s'", f)
        buf, n = subst_regex.subn(lambda mo: substitutes[mo.group(1)], f.read_text())
        f.write_text(buf)
        logger.info("Processed '%s', %d substitutions", f, n)


def main():
    """Perform the cache busting when executing the script from command line."""
    args = parse_args()
    logger.debug("args: %r", args)

    source = Path(args.source)
    logger.debug("source: %r", source)

    assets = {Path(a) for a in args.assets}
    logger.debug("assets: %r", assets)

    return buster(source, assets)


if __name__ == "__main__":
    # setup the logging module
    logging.config.dictConfig(LOGGING_DEFAULT_CONFIG)

    main()
