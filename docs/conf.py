from shutil import copytree, rmtree
from site import getsitepackages

from sphinx.application import Sphinx

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'pntOS-Python Exercises'
copyright = '2026, IS4S'
author = 'IS4S'
release = '0.1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['myst_parser', 'sphinx_design']

# Myst settings
myst_enable_extensions = [
    'dollarmath',  # For inline and block math using $...$
]
myst_heading_anchors = 3
myst_footnote_sort = False


templates_path = ['_templates']


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
site_packages_dir = getsitepackages()[0]
branding_dir = f'{site_packages_dir}/branding/'

# Copy images from site packages into docs directory
rmtree('images', ignore_errors=True)
copytree(src=branding_dir + '/figures/', dst='images')

html_static_path = ['_static', branding_dir]

html_logo = branding_dir + 'pntOs_Logo_Gradient_Light_Horizontal.png'
html_theme_options = {
    'logo_only': True,
    'collapse_navigation': True,
}
html_favicon = f'{branding_dir}/favicon.ico'

nitpicky = True

# Linkcheck builder options.
linkcheck_allowed_redirects = {}
# Ignore line number anchors (e.g. #L12), since linkcheck gives false positives for these.
linkcheck_anchors_ignore = [r'L\d*']


def setup(app: Sphinx) -> None:
    app.add_css_file('pntos.css')
    app.add_css_file('hk-grotesk.css')
