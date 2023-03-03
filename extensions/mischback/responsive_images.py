"""Provide *responsive images* for HTML-based output."""


# Python imports
import logging
import logging.config
from functools import total_ordering
from pathlib import Path

# Sphinx imports
from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.environment.collectors import EnvironmentCollector
from sphinx.util import FilenameUniqDict
from sphinx.util.i18n import search_image_for_language

# external imports
# ``imagesize`` is as of now a Sphinx dependency already and *should* be
# available.
import imagesize
from docutils import nodes

EXTENSION_LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "console_output": {
            "format": "[%(levelname)s] [%(name)s:%(lineno)d] %(message)s",
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

# FIXME: Development only! The desired setup integrates into Sphinx's logging
#        system!
#        ``from sphinx.util import logging`` and remove the configuration of
#        ``logging`` here!
logging.config.dictConfig(EXTENSION_LOGGING)

# get a module-level logger
logger = logging.getLogger(__name__)


# Map filename extensions to mime types.
EXT_TO_MIME = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".avif": "image/avif",
}


def _get_sorted_format_list(format_list, reverse=False):
    """Apply sorting to the list of image formats.

    This function is meant to be used with the extension's configuration value
    ``responsive_images_formats``. It applies the sorting and returns a list
    of formats, given as :py:`str`.
    """
    tmp = format_list
    tmp.sort(key=lambda tup: tup[1], reverse=reverse)

    return [f[0] for f in tmp]


def _get_image_size(filename):
    """Return the image's width and height.

    This wraps around ``imagesize`` to make its interface usable by the
    extension's code.

    There is a similar implementation in Sphinx's codebase. This function
    removes all exception handling, as exceptions are handled in the
    directive's ``_get_all_candidates()``.

    Parameters
    ----------
    filename : str or Path
        The filename including the path relative to Sphinx's working directory.

    Returns
    -------
    tuple, None
    """
    size = imagesize.get(filename)

    if size[0] == -1:
        return None
    elif isinstance(size[0], float) or isinstance(size[1], float):
        return (int(size[0]), int(size[1]))

    return size


@total_ordering
class ResponsiveImageSourceFile:
    """Represent a single image source file.

    When an image source file is represented as an instance of this class, it
    it ensured that
    a) the file is available and readable
    b) required meta information is available, including the image's dimensions
       and its filetype/MIME type

    Parameters
    ----------
    src_path : :class:`Path`
        The filename, including it's path (relative to Sphinx's root directory).
    file_width: int, None
    file_height: int, None

    Attributes
    ----------
    src_path : Path
        The actual path (relative to Sphinx's working directory) to the image
        file.

        Note: This is **not** the final path for Sphinx's output/build process.
    width: int
        The actual width of the image source file, provided in **px** (but
        without the actual unit).
    height: int
        The actual height of the image source file, provided in **px** (but
        without the actual unit).
    mime: str
        The MIME type of the image source file, derived from its extension.
    """

    class ProcessingError(RuntimeError):
        """Indicate problems during processing."""

    def __init__(self, src_path, file_width=None, file_height=None):
        file_dim = _get_image_size(src_path)

        if file_dim is None:
            if (file_width is None) or (file_height is None):
                raise self.ProcessingError("Could not determine image dimensions")
            else:
                file_dim = (file_width, file_height)

        self.src_path = src_path
        self.width = file_dim[0]
        self.height = file_dim[1]
        self.mime = EXT_TO_MIME[src_path.suffix]

    def __eq__(self, other):
        """Check equality with ``other`` object."""
        # see https://stackoverflow.com/a/2909119
        # see https://stackoverflow.com/a/8796908
        if isinstance(other, ResponsiveImageSourceFile):
            return self.__key() == other.__key()
        return NotImplemented

    def __hash__(self):
        """Provide a unique representation of the instance."""
        # see https://stackoverflow.com/a/2909119
        return hash(self.__key())

    def __lt__(self, other):
        """Check equality with ``other`` object."""
        # see https://stackoverflow.com/a/8796908
        if isinstance(other, ResponsiveImageSourceFile):
            return self.__key() < other.__key()
        return NotImplemented

    def __repr__(self):
        """Provide an instance's ``representation``."""
        # see https://stackoverflow.com/a/12448200
        return "<ResponsiveImageSourceFile(src_path={}, file_width={}, file_height={})>".format(
            self.src_path.__repr__(), self.width.__repr__(), self.height.__repr__()
        )

    def __key(self):
        """Provide internal representation of the instance."""
        # see https://stackoverflow.com/a/2909119
        return (self.src_path, self.width, self.height, self.mime)


