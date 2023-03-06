"""Provide *responsive images* for HTML-based output."""


# Python imports
import logging
import logging.config
from functools import total_ordering
from pathlib import Path

# Sphinx imports
from sphinx.builders import Builder
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
    img_path : Path
        The actual path (relative to Sphinx's source directory) to the image
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

    def __init__(self, img_path, srcdir, file_width=None, file_height=None):
        file_dim = _get_image_size(Path(srcdir, img_path))

        if file_dim is None:
            if (file_width is None) or (file_height is None):
                raise self.ProcessingError("Could not determine image dimensions")
            else:
                file_dim = (file_width, file_height)

        self.img_path = img_path
        self.width = file_dim[0]
        self.height = file_dim[1]
        self.mime = EXT_TO_MIME[img_path.suffix]

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
        return "<ResponsiveImageSourceFile(img_path={}, file_width={}, file_height={})>".format(
            self.img_path.__repr__(), self.width.__repr__(), self.height.__repr__()
        )

    def __key(self):
        """Provide internal representation of the instance."""
        # see https://stackoverflow.com/a/2909119
        return (self.img_path, self.width, self.height, self.mime)


class ResponsiveImageSources:  # noqa D101
    def __init__(self):
        self._sources = set()

    def __len__(self):
        """Get the number of sources."""
        # see https://stackoverflow.com/a/15114062
        return len(self._sources)

    def add(self, new_source):
        """Add a new source file."""
        if isinstance(new_source, ResponsiveImageSourceFile):
            return self._sources.add(new_source)
        return NotImplemented

    def get_by_img_path(self, img_path):
        """Return an ``ResponsiveImageSourceFile`` by its path."""
        # see https://stackoverflow.com/a/22693614
        #
        # The list comprehension *should* return just a single element, which
        # is returned with ``next(iter(...))``. If the comprehension is empty,
        # ``None`` is returned.
        return next(
            iter({item for item in self._sources if item.img_path == img_path}), None
        )

    def get_fallback(self, fileformat):  # noqa D102
        return self.get_source_files(fileformat=fileformat)[0]

    def get_img_path_list(self):
        """Return the paths of all source files as list."""
        return {item.img_path for item in self._sources}

    def get_source_files(self, fileformat=None, min_width=0):  # noqa: D102
        if fileformat is None:
            source_files = list(
                {item for item in self._sources if (item.width >= min_width)}
            )
        else:
            source_files = list(
                {
                    item
                    for item in self._sources
                    if (
                        item.width >= min_width and item.mime == EXT_TO_MIME[fileformat]
                    )
                }
            )

        source_files.sort(key=lambda src: src.width)

        return source_files


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
            # logger.debug("Processing node [%s] in [%s]", node, docname)

            # We can't determine, if we're running before or after the built-in
            # ``ImageCollector``, which modifies the node while processing it.
            # We replicate its behaviour, but don't modify the existing
            # attributes of the node. Hopefully this does not interfere with
            # Sphinx's existing codebase.
            imguri = search_image_for_language(node["uri"], app.env)

            img_path, _ = app.env.relfn2path(imguri, docname)

            # Determine the available *responsive* versions of the image
            self.collect_sources(
                img_path,
                app.config.responsive_images_size_suffixes,
                formats,
                app.srcdir,
            )

            # Add the *responsive sources* to the document's dependencies and
            # track them in the build environment.
            for src_path in self.sources.get_img_path_list():
                app.env.dependencies[docname].add(str(src_path))
                app.env.responsive_images.add_file(docname, str(src_path))

            # Add the *responsive sources* to the actual node
            node["responsive_sources"] = self.sources

    def collect_sources(self, ref_path, size_suffixes, formats, app_srcdir):
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
        app_srcdir : str
            Full path to Sphinx's source directory.
        """
        self.sources = ResponsiveImageSources()

        ref_path = Path(ref_path)

        for s in size_suffixes:
            new_stem = "{}{}".format(ref_path.stem, s)
            for f in formats:
                work_path = ref_path.with_stem(new_stem).with_suffix(f)

                try:
                    self.sources.add(ResponsiveImageSourceFile(work_path, app_srcdir))
                except ResponsiveImageSourceFile.ProcessingError:
                    # Could not determine image's dimensions.
                    #
                    # Try to recover from an already-processed version of the
                    # corresponding size, most likely JPG or PNG.
                    try:
                        fallback = self.sources.get_by_img_path(
                            ref_path.with_stem(new_stem)
                        )
                        self.sources.add(
                            ResponsiveImageSourceFile(
                                work_path,
                                app_srcdir,
                                file_width=fallback.width,
                                file_height=fallback.height,
                            )
                        )
                    except Exception:
                        # Note: This will raise a warning. When running with
                        #       Sphinx's ``-W`` option, this will fail the
                        #       build!
                        logger.warning(
                            "Could not determine dimensions for %s - skipping!"
                        )
                except FileNotFoundError:
                    # logger.debug("File not found: %s - skipping!", work_path)
                    continue


def visit_image(self, node, original_visit_image):  # noqa D103
    logger.debug("%s", node)

    sources = node.get("responsive_sources", [])

    # The ``ResponsiveImageCollector`` did not find responsive versions of the
    # image, so we just use the original implementation of ``visit_image()``.
    if len(sources) < 1:
        logger.debug("No responsive_sources, falling back to original visit_node()")
        return original_visit_image(self, node)

    # Start the <picture> element
    self.body.append("<picture>")

    # Create the actual <img> element
    # FIXME: Instead of creating this manually, we could rely on the original
    #        implementation.
    #        This does require, that the relevant information is provided in
    #        the right attributes.
    # TODO: How and when to determine the target path of the image?!
    fallback = sources.get_fallback(Path(node["uri"]).suffix)
    alt_text = node.get("alt", "")
    self.body.append(
        '<img src="{img_src}" alt="{alt_text}" width="{img_width}" height="{img_height}">'.format(
            img_src=fallback.img_path,
            img_width=fallback.width,
            img_height=fallback.height,
            alt_text=alt_text,
        )
    )

    # Close the <picture> element
    self.body.append("</picture>")


def post_process_images(self, doctree, original_post_process_images):  # noqa D103
    # logger.debug("custom post_process_images()")

    # call the original function first!
    original_post_process_images(doctree)

    for node in doctree.findall(nodes.image):
        sources = node.get("responsive_sources", [])

        if len(sources) < 1:
            logger.debug("nodes.image without responsive sources - skipping!")
            continue

        logger.debug("nodes.image **with** responsive sources: %r", sources)
        # logger.debug(self.env.responsive_images)
        # logger.debug(self.env.images)

        for s in sources._sources:
            logger.debug("source: %r", s)


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
    if not isinstance(app.builder, StandaloneHTMLBuilder):
        logger.info("Detected a non-HTML builder. Skipping extension setup!")
        return

    # Setup the specific ``EnvironmentCollector`` for the responsive image sources
    if not hasattr(app.env, "responsive_images"):
        app.env.responsive_images = FilenameUniqDict()
    app.add_env_collector(ResponsiveImageCollector)

    # Replace the original ``visit_image()`` with a custom wrapper
    #
    # This code is based on the implementation in ``sphinxext-photofinish``.
    translator_class = app.builder.get_translator_class()
    original_visit_image = translator_class.visit_image

    def visit_image_replacement(translator, node):
        visit_image(translator, node, original_visit_image)

    translator_class.visit_image = visit_image_replacement

    # Replace the original ``post_process_images()`` with a custom wrapper
    original_post_process_images = app.builder.post_process_images

    def post_process_images_replacement(builder, doctree):
        post_process_images(builder, doctree, original_post_process_images)

    app.builder.post_process_images = post_process_images_replacement.__get__(
        app.builder, Builder
    )


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
