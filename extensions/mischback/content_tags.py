"""Provide a tagging mechanism for Sphinx."""


def evaluate_rendering_context(  # noqa: D103
    app, pagename, templatename, context, doctree
):
    # TODO: Add docstring, if this event handler is really required!
    print("[DEBUG] pagename: {!r}".format(pagename))
    # print("[DEBUG] context: {!r}".format(context))


def setup(app):
    """Register the extension with Sphinx.

    This function is required by ``Sphinx``'s extension interface, see
    https://www.sphinx-doc.org/en/master/development/tutorials/helloworld.html#writing-the-extension
    for reference.

    TODO: Finish this!
    """
    app.connect("html-page-context", evaluate_rendering_context)

    return {
        "version": "0.0.1",
        "env-version": "1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
