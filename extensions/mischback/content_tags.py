"""Provide a tagging mechanism for Sphinx."""

# Python imports
from collections import defaultdict
from functools import total_ordering

# Sphinx imports
from sphinx.util.docutils import SphinxDirective

ENV_TAG_KEY = "ct_tags"
"""Key to track the tags in Sphinx's build environment.

Provides a dictionary with *tags* as keys and sets of *document names* as
values.
"""


@total_ordering
class CTDoc:
    """Represent a (tagged) document.

    Parameters
    ----------
    docname : str
    doctitle : str

    Attributes
    ----------
    docname : str
        The document's location, relative to the source directory. May be used
        to generate links to the document, either from reST sources (using
        ``:doc:`[docname]```) or from Jinja2 templates (using
        ``{{ pathto(docname) }}``).
    title : str
        The document's title, that is the first headline in the document.
    """

    def __init__(self, docname, doctitle):
        self.docname = docname
        self.title = doctitle

    def __eq__(self, other):
        """Check equality with ``other`` object."""
        # see https://stackoverflow.com/a/2909119
        # see https://stackoverflow.com/a/8796908
        if isinstance(other, CTDoc):
            return self.__key() == other.__key()
        return NotImplemented

    def __hash__(self):
        """Provide a unique representation of the instance."""
        # see https://stackoverflow.com/a/2909119
        return hash(self.__key())

    def __lt__(self, other):
        """Check equality with ``other`` object."""
        # see https://stackoverflow.com/a/8796908
        if isinstance(other, CTDoc):
            return self.__key() < other.__key()
        return NotImplemented

    def __repr__(self):
        """Provide an instance's ``representation``."""
        # see https://stackoverflow.com/a/12448200
        return "<CTDoc(docname={}, doctitle={})>".format(
            self.docname.__repr__(), self.title.__repr__()
        )

    def __key(self):
        """Provide internal representation of the instance."""
        # see https://stackoverflow.com/a/2909119
        return (self.docname, self.title)


class CTTag:
    """The logical representation of a tag.

    Provides a list of documents (``CTDoc`` instances), that are tagged with
    the instances ``name``.

    Parameters
    ----------
    name : str

    Attributes
    ----------
    name : str
        The actual *value* of the tag. It is stored in *lowercase* only.
    pagename : str
        This is the pagename for this tag.
    _docs : set
        A set of ``CTDoc`` instances. This should not be accessed directly,
        instead the methods ``add_doc`` and ``get_docs`` should be used.
    """

    def __init__(self, name, url_format_string="tags/{}/index"):
        self.name = name.strip().lower()
        # TODO: The URLs are currently hardcoded. If this is to be released as
        #       a generalized extension, this should be configurable with an
        #       extension-specific setting.
        #       The templates already rely on this class's ``pagename``
        #       attribute.
        self.pagename = url_format_string.format(self.name)
        self._docs = set()

    def add_doc(self, docname, doctitle):
        """Add a document to the tag.

        Documents are represented by instances of ``CTDoc``.

        Parameters
        ----------
        docname : str
        doctitle : str
        """
        self._docs.add(CTDoc(docname, doctitle))

    def rm_doc(self, docname):
        """Remove a document from this tag.

        This method is used during purging the environment, before re-reading
        a source file.

        Parameters
        ----------
        docname : str
        """
        self._docs = {doc for doc in self._docs if not doc.docname == docname}

    def merge(self, other):
        """Merge two instances of this class.

        After some sanity checks, it uses the ``set``'s ``update()`` method
        to merge the documents.

        Parameters
        ----------
        other : ``CTTag``
        """
        if not isinstance(other, CTTag):
            return NotImplemented
        if not self.name == other.name:
            raise Exception("Name mismatch")
        self._docs.update(other._docs)

    def contains(self, docname):
        """Determine if a document is associated with a tag.

        Parameters
        ----------
        docname : str
        """
        return len({doc for doc in self._docs if doc.docname == docname}) != 0

    def __repr__(self):
        """Provide an instance's ``representation``."""
        # see https://stackoverflow.com/a/12448200
        return "<CTTag(name={})>".format(self.name)

    def __getitem__(self, index):
        """Make the objects iterable.

        Notes
        -----
        - https://stackoverflow.com/a/7542261
        - https://stackoverflow.com/a/15479974
        """
        return list(self._docs)[index]


class TagDefaultDict(defaultdict):
    """Custom override for Python's ``defaultdict``.

    This enables the defaultdict to use a (custom) class as its default while
    passing the *desired* ``key`` to the constructor of that class.

    While this implementation is pretty generic, it is meant to be used with
    ``CTTag`` as its default.
    """

    def __missing__(self, key):
        """Create a new ``key`` with the provided default ``value``.

        This passes the *desired* key to the constructor of the default class
        for ``value``.
        """
        # see https://stackoverflow.com/a/32932568
        self[key] = new = self.default_factory(key)
        return new


def add_tags_to_render_context(app, pagename, templatename, context, doctree):
    """Add the document's associated tags to the rendering context.

    TODO: This is not really used at the moment, but the idea is to be able
          to render the tags in the layout, outside of the actual body provided
          by the doctree.
    """
    tags_raw = getattr(app.env, ENV_TAG_KEY, {})
    tag_docs = {tags_raw[tag] for tag in tags_raw if tags_raw[tag].contains(pagename)}

    # only add tags to the rendering context if there actually are tags
    if len(tag_docs) > 0:
        context["ct_document_tags"] = tag_docs

    # print("[DEBUG] evaluate_rendering_context() - {}".format(pagename))
    # print("[DEBUG] context: {!r}".format(context))


