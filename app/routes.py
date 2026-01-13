"""
Web Routes for OppNDA
Handles page rendering and static file serving.
"""

import os
from pathlib import Path
from flask import Blueprint, render_template, send_from_directory, current_app

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Serve the main settings page."""
    return render_template('settings.html')


@main_bp.route('/nda')
def nda():
    """Serve the analysis results page with plot gallery."""
    plots_dir = current_app.config['PLOTS_DIR']
    
    plot_files = []
    if plots_dir.exists():
        for fname in os.listdir(plots_dir):
            if fname.lower().endswith(('.png', '.jpg', '.jpeg', '.svg')):
                plot_files.append(fname)
    plot_files.sort()
    
    img_urls = [f"/plots/{fname}" for fname in plot_files]
    return render_template('nda.html', img_urls=img_urls)


@main_bp.route('/plots/<path:filename>')
def serve_plot(filename):
    """Serve plot images from the plots directory."""
    return send_from_directory(
        str(current_app.config['PLOTS_DIR']), 
        filename
    )


@main_bp.route('/GUI/<path:filename>')
def serve_gui_static(filename):
    """Serve static GUI files."""
    gui_dir = current_app.config['BASE_DIR'] / 'GUI'
    return send_from_directory(str(gui_dir), filename)
