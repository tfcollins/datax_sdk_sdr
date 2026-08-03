"""Sphinx configuration for the DataX SDR SDK documentation."""

project = "DataX SDR SDK"
author = "Travis Collins"
release = "0.1.0"

extensions = [
    "sphinx.ext.githubpages",
    "sphinx.ext.graphviz",
    "sphinxcontrib.mermaid",
    "myst_parser",
    "adi_doctools",
]
needs_extensions = {"adi_doctools": "0.4.21"}

# deterministicIds: mermaid's default IDs come from Date.now(), so two
# diagrams rendered within the same millisecond collide and one lands
# inside the other's container. A counter-based ID never collides.
mermaid_init_config = {"startOnLoad": False, "deterministicIds": True}

html_theme = "cosmic"
html_logo = "_static/logo.svg"
html_theme_options = {
    "light_logo": "logo.svg",
    "dark_logo": "logo.svg",
}
html_static_path = ["_static"]
html_css_files = ["css/theme-image-swap.css"]
exclude_patterns = ["_build"]
