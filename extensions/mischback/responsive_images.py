"""Provide the required HTML markup for *responsive images*.

This is a custom extension, exclusively developed for my very own website. It
makes certain assumptions about the project's structure. You may freely use it
at your own risk!

The extension hooks deeply into Sphinx's build process, monkey patching some
of Sphinx's and docutils' internal functions. It *should work* out of the box,
as the extension calls the original versions of the functions alongside its
own processing logic. But there *may be* side effects.

The extension is integrated into Sphinx's logging system.

The extension only provides the required HTML markup for responsive images,
supporting different sizes aswell as different file formats. The idea is to
serve highly optimized image files, which are as small as possible, depending
on the displayed size of the image aswell using the best compressing method
(depending on browser compatibility). However, the extension **does not
generate** the required image source files! There is a companion utility script
(``util/process_image.py``) which may be used to generate the desired image
versions, applying resizing and compression.

The generated markup is **not suitable** for *art direction* using the
``<picture>`` element, because the generated markup will add all available
sources (of a given file format), which have bigger dimensions, as alternatives
to the ``<source>`` elements (this *should* cover higher pixel density
displays).
"""


# Python imports
import logging
import logging.config
import urllib.parse
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
    ``responsive_images_formats``. It applies the priority and returns a list
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
    img_path : :class:`Path`
        The filename, including it's path (relative to Sphinx's source
        directory).
    src_dir : str
        The path to Sphinx's source directory.
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


class ResponsiveImageSources:
    """A set of responsive image sources.

    The class is meant to manage the available responsive image sources,
    represented as :class:`ResponsiveImageSourceFile` instances **per node**.

    It wraps around Python's ``set`` and provides several functions to access
    and filter the sources.
    """

    def __init__(self):
        self._sources = set()

    def __len__(self):
        """Get the number of sources."""
        # see https://stackoverflow.com/a/15114062
        return len(self._sources)

    def add(self, new_source):
        """Add a new source file.

        new_source : ResponsiveImageSourceFile
        """
        if isinstance(new_source, ResponsiveImageSourceFile):
            return self._sources.add(new_source)
        return NotImplemented

    def get_by_img_path(self, img_path):
        """Return an ``ResponsiveImageSourceFile`` by its path.

        Parameters
        ----------
        img_path : Path

        Returns
        -------
        ResponsiveImageSourceFile
        """
        # see https://stackoverflow.com/a/22693614
        #
        # The list comprehension *should* return just a single element, which
        # is returned with ``next(iter(...))``. If the comprehension is empty,
        # ``None`` is returned.
        return next(
            iter({item for item in self._sources if item.img_path == img_path}), None
        )

    def get_fallback(self, fileformat):
        """Get the *smallest* image source of the given *fileformat*.

        Parameters
        ----------
        fileformat : str

        Returns
        -------
        ResponsiveImageSourceFile
        """
        return self.get_source_files(fileformat=fileformat)[0]

    def get_img_path_list(self):
        """Get a flat list of the sources' paths.

        Returns
        -------
        list(str)
        """
        return {item.img_path for item in self._sources}

    def get_source_files(self, fileformat=None, min_width=0):
        """Get all images sources, ordered by width.

        The result might be filtered by *fileformat* and/or a *minimum width*.

        Parameters
        ----------
        fileformat : str, None
        min_width : int
        """
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


