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
