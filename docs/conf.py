from pallets_sphinx_themes import ProjectLink, get_version

# Project --------------------------------------------------------------

project = "Click"
copyright = "2014 Pallets Team"
author = "Pallets Team"
release, version = get_version("Click")

# General --------------------------------------------------------------

master_doc = "index"
extensions = ["sphinx.ext.autodoc", "sphinx.ext.intersphinx", "pallets_sphinx_themes"]
intersphinx_mapping = {"python": ("https://docs.python.org/3/", None)}

# HTML -----------------------------------------------------------------

html_theme = "click"
html_theme_options = {
    "index_sidebar_logo": False,
}
html_context = {
    "project_links": [
        ProjectLink("Donate to Pallets", "https://palletsprojects.com/donate"),
        ProjectLink("Click Website", "https://palletsprojects.com/p/click/"),
        ProjectLink("PyPI releases", "https://pypi.org/project/Click/"),
        ProjectLink("Source Code", "https://github.com/pallets/click/"),
        ProjectLink("Issue Tracker", "https://github.com/pallets/click/issues/"),
    ]
}
html_sidebars = {
    "index": ["project.html", "versions.html", "searchbox.html"],
    "**": ["localtoc.html", "relations.html", "versions.html", "searchbox.html"],
}
singlehtml_sidebars = {"index": ["project.html", "versions.html", "localtoc.html"]}
html_static_path = ["_static"]
html_favicon = "_static/click-icon.png"
html_logo = "_static/click-logo-sidebar.png"
html_show_sourcelink = False
html_domain_indices = False
html_experimental_html5_writer = True

# LaTeX ----------------------------------------------------------------

latex_documents = [
    (master_doc, "Click.tex", "Click Documentation", "Pallets Team", "manual")
]
