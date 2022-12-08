"""Provide a tagging mechanism for Sphinx."""

# Python imports
from collections import defaultdict

# Sphinx imports
from sphinx.util.docutils import SphinxDirective

ENV_TAG_KEY = "content_tags"


def evaluate_rendering_context(  # noqa: D103
    app, pagename, templatename, context, doctree
):
    # TODO: Add docstring, if this event handler is really required!
    print("[DEBUG] pagename: {!r}".format(pagename))
    # print("[DEBUG] context: {!r}".format(context))
    
    
def purge_document_from_tags(app, env, docname):
    """Remove document from the cached tags dictionary.
    
    Tag information is stored in Sphinx's build environment, which is cached 
    between runs. Before (re-) reading the source file, all existing references
    must be removed from the cached tag information in order to allow changes /
    updates of the tags of a document.
    
    This function is meant to be attached to Sphinx's ``env-purge-doc`` event
    and will enable the extension to work with parallel builds.
    """
    if not hasattr(env, ENV_TAG_KEY):
        return
    
    tmp = getattr(env, ENV_TAG_KEY)
    for tag in tmp.keys():
        try:
            tmp[tag].remove(docname)
        except KeyError:
            # KeyError is raised if ``docname`` is not in the set referenced
            # by ``tmp[tag]``.
            pass
        
    print("[DEBUG] tags: {!r}".format(getattr(env, ENV_TAG_KEY)))


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
        # ... and remove empty strings from the result.
        tag_list = [tag for tag in tag_list if tag]
        print("[DEBUG] tag_list: {!r}".format(tag_list))

        if not hasattr(self.env, ENV_TAG_KEY):
            setattr(self.env, ENV_TAG_KEY, defaultdict(set))

        for tag in tag_list:
            getattr(self.env, ENV_TAG_KEY)[tag].add(self.env.docname)

        print("[DEBUG] tags: {!r}".format(getattr(self.env, ENV_TAG_KEY)))

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

    # app.connect("html-page-context", evaluate_rendering_context)
    app.connect("env-purge-doc", purge_document_from_tags)

    return {
        "version": "0.0.1",
        "env-version": "1",
        "parallel_read_safe": False,
        "parallel_write_safe": False,
    }
