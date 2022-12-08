"""Provide a tagging mechanism for Sphinx."""

# Python imports
from collections import defaultdict

# Sphinx imports
from sphinx.util.docutils import SphinxDirective

ENV_TAG_KEY = "ct_tags"
"""Key to track the tags in Sphinx's build environment.

Provides a dictionary with *tags* as keys and sets of *document names* as
values.
"""

ENV_DOC_KEY = "ct_docs"
"""Key to track the tags of documents in Sphinx's build environment.

Provides a dictionary with *document names* as keys and sets of *tags* as
values.
"""


def add_tags_to_render_context(app, pagename, templatename, context, doctree):
    """Add the document's associated tags to the rendering context.

    TODO: This is not really used at the moment, but the idea is to be able
          to render the tags in the layout, outside of the actual body provided
          by the doctree.
    """
    if hasattr(app.env, ENV_DOC_KEY):
        tmp = getattr(app.env, ENV_DOC_KEY)
        context["ct_document_tags"] = tmp[pagename]

    print("[DEBUG] evaluate_rendering_context() - {}".format(pagename))
    print("[DEBUG] context: {!r}".format(context))
    # print("[DEBUG] html_context: {!r}".format(app.config.html_context))


def add_tag_pages(app):  # noqa: D103
    print("[DEBUG] add_tag_pages()")

    return [("tags/index", {"foo": "bar"}, "tag_overview.html")]


def purge_document_from_tags(app, env, docname):
    """Remove document from the cached tags dictionary.

    Tag information is stored in Sphinx's build environment, which is cached
    between runs. Before (re-) reading the source file, all existing references
    must be removed from the cached tag information in order to allow changes /
    updates of the tags of a document.

    This function is meant to be attached to Sphinx's ``env-purge-doc`` event
    and will enable the extension to work with parallel builds.
    """
    if hasattr(env, ENV_TAG_KEY):
        tmp = getattr(env, ENV_TAG_KEY)
        for tag in tmp.keys():
            try:
                tmp[tag].remove(docname)
            except KeyError:
                # KeyError is raised if ``docname`` is not in the set referenced
                # by ``tmp[tag]``.
                pass

    if hasattr(env, ENV_DOC_KEY):
        tmp = getattr(env, ENV_DOC_KEY)
        # see https://stackoverflow.com/a/11277439
        tmp.pop(docname, None)

    print("[DEBUG] purge_document_from_tags() - {}".format(docname))
    # print("[DEBUG] tags: {!r}".format(getattr(env, ENV_TAG_KEY, None)))
    # print("[DEBUG] docs: {!r}".format(getattr(env, ENV_DOC_KEY, None)))


def merge_tags(app, env, docname, other):
    """Merge tags dictionaries from parallel builds.

    While running Sphinx's build in parallel threads, each thread maintains its
    own build environment, which must be merged back into the main thread's
    build environment.

    This function is meant to be attached to Sphinx's ``env-merge-info`` event
    and will enable the extension to work with parallel builds.
    """
    if not hasattr(env, ENV_TAG_KEY):
        setattr(env, ENV_TAG_KEY, defaultdict(set))

    if hasattr(other, ENV_TAG_KEY):
        tmp = getattr(env, ENV_TAG_KEY)
        tmp_o = getattr(other, ENV_TAG_KEY)
        for tag in tmp_o.keys():
            tmp[tag].update(tmp_o[tag])

    if not hasattr(env, ENV_DOC_KEY):
        setattr(env, ENV_DOC_KEY, defaultdict(set))

    if hasattr(other, ENV_DOC_KEY):
        tmp = getattr(env, ENV_DOC_KEY)
        tmp_o = getattr(other, ENV_DOC_KEY)
        for doc in tmp_o.keys():
            tmp[doc].update(tmp_o[doc])

    print("[DEBUG] merge_tags() - {}".format(docname))
    # print("[DEBUG] tags: {!r}".format(getattr(env, ENV_TAG_KEY, None)))
    # print("[DEBUG] docs: {!r}".format(getattr(env, ENV_DOC_KEY, None)))


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
            setattr(self.env, ENV_TAG_KEY, defaultdict(set))

        for tag in tag_list:
            getattr(self.env, ENV_TAG_KEY)[tag].add(self.env.docname)

        # print("[DEBUG] tags: {!r}".format(getattr(self.env, ENV_TAG_KEY)))

        # Add associated tags to the document
        if not hasattr(self.env, ENV_DOC_KEY):
            setattr(self.env, ENV_DOC_KEY, defaultdict(set))

        # FIXME: Does this automatically remove duplicate items?
        getattr(self.env, ENV_DOC_KEY)[self.env.docname] = tag_list

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