class ResponsiveImageSources:  # noqa D101
    def __init__(self):
        self._sources = set()

    def add(self, new_source):
        """Add a new source file."""
        if isinstance(new_source, ResponsiveImageSourceFile):
            return self._sources.add(new_source)
        return NotImplemented


class ResponsiveImageCollector(EnvironmentCollector):  # noqa D101
    def clear_doc(self, app, env, docname):  # noqa D102
        env.responsive_images.purge_doc(docname)

    def merge_other(self, app, env, docnames, other):  # noqa D102
        env.responsive_images.merge_other(docnames, other.responsive_images)

    def process_doc(self, app, doctree):  # noqa D102
        docname = app.env.docname
        formats = _get_sorted_format_list(
            app.config.responsive_images_formats, reverse=True
        )

        for node in doctree.findall(nodes.image):
            logger.debug("Processing node [%s] in [%s]", node, docname)

            # We can't determine, if we're running before or after the built-in
            # ``ImageCollector``, which modifies the node while processing it.
            # We replicate its behaviour, but don't modify the existing
            # attributes of the node. Hopefully this does not interfere with
            # Sphinx's existing codebase.
            imguri = search_image_for_language(node["uri"], app.env)
            logger.debug("imguri: %r", imguri)

            img_src_path, _ = app.env.relfn2path(imguri, docname)
            logger.debug("img_src_path: %r", img_src_path)

            self.collect_sources(
                img_src_path, app.config.responsive_images_size_suffixes, formats
            )

    def collect_sources(self, ref_path, size_suffixes, formats):
        """Determine the responsive versions of the image.

        Parameters
        ----------
        ref_path : str
            The source file, as referenced in the directive, provided as plain
            :py:`str`. This will be processed to generate the *responsive
            filenames*.
        size_suffixes : list(str)
            A list of suffixes to identify different sizes.
        formats : list(str)
            A list of formats (file extensions).
        """
        self.sources = ResponsiveImageSources()

        ref_path = Path(ref_path)
        logger.debug("ref_path: %r", ref_path)
        logger.debug("stem: %r", ref_path.stem)
        logger.debug("parent: %r", ref_path.parent)

        for s in size_suffixes:
            for f in formats:
                logger.debug("%r, %r", s, f)


def integrate_into_build_process(app):
    """Integrate the extension into Sphinx's build process.

    The extension is developed with HTML output in mind, providing the required
    markup for *responsive images*. It has no purpose for other output formats,
    so the setup of the extension is done here, as this function is executed
    when the builder has been determined.

    This function is meant to be attached to Sphinx's ``builder-inited`` event.
    See :func:`setup`.
    """
    # Only intgegrate the extension if this is an HTML build
    logger.debug("Detecting builder: %r", app.builder)
    if not isinstance(app.builder, StandaloneHTMLBuilder):
        logger.info("Detected a non-HTML builder. Skipping extension setup!")
        return

    # Setup the specific ``EnvironmentCollector`` for the responsive image sources
    if not hasattr(app.env, "responsive_images"):
        app.env.responsive_images = FilenameUniqDict()
    app.add_env_collector(ResponsiveImageCollector)


def setup(app):
    """Register the extension with Sphinx.

    This function is required by Sphinx's extension interface, see
    https://www.sphinx-doc.org/en/master/development/tutorials/helloworld.html#writing-the-extension
    for reference.
    """
    # This configuration value maps image formats to their corresponding output
    # priorities (lower priority value = higher logical priority).
    #
    # The items in the list are of type ``tuple``, where the first element is
    # the target format, specified **including** a leading full stop (``.``).
    # The second item is the corresponding **output priority**.
    #
    # Note: The **output priority** also controls the order of processing the
    #       source files. While *lower* priority values mean a higher logical
    #       output priority, *higher* priority values lead to earlier
    #       processing for candidates.
    app.add_config_value(
        "responsive_images_formats",
        [
            (".avif", 1),
            (".webp", 2),
            (".jpg", 99),
            (".png", 98),
        ],
        "env",
    )

    # This configuration value provides a list of filename suffixes to indicate
    # the image dimensions.
    #
    # It is recommended to provide a *semantic name*. The values are appended
    # to the *stem* of the given source filename to construct the filenames of
    # the responsive variants with different sizes.
    app.add_config_value(
        "responsive_images_size_suffixes",
        ["-tiny", "-small", "-medium", "-big", "-large", "-xlarge"],
        "env",
    )

    # When the builder is set up, we can determine if we're running an HTML
    # build. Only in this case, all other magic of this extension needs to be
    # applied.
    app.connect("builder-inited", integrate_into_build_process)

    return {
        "version": "0.0.1",
        "env-version": "1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
