"""Make Jinja2's debug extension available in ``Sphinx``'s templates."""


def activate_jinja2_debug_ext(app):
    """Add the debug extension to Jinja2's environment.

    The function traverses from ``Sphinx``'s ``app`` to the Jinja2 environment
    and uses its ``add_extension()`` method to activate the debug extension as
    specified here:

    - https://jinja.palletsprojects.com/en/3.0.x/extensions/#adding-extensions
    - https://jinja.palletsprojects.com/en/3.0.x/extensions/#debug-extension
    """
    if hasattr(app.builder, "templates"):
        app.builder.templates.environment.add_extension("jinja2.ext.debug")


def setup(app):
    """Register the extension with Sphinx.

    This function is required by ``Sphinx``'s extension interface, see
    https://www.sphinx-doc.org/en/master/development/tutorials/helloworld.html#writing-the-extension
    for reference.

    It connects this plugins (only) function with the ``"builder-inited"`` event, see
    https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx-core-events
    for reference.
    """
    app.connect("builder-inited", activate_jinja2_debug_ext)
