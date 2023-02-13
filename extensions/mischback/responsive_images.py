"""Generate the required (HTML) markup for responsive images.

This extension handles the markup generation only, the actual images are
generated using the utility script in ``util/process-image.py``.
"""


def setup(app):
    """Register the extension with Sphinx.

    This function is required by Sphinx's extension interface, see
    https://www.sphinx-doc.org/en/master/development/tutorials/helloworld.html#writing-the-extension
    for reference.
    """
    print("HELLO responsive_images")

    return {
        "version": "0.0.1",
        "env-version": "1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
