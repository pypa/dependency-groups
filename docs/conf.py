import datetime
import importlib.metadata

project = "dependency-groups"
copyright = f"2023-{datetime.datetime.today().strftime('%Y')}, Stephen Rosen"
author = "Stephen Rosen"

# The full version, including alpha/beta/rc tags
release = importlib.metadata.version("dependency_groups")

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx_issues",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

issues_github_path = "pypa/dependency-groups"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build"]

# HTML theme options
html_theme = "furo"
pygments_style = "friendly"
pygments_dark_style = "monokai"  # this is a furo-specific option
html_theme_options = {
    "source_repository": "https://github.com/pypa/dependency-groups/",
    "source_branch": "main",
    "source_directory": "docs/",
}