class ResponsiveImageCollector(EnvironmentCollector):
    """An extension-specific implementation of Sphinx's EnvironmentCollector.

    This class is basically a re-implementation of
    ``sphinx.environment.collectors.asset.ImageCollector`` to take care of the
    responsive versions of images. It iterates all ``image`` nodes of a given
    document, determines the (available) responsive image versions, keeps track
    of them in the build environment and adds them as dependencies of the
    document.

    The ``responsive_images`` attribute and this class are added to the build
    environment in ``integrate_into_build_process()``.

    ``EnvironmentCollector`` instances are run during the build after the
    source file has been parsed into a ``doctree``. ``process_doc()`` is then
    called for every document (Sphinx's core event ``doctree-read`` is used
    to run the method).
    """

    def clear_doc(self, app, env, docname):
        """Remove a document from ``responsive_images``.

        This method is required to enable parallel builds.
        """
        env.responsive_images.purge_doc(docname)

    def merge_other(self, app, env, docnames, other):
        """Merge one ``responsive_images`` with the one from another ``env``.

        This method is required to enable parallel builds.
        """
        env.responsive_images.merge_other(docnames, other.responsive_images)

    def process_doc(self, app, doctree):
        """Process the ``image`` nodes of a document to identify responsive images.

        The real magic is done in ``collect_sources()`` and its result is then
        added to the processed ``node`` instance and to the document's
        dependencies.
        """
        docname = app.env.docname
        formats = _get_sorted_format_list(
            app.config.responsive_images_formats, reverse=True
        )

        for node in doctree.findall(nodes.image):
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

        # Convert the ``str`` to an actual ``Path`` object for processing
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
                    logger.info("File not found: %s - skipping!", work_path)
                    continue


def visit_image(self, node, original_visit_image):
    """Provide the actual HTML markup for responsive images.

    This function handles the generation of the required markup for ``image``
    nodes. It replaces Sphinx's original implementation by monkey patching the
    corresponding function in Sphinx's ``Translator``, see
    ``integrate_into_build_process()``.

    The ``ResponsiveImageCollector`` adds the responsive source files to the
    ``node`` instance. This function generates the corresponding markup and
    automatically adjusts the source paths (to be relative to the generated
    output document).

    If there are no responsive image sources available, the original
    implementation of ``visit_image()`` is called.
    """

    def _get_path(basedir, img_path):
        return str(Path(basedir, urllib.parse.quote(img_path)))

    sources = node.get("responsive_sources", [])

    # The ``ResponsiveImageCollector`` did not find responsive versions of the
    # image, so we just use the original implementation of ``visit_image()``.
    if len(sources) < 1:
        logger.debug("No responsive_sources, falling back to original visit_node()")
        return original_visit_image(self, node)

    # Start the <picture> element
    self.body.append("<picture>")

    # Generate the <source> elements
    #
    # The <source> elements are generated depending on the breakpoints (as
    # specified from the extension's configuration) and the file formats.
    #
    # Note: Generating *mobile first* breakpoints is hardcoded as of now!
    formats = _get_sorted_format_list(self.builder.app.config.responsive_images_formats)
    bpoints = [(0, 0)] + self.builder.app.config.responsive_images_layout_breakpoints
    bpoints.sort(reverse=True)

    for b in bpoints:
        for f in formats:
            gen_source = ["<source", ">"]
            tmp_sources = sources.get_source_files(fileformat=f, min_width=b[1])

            # All further processing is only done, if there are matching source
            # files!
            if len(tmp_sources) > 0:
                gen_source.insert(1, 'type="{}"'.format(tmp_sources[0].mime))
                gen_source.insert(1, 'width="{}"'.format(tmp_sources[0].width))
                gen_source.insert(1, 'height="{}"'.format(tmp_sources[0].height))

                # The media query needs only to be applied if there is an actual
                # min-width!
                if b[0] > 0:
                    gen_source.insert(1, 'media="(min-width: {}px)"'.format(b[0]))

                # Include all matching source files into the ``srcset``.
                #
                # Provide the actual path (relative to the document's location)
                # dynamically.
                tmp_srcset = []
                for s in tmp_sources:
                    tmp_srcset.append(
                        "{img_path} {img_width}w".format(
                            img_path=_get_path(
                                self.builder.imgpath,
                                self.builder.images[str(s.img_path)],
                            ),
                            img_width=s.width,
                        )
                    )

                gen_source.insert(1, 'srcset="{}"'.format(", ".join(tmp_srcset)))

                # Actually append the <source> element
                logger.debug("Generated source: %r", gen_source)
                self.body.append(" ".join(gen_source))

    # Create the actual <img> element
    #
    # One might be tempted to re-use ``original_visit_image()`` here, after
    # setting the node's attributes to matching values. However, this is **not
    # desired**, as ``docutils`` implementation of ``visit_image()`` (for this
    # use case this is
    # ``docutils.writers._html_base.HTMLTranslator.visit_image()``) will apply
    # a ``style`` attribute to the ``<img>`` tag with the image's dimensions,
    # which is **not desired**.
    #
    # TODO: Apply CSS classes!
    # TODO: Apply ``loading`` attributes!
    fallback = sources.get_fallback(Path(node["uri"]).suffix)
    alt_text = node.get("alt", "")
    self.body.append(
        '<img src="{img_src}" alt="{alt_text}" width="{img_width}" height="{img_height}">'.format(
            img_src=_get_path(
                self.builder.imgpath, self.builder.images[str(fallback.img_path)]
            ),
            img_width=fallback.width,
            img_height=fallback.height,
            alt_text=alt_text,
        )
    )

    # Close the <picture> element
    self.body.append("</picture>")


