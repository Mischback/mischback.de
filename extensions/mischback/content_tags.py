"""Provide a tagging mechanism for Sphinx.

This extension adds a ``tags`` directive to Sphinx standard domain. The
directive will not produce any output (it does not add anything to docutils'
tree), but it will keep track of *content tags* assigned to documents.

The extension creates a dedicated page for every tag, linking to the
associated documents aswell as a tag overview page, providing links to all
tag pages.

The required templates (``tag.html`` and ``tag_index.html``) must be provided
by the theme (see `#19 <https://github.com/Mischback/static-web/issues/19>`_).

The extension hooks into Sphinx's build system using the provided events. It
does not rely on Sphinx's ``:index:``, which feels hacky, but creating the
required indices dynamically failed badly. Instead, the extension manages all
tag-related data internally.

While Sphinx is running the ``html`` or ``dirhtml`` builder, all documents with
tags will have them available in the context passed to Jinja2. It is up to the
theme to provide the required markup.
"""

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

    def __init__(self, name):
        self.name = name.strip().lower()
        # During object initialization, the ``pagename`` is not determined!
        # Instead, the first call to ``add_doc()`` will set the ``pagename``
        # for the object.
        #
        # Reasoning: Objects of this class are not directly created /
        # initialized in this extension, instead they are created using a
        # custom ``defaultdict`` implementation (see ``TagDefaultDict`` below)
        # while the very first document is added to the desired tag.
        #
        # The ``pagename`` should be dependent on a Sphinx configuration value,
        # thus the template to create the ``pagename`` can not be hardcoded in
        # ``TagDefaultDict`` but must be provided when Sphinx's config has
        # been fully evaluated.
        self.pagename = None
        self._docs = set()

    def add_doc(self, docname, doctitle, pagename_template="tags/{}"):
        """Add a document to the tag.

        Documents are represented by instances of ``CTDoc``.

        Parameters
        ----------
        docname : str
        doctitle : str

        Side Effects
        ------------
        The very first call to ``add_doc`` will set the object's ``pagename``
        attribute. Reasons are mostly implementation details, see comments in
        the class's ``__init__()``.
        """
        if self.pagename is None:
            self.pagename = pagename_template.format(self.name)
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

    def set_doc_titles(self, titles):
        """Set the titles of all tagged documents.

        This method is called during the ``env-update`` event handler and will
        update the titles of all documents.

        See ``update_doc_titles()`` for details of this operation.

        Parameters
        ----------
        titles : dict
        """
        for doc in self._docs:
            # print("[DEBUG] -> {}".format(titles[doc.docname].astext()))
            doc.title = titles[doc.docname].astext()

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

    The document's tags will be accessible as ``ct_document_tags`` in Jinja2
    templates. This is a ``set`` of ``CTTag`` instances.

    This function will not add ``ct_document_tags`` if there are no tags
    associated with the document.
    """
    tags_raw = getattr(app.env, ENV_TAG_KEY, {})
    tag_docs = {tags_raw[tag] for tag in tags_raw if tags_raw[tag].contains(pagename)}

    # only add tags to the rendering context if there actually are tags
    if len(tag_docs) > 0:
        context["ct_document_tags"] = tag_docs

    # print("[DEBUG] evaluate_rendering_context() - {}".format(pagename))
    # print("[DEBUG] context: {!r}".format(context))


def add_tag_pages(app):
    """Add the required tag-related pages to Sphinx's build.

    This will automatically create a *tag overview* page with an URL that may
    be configured using ``ct_tag_overview_url`` in Sphinx's configuration and
    a *page for every tag* that is used in the source files, whose URLs may be
    configured using ``ct_tag_page_url_template`` in Sphinx's configuration.

    This function is meant to be attached to Sphinx's ``html-collect-pages``
    event.
    """
    # print("[DEBUG] add_tag_pages()")

    tags = getattr(app.env, ENV_TAG_KEY, {})
    # print("[DEBUG] tags: {!r}".format(tags))

    tag_pages = [(app.config.ct_tag_overview_url, {"ct_tags": tags}, "tag_index.html")]

    for tag in tags:
        tag_pages.append(
            (
                tags[tag].pagename,
                {"ct_tag_docs": tags[tag]},
                "tag.html",
            )
        )

    return tag_pages


def update_doc_titles(app, env):
    """Update the documents' titles.

    When the tags dictionary is built, the documents' titles may not be
    available yet. This function is executed, when Sphinx has finished all
    parsing tasks and will update the ``title`` attributes of all ``CTDoc``
    instances.

    This is a highly inefficient operation, as it will iterate over all tags
    and all tagged documents.

    This function is meant to be attached to Sphinx's ``env-updated`` event.
    """
    titles = env.titles
    tags = getattr(app.env, ENV_TAG_KEY, {})

    for tag in tags:
        tags[tag].set_doc_titles(titles)


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
            getattr(self.env, ENV_TAG_KEY)[tag].add_doc(
                self.env.docname,
                "",
                self.env.config.ct_tag_page_url_template,
            )

        # print("[DEBUG] tags: {!r}".format(getattr(self.env, ENV_TAG_KEY)))

        # as of now, don't add anything to the doctree
        return []


def setup(app):
    """Register the extension with Sphinx.

    This function is required by Sphinx's extension interface, see
    https://www.sphinx-doc.org/en/master/development/tutorials/helloworld.html#writing-the-extension
    for reference.

    It makes the extension's configuration values available for Sphinx, adds
    the extension's ``tags`` directive and hooks into Sphinx's build system
    using dedicated *events* (the events are documented in the respective
    event handler's / callback's docstring).
    """
    app.add_config_value("ct_tag_overview_url", "tags", "env")
    app.add_config_value("ct_tag_page_url_template", "tags/{}", "env")

    app.add_directive("tags", ContentTagDirective)

    app.connect("env-purge-doc", purge_document_from_tags)
    app.connect("env-updated", update_doc_titles)
    app.connect("env-merge-info", merge_tags)
    app.connect("html-collect-pages", add_tag_pages)
    app.connect("html-page-context", add_tags_to_render_context)

    return {
        "version": "0.0.1",
        "env-version": "1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
