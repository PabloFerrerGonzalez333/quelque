project = "Quelque"
author = "Pablo Ferrer Gonzalez"
copyright = "2026, Pablo Ferrer Gonzalez"

extensions = [
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build"]

html_theme = "furo"
html_title = "Quelque"
html_static_path = ["_static"]
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}
