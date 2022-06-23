"""Configuration file for the Sphinx documentation builder."""
import os
import re
import subprocess
import sys


try:
    import importlib.metadata as importlib_metadata
except ImportError:
    # Python < 3.8 with `pip install imporpoetry exec doctlib_metadata`
    import importlib_metadata


SPHINX_IS_RUNNING = "sphinx" in sys.modules


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
extensions = [
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_tabs.tabs",
    "chios.bolditalic",
    "sphinx_argparse_cli",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# See: https://stackoverflow.com/a/30624034/9167585
# https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-nitpick_ignore
nitpick_ignore = [
    ("py:class", "argparse._SubParsersAction"),
    ("py:class", "importlib_metadata.EntryPoint"),  # Python <= 3.9
    ("py:class", "jmespath.exceptions.JMESPathError"),
    ("py:class", "jmespath.functions.Functions"),
    ("py:class", "jmespath.parser.ParsedResult"),
    ("py:class", "project_config.types.Results"),
]
nitpick_ignore_regex = [
    ("py:class", r"^t.[A-Z]\w+$"),
    ("py:class", r"^[A-Za-z]+$"),  # internal references
    ("py:class", r"^typing_extensions\.\w+$"),
]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
html_css_files = [
    os.path.join("css", "override-styles.css"),
]

# -- Options for `sphinx.ext.autosectionlabel` -------------------------------

# Make sure the target is unique
autosectionlabel_prefix_document = True

# -- Options for `sphinx.ext.intersphinx` ------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "diskcache": ("https://grantjenks.com/docs/diskcache", None),
    "pyjson5": ("https://pyjson5.readthedocs.io/en/latest/", None),
}

# ----------------------------------------------------------------------------

# --- Examples page creation ---

if SPHINX_IS_RUNNING:

    import pygments.lexers

    # Some Pygments lexers are not available yet, so we use fallbacks
    PYGMENTS_LEXERS_FALLBACKS = {
        # JSON5 lexer is not implemented
        # https://github.com/pygments/pygments/issues/1880
        "json5": "js",
    }

    def _parse_example_readme(readme_filepath):
        result = {"name": None, "body": ""}
        with open(readme_filepath) as f:
            readme_lines = f.readlines()
        _inside_metadata = False
        for line in readme_lines:
            if not _inside_metadata:
                if line.replace("\r\n", "\n") == "..\n":
                    _inside_metadata = True
                else:
                    result["body"] += line
            else:
                if line.startswith("   "):
                    if line.lower().startswith("   name:"):
                        result["name"] = line.split(":", maxsplit=1)[-1].strip()
                else:
                    _inside_metadata = False
        return result

    def _parse_example_directory(example_dir):
        example_data = {"name": None, "body": "", "files": []}
        for filename in os.listdir(example_dir):
            filepath = os.path.join(example_dir, filename)
            if filename == "README.rst":
                example_data.update(_parse_example_readme(filepath))
            else:
                with open(filepath) as f:
                    content = f.read()
                    # put configuration files first
                    if filename in (".project-config.toml", "pyproject.toml"):
                        example_data["files"].insert(0, (filename, content))
                    else:
                        example_data["files"].append((filename, content))
        return example_data

    def _generate_example_tabs(files):
        tabs_content = ".. tabs::\n\n"
        for filename, content in files:
            # check if pygments has a lexer for the code block because
            # if we add a code block without available lexer, Sphinx will
            # raise a warning
            try:
                code_block_language = pygments.lexers.get_lexer_for_filename(
                    filename,
                ).aliases[0]
            except Exception:
                extension = filename.split(".")[-1]
                try:
                    code_block_language = PYGMENTS_LEXERS_FALLBACKS[extension]
                except KeyError:
                    code_block_language = "text"

            tabs_content += (
                f"   .. tab:: {filename}\n\n"
                f"      .. code-block:: {code_block_language}\n\n"
            )
            indented_content = "\n".join(
                (" " * 9 + line) if line.strip() else ""
                for line in content.splitlines()
            )
            tabs_content += f"{indented_content}\n\n"
        return tabs_content

    def _create_examples_page():
        """Creates the examples page with the content in examples/ folder."""
        examples_dir = os.path.join(rootdir, "examples")
        examples_data, error_messages = [], []
        for example_dirname in sorted(os.listdir(examples_dir)):
            # ignore private examples (used mainly for acceptance tests)
            if example_dirname.startswith("_"):
                continue
            example_dir = os.path.join(examples_dir, example_dirname)
            example_data = _parse_example_directory(example_dir)

            if not example_data.get("name"):
                example_reldir = os.path.relpath(example_dir, rootdir)
                error_messages.append(
                    f"The example at {example_reldir} does not have a name",
                )
            examples_data.append(example_data)

        if error_messages:
            for error_message in error_messages:
                sys.stderr.write(f"{error_message}\n")
            raise SystemExit(1)

        examples_page_content = """********
Examples
********

"""

        for example_data in examples_data:
            examples_page_content += (
                f'{example_data["name"]}\n{"=" * len(example_data["name"])}\n\n'
            )
            if example_data["body"]:
                examples_page_content += f'{example_data["body"]}\n'
            examples_page_content += _generate_example_tabs(
                example_data["files"],
            )

        examples_page_content += """.. raw:: html

   <hr>

.. tip::

   For more complex examples check my own styles at `mondeja/project-config-styles`_.

   .. _mondeja/project-config-styles: https://github.com/mondeja/project-config-styles
"""  # noqa: E501

        examples_page_path = os.path.join(rootdir, "docs", "examples.rst")
        with open(examples_page_path, "w") as f:
            f.write(examples_page_content)

    _create_examples_page()

# ---------------------------------------------------------

# --- sphinx-apidoc ---

if SPHINX_IS_RUNNING:
    subprocess.run(
        [
            "sphinx-apidoc",
            "-o",
            os.path.join(rootdir, "docs/dev/reference"),
            "-H",
            "Reference",
            "-ePMf",
            os.path.join(rootdir, "src/project_config"),
        ],
        check=True,
    )

# ---------------------------------------------------------
