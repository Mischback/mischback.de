"""Provide a tagging mechanism for Sphinx."""

# Sphinx imports
from sphinx.util.docutils import SphinxDirective


def evaluate_rendering_context(  # noqa: D103
    app, pagename, templatename, context, doctree
):
    # TODO: Add docstring, if this event handler is really required!
    print("[DEBUG] pagename: {!r}".format(pagename))
    # print("[DEBUG] context: {!r}".format(context))


class ContentTagDirective(SphinxDirective):  # noqa: D101
    # TODO: Add docstring!

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

    def run(self):  # noqa: D102
        # TODO: Add docstring!
        tag_list = self.arguments[0]
        print("[DEBUG] tag_list: {!r}".format(tag_list))

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

    return {
        "version": "0.0.1",
        "env-version": "1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