def add_tag_pages(app):  # noqa: D103
    # print("[DEBUG] add_tag_pages()")

    tags = getattr(app.env, ENV_TAG_KEY, {})
    # print("[DEBUG] tags: {!r}".format(tags))

    # TODO: It might work to pass ``tags_raw`` into the context. This *might*
    #       enable a better tag index, probably allowing to include the count
    #       of articles of a tag beside the tag.
    tag_pages = [("tags/index", {"ct_tags": tags}, "tag_index.html")]

    for tag in tags:
        tag_pages.append(
            (
                tags[tag].pagename,
                {"ct_tag_docs": tags[tag]},
                "tag.html",
            )
        )

    return tag_pages


def purge_document_from_tags(app, env, docname):
    """Remove document from the cached tags dictionary.

    Tag information is stored in Sphinx's build environment, which is cached
    between runs. Before (re-) reading the source file, all existing references
    to a document must be removed from the cached tag information in order to
    allow changes / updates of the tags of a document.

    This function is meant to be attached to Sphinx's ``env-purge-doc`` event
    and will enable the extension to work with parallel builds.
    """
    if hasattr(env, ENV_TAG_KEY):
        tmp = getattr(env, ENV_TAG_KEY)
        for tag in tmp.keys():
            try:
                tmp[tag].rm_doc(docname)
            except KeyError:
                # KeyError is raised if ``docname`` is not in the set referenced
                # by ``tmp[tag]``.
                pass

    # print("[DEBUG] purge_document_from_tags() - {}".format(docname))
    # print("[DEBUG] tags: {!r}".format(getattr(env, ENV_TAG_KEY, None)))


def merge_tags(app, env, docname, other):
    """Merge tags dictionaries from parallel builds.

    While running Sphinx's build in parallel threads, each thread maintains its
    own build environment, which must be merged back into the main thread's
    build environment.

    This function is meant to be attached to Sphinx's ``env-merge-info`` event
    and will enable the extension to work with parallel builds.
    """
    if not hasattr(env, ENV_TAG_KEY):
        setattr(env, ENV_TAG_KEY, TagDefaultDict(CTTag))

    if hasattr(other, ENV_TAG_KEY):
        tmp = getattr(env, ENV_TAG_KEY)
        tmp_o = getattr(other, ENV_TAG_KEY)
        for tag in tmp_o.keys():
            tmp[tag].merge(tmp_o[tag])

    # print("[DEBUG] merge_tags() - {}".format(docname))
    # print("[DEBUG] tags: {!r}".format(getattr(env, ENV_TAG_KEY, None)))


class ContentTagDirective(SphinxDirective):
    """Provide a directive to add *tags* to a document.

    The directive accepts a single argument, which is a list of *tags*,
    seperated by ``;``. At least one tag **must** be provided.

    Example Usage:
    ```
    .. tags:: foo; bar; baz
    ```
    """

    # At least one argument is required (doesn't make any sense without!)
    required_arguments = 1

    # Allow "whitespace" characters in the final argument.
    #
    # The idea is to treat a list of tags like a single argument and parse them
    # in the ``run()`` method.
    #
    # TODO: This needs heavy testing, if this extension goes beyond my personal
    #       project.
    final_argument_whitespace = True

    def run(self):
        """Process the directive.

        The directive treats its argument as a single string, though it is most
        likely a list of tags semantically.

        First step of processing is converting the string into a list of
        strings, representing the tags.

        The tags are stored in Sphinx's build environment and the currently
        processed document (``self.env.docname``) is added to the list of
        documents associated with those tags.
        """
        # ``arguments[0]`` is a ``str``, so just split by ";" (the seperator)
        # and trim whitespaces...
        tag_list = [tag.strip() for tag in self.arguments[0].split(";")]
        # ... and convert non-empty strings to lower case.
        tag_list = [tag.lower() for tag in tag_list if tag]
        tag_list = set(tag_list)
        # print("[DEBUG] tag_list: {!r}".format(tag_list))

        # Add the documents to all associated tags
        if not hasattr(self.env, ENV_TAG_KEY):
            setattr(self.env, ENV_TAG_KEY, TagDefaultDict(CTTag))

        for tag in tag_list:
            # FIXME: The document's title is not really available here...
            getattr(self.env, ENV_TAG_KEY)[tag].add_doc(
                self.env.docname, self.env.docname
            )

        # print("[DEBUG] tags: {!r}".format(getattr(self.env, ENV_TAG_KEY)))

        # as of now, don't add anything to the doctree
        return []


def setup(app):
    """Register the extension with Sphinx.

    This function is required by ``Sphinx``'s extension interface, see
    https://www.sphinx-doc.org/en/master/development/tutorials/helloworld.html#writing-the-extension
    for reference.

    TODO: Finish this!
    """
    app.add_directive("tags", ContentTagDirective)

    app.connect("env-purge-doc", purge_document_from_tags)
    app.connect("env-merge-info", merge_tags)
    app.connect("html-collect-pages", add_tag_pages)
    app.connect("html-page-context", add_tags_to_render_context)

    return {
        "version": "0.0.1",
        "env-version": "1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