def post_process_images(self, doctree, original_post_process_images):
    """Post-process image nodes and add extension-specific processing.

    This method is a monkey patch around Sphinx's own implementation of
    ``Builder.post_process_images()`` or more specifically
    ``StandaloneHTMLBuilder.post_process_images()``. The monkey patching is
    performed in ``integrate_into_build_process()``.

    This method calls the original method first, to ensure the expected
    behaviour for non-responsive images and then processes the
    extension-specific image sources and adds them to the builder's ``images``
    dictionary, which is used to determine the files that need to be copied
    during the build.

    Parameters
    ----------
    self : sphinx.builders.Builder
    doctree : docutils.nodes.Node
    original_post_process_images : func
        A reference to the original function, as provided by the ``Builder`` or
        more specifically the ``StandaloneHTMLBuilder`` instace.
    """
    # Call the original function first to ensure, that non-responsive images
    # are processed as usual.
    original_post_process_images(doctree)

    # The extension's custom *post processing* replicates the behaviour of the
    # original implementation, but instead of working with the node's ``uri``
    # attribute, the ``responsive_sources`` attribute is processed, which is
    # added to the node in the ``ResponsiveImageCollector.process_doc()``
    # method.
    for node in doctree.findall(nodes.image):
        sources = node.get("responsive_sources", [])

        if len(sources) < 1:
            logger.debug("nodes.image without responsive sources - skipping!")
            continue

        for s in sources._sources:
            # logger.debug("source: %r", s)
            s_img_path = str(s.img_path)
            if s_img_path not in self.env.responsive_images:
                continue
            # This is where the magic happens!
            #
            # The HTML writer will use its ``self.images`` dictionary to
            # determine the files that need to be copied over to the build's
            # image directory.
            self.images[s_img_path] = self.env.responsive_images[s_img_path][1]


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

    As the extension is intended to be used with (siblings of) Sphinx's
    ``StandaloneHTMLBuilder``, most of the actual setup is performed in
    ``integrate_into_build_process()``, which is hooked to Sphinx's
    ``builder-inited`` event. At this point, the ``Builder`` is known and the
    extension performs its setup only, if the builder is an HTML builder.
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
    #       This is done, because the library to "read" image's dimensions
    #       doesn't work with ``avif`` files. But as the avifs are generated
    #       from JPEG or PNG sources, the dimensions may be looked up from the
    #       corresponding JPEG/PNG, if that file was already processed. See the
    #       implementation in ``ResponsiveImageCollector.collect_sources()``.
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
    #
    # All elements of the list are processed and used to generate filenames.
    # If the file is not available, a message of level ``INFO`` is logged.
    app.add_config_value(
        "responsive_images_size_suffixes",
        ["-tiny", "-small", "-medium", "-big", "-large", "-xlarge"],
        "env",
    )

    # This configuration value maps *layout breakpoints* to minimum required
    # *image widths*.
    #
    # During processing, a default *non-breakpoint* ``(0, 0)`` is provided
    # automatically.
    #
    # The items in the list are of type ``tuple``, where the first element is
    # the required minimum display width and the second element a corresponding
    # minimal image width.
    #
    # The first value will be applied in the ``<source>`` element's ``media``
    # attribute as a ``min-width`` in ``px``, the second value is used to
    # filter the available *responsive image sources*.
    #
    # TODO: Provide a sane default value, probably even an empty list.
    app.add_config_value(
        "responsive_images_layout_breakpoints",
        [(777, 444), (500, 222)],
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
