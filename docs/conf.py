"""Configuration file for the Sphinx documentation builder."""
import os
import re
import sys


try:
    import importlib.metadata as importlib_metadata
except ImportError:
    # Python < 3.8 with `pip install imporpoetry exec doctlib_metadata`
    import importlib_metadata


# -- Path setup --------------------------------------------------------------
rootdir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, rootdir)

# -- Project information -----------------------------------------------------
metadata = importlib_metadata.distribution("project-config").metadata
with open(os.path.join(rootdir, "LICENSE")) as f:
    license_years_range = re.search(
        r"Copyright \(c\) (\d+\-?\d*)",
        f.read(),
    ).group(1)
project = metadata["name"]
author = metadata["author"]
project_copyright = f"{license_years_range}, {author}"
release = metadata["version"]
version = ".".join(release.split(".")[:2])


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = []

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
