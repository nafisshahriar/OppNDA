# Sphinx Configuration for OppNDA Documentation
# Built with Sphinx autodoc and napoleon extensions

import os
import sys

# Add project root to path for autodoc
sys.path.insert(0, os.path.abspath('..'))

# -- Project information -----------------------------------------------------
project = 'OppNDA'
copyright = '2024, OppNDA Contributors'
author = 'OppNDA Contributors'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',           # Auto-generate docs from docstrings
    'sphinx.ext.napoleon',          # Support Google/NumPy style docstrings
    'sphinx.ext.viewcode',          # Add links to source code
    'sphinx.ext.intersphinx',       # Link to other projects' docs
    'sphinx.ext.todo',              # Support TODO directives
    'sphinx.ext.coverage',          # Check documentation coverage
]

# Napoleon settings for Google-style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True

# Autodoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}
autodoc_typehints = 'description'

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_logo = None  # Add logo path if available
html_favicon = None

# Theme options
html_theme_options = {
    'navigation_depth': 4,
    'collapse_navigation': False,
    'sticky_navigation': True,
    'includehidden': True,
    'titles_only': False,
}

# -- Intersphinx configuration -----------------------------------------------
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'pandas': ('https://pandas.pydata.org/docs/', None),
}

# -- TODO extension ----------------------------------------------------------
todo_include_todos = True

# -- Templates ---------------------------------------------------------------
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Source suffix -----------------------------------------------------------
source_suffix = '.rst'
master_doc = 'index'

# -- LaTeX/PDF Configuration -------------------------------------------------
# Use XeLaTeX for better Unicode and font support
latex_engine = 'xelatex'
latex_elements = {
    'papersize': 'a4paper',
    'pointsize': '11pt',
    'preamble': '',
    'figure_align': 'htbp',
    'extraclassoptions': 'openany,oneside',
    'fontpkg': '',  # Don't load extra font packages
}

latex_documents = [
    (master_doc, 'OppNDA.tex', 'OppNDA Documentation',
     'OppNDA Contributors', 'manual'),
]

# Suppress some common warnings
suppress_warnings = ['toc.secnum']
