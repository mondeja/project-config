"""Configuration file for the Sphinx documentation builder."""

import json
import os
import re
import shutil
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
with open(os.path.join(rootdir, "LICENSE"), encoding="utf-8") as f:
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
    "sphinx_github_changelog",
    "sphinx_argparse_cli",
    "chios.bolditalic",
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
    ("py:class", "pytest.MonkeyPatch"),
    ("py:class", "_pytest.monkeypatch.MonkeyPatch"),
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
    "deepmerge": ("https://deepmerge.readthedocs.io/en/latest/", None),
}

exclude_patterns = ["_examples", "_build", "Thumbs.db", ".DS_Store"]

# ----------------------------------------------------------------------------

# --- Examples page creation ---

if SPHINX_IS_RUNNING:

    import pygments.lexers

    # Some Pygments lexers are not available yet, so we use fallbacks
    PYGMENTS_LEXERS_FALLBACKS = {
        # JSON5 lexer is not implemented
        # https://github.com/pygments/pygments/issues/1880
        "json5": "js",
        "gitignore": "text",
        "txt": "shell",
    }

    def _pygments_lexer_by_extension(extension):
        if not extension.endswith("/"):
            if extension in PYGMENTS_LEXERS_FALLBACKS:
                return PYGMENTS_LEXERS_FALLBACKS[extension]
            elif extension:
                return extension
        return "text"

    def _parse_example_readme(readme_filepath):
        result = {"name": None, "body": ""}
        with open(readme_filepath, encoding="utf-8") as f:
            readme_content = f.read()
        _inside_metadata = False
        for line in readme_content.splitlines():
            if not _inside_metadata:
                if line == "..":
                    _inside_metadata = True
                else:
                    if result["body"]:
                        line = f" {line}\n"
                    result["body"] += line
            else:
                if line.startswith("   "):
                    if line.lower().startswith("   name:"):
                        result["name"] = line.split(":", maxsplit=1)[-1].strip()
                    elif line.lower().startswith("   bodyfiles:"):
                        result["bodyfiles"] = json.loads(
                            line.split(":", maxsplit=1)[-1].strip(),
                        )
                else:
                    _inside_metadata = False

        if not result["body"].endswith("\n"):
            result["body"] += "\n"

        return result

    def _parse_example_directory(example_dir):
        example_data = {"name": None, "body": "", "files": []}
        for filename in os.listdir(example_dir):
            filepath = os.path.join(example_dir, filename)
            if filename == "README.rst":
                example_data.update(_parse_example_readme(filepath))
            else:
                if os.path.isdir(filepath):
                    content = ""
                    filename = f'{filename.rstrip("/")}/'
                else:
                    with open(filepath, encoding="utf-8") as f:
                        content = f.read()
                # put style files first
                if content and "style" in filename:
                    example_data["files"].insert(0, (filename, content))
                else:
                    example_data["files"].append((filename, content))
        return example_data

    def _generate_example_tabs(files):
        tabs_content = ".. tabs::\n\n"

        # put empty files at the end
        files = sorted(files, key=lambda x: not len(x[1]))

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
                code_block_language = _pygments_lexer_by_extension(extension)

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
            if not example_dirname[0].isdigit():
                continue
            example_dir = os.path.join(examples_dir, example_dirname)
            if not os.path.isdir(example_dir):
                continue
            example_data = _parse_example_directory(example_dir)

            if not example_data.get("name"):
                example_reldir = os.path.relpath(example_dir, rootdir)
                error_messages.append(
                    f"The example at {example_reldir} does not have a name",
                )
            examples_data.append(example_data)

        if error_messages:
            raise Exception("\n".join(error_messages))

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

    def _create_tutorials_pages():
        tutorials_dir = os.path.join(rootdir, "examples", "tutorials")
        for tutorial_dirname in sorted(os.listdir(tutorials_dir)):
            tutorial_dir = os.path.join(tutorials_dir, tutorial_dirname)
            if not os.path.isdir(tutorial_dir):
                continue
            tutorial_data = _parse_example_directory(tutorial_dir)
            tutorial_page_content = (
                f'{tutorial_data["name"]}\n'
                f'{"=" * len(tutorial_data["name"])}\n\n'
            )
            if tutorial_data["body"]:
                tutorial_page_content += f'{tutorial_data["body"]}\n'
            if "bodyfiles" in tutorial_data:
                for bodyfile_name in tutorial_data["bodyfiles"]:
                    code_block_lang = _pygments_lexer_by_extension(
                        os.path.splitext(bodyfile_name)[-1].split(".")[-1],
                    )
                    with open(
                        os.path.join(tutorial_dir, bodyfile_name),
                        encoding="utf-8",
                    ) as f:
                        bodyfile_content = f.read().splitlines()
                    tutorial_page_content += (
                        f"\n\n.. code-block:: {code_block_lang}\n\n"
                        + "\n".join(
                            [
                                f"   {line}" if line else ""
                                for line in bodyfile_content
                            ],
                        )
                    )
            tutorial_page_content = tutorial_page_content.replace(
                "\n\n\n",
                "\n",
            )
            tutorial_page_path = os.path.join(
                rootdir,
                "docs",
                "tutorials",
                "pages",
                f"{tutorial_dirname}.rst",
            )
            with open(tutorial_page_path, "w") as f:
                f.write(tutorial_page_content)

    _create_examples_page()
    _create_tutorials_pages()

    examples_dir = os.path.join(rootdir, "examples")
    examples_docs_files_dir = os.path.join(rootdir, "docs", "_examples")
    if not os.path.isdir(examples_docs_files_dir):
        os.mkdir(examples_docs_files_dir)

    examples_to_include = [11]
    for example_num in examples_to_include:
        if not any(
            [
                fname.lstrip("0").startswith(str(example_num))
                for fname in os.listdir(examples_dir)
            ],
        ):
            raise Exception(
                "Non existing example files to include in the documentation",
            )

        for fname in os.listdir(examples_dir):
            if not fname[0].isdigit():
                continue

            if fname.lstrip("0").startswith(str(example_num)):
                src_dir = os.path.join(examples_dir, fname)
                dst_dir = os.path.join(examples_docs_files_dir, fname)

                if os.path.isdir(dst_dir):
                    shutil.rmtree(dst_dir)
                shutil.copytree(src_dir, dst_dir)


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
