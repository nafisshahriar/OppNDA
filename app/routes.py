"""
Web Routes for OppNDA
Handles page rendering and static file serving.
"""

import os
import sys
import json
import platform
import subprocess
from pathlib import Path
from flask import Blueprint, render_template, send_from_directory, current_app, request, jsonify

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


@main_bp.route('/run-one', methods=['POST'])
def run_one_pipeline():
    """Complete simulation pipeline: Save config → Run ONE → Post-processing.
    
    This handles both /run-one (legacy) and works for the complete pipeline.
    """
    try:
        data = request.get_json() or {}
        
        base_dir = current_app.config['BASE_DIR']
        config_dir = current_app.config['CONFIG_DIR']
        core_dir = current_app.config['CORE_DIR']
        
        # Config file mapping
        CONFIG_FILES = {
            'analysis': 'analysis_config.json',
            'averager': 'averager_config.json',
            'regression': 'regression_config.json'
        }
        
        results = {
            'settings_saved': False,
            'configs_saved': [],
            'simulation': None,
            'post_processing': []
        }
        
        # ============================================================
        # STEP 1: Save simulation settings file
        # ============================================================
        settings_filename = None
        if 'settings' in data:
            settings = data['settings']
            filename = settings.get('filename', 'default_settings.txt')
            content = settings.get('content', '')
            
            # Sanitize filename
            filename = Path(filename).name
            if not filename.endswith('.txt'):
                filename += '.txt'
            
            settings_path = base_dir / filename
            with open(settings_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            settings_filename = filename
            results['settings_saved'] = True
            results['settings_file'] = str(settings_path)
        
        # ============================================================
        # STEP 2: Save post-processing configs (with merge)
        # ============================================================
        def deep_merge(base, updates):
            """Deep merge updates into base dict."""
            import copy
            result = copy.deepcopy(base)
            for key, value in updates.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result
        
        for config_name in ['analysis', 'averager', 'regression']:
            if config_name in data:
                config_path = config_dir / CONFIG_FILES[config_name]
                
                existing_config = {}
                if config_path.exists():
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            existing_config = json.load(f)
                    except json.JSONDecodeError:
                        existing_config = {}
                
                merged_config = deep_merge(existing_config, data[config_name])
                
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(merged_config, f, indent=2)
                
                results['configs_saved'].append(config_name)
        
        # ============================================================
        # STEP 3: Build ONE simulator command
        # ============================================================
        batch_count = data.get('batch_count', 0)
        compile_first = data.get('compile', False)
        enable_ml = data.get('enable_ml', False)
        
        # Detect OS
        is_windows = platform.system() == 'Windows'
        
        if is_windows:
            one_cmd = 'one.bat'
            compile_cmd = 'compile.bat'
        else:
            one_cmd = './one.sh'
            compile_cmd = './compile.sh'
        
        # Build command
        command_parts = []
        
        if compile_first:
            command_parts.append(compile_cmd)
            command_parts.append('&&')
        
        command_parts.append(one_cmd)
        
        if batch_count and batch_count > 0:
            command_parts.append('-b')
            command_parts.append(str(batch_count))
        
        if settings_filename:
            command_parts.append(settings_filename)
        
        full_command = ' '.join(command_parts)
        
        # ============================================================
        # STEP 4: Run ONE simulator
        # ============================================================
        one_path = base_dir / (one_cmd.replace('./', ''))
        if not one_path.exists():
            return jsonify({
                'success': False,
                'message': f'ONE simulator not found: {one_path}. Settings were saved successfully.',
                'results': results,
                'command': full_command
            }), 404
        
        sim_result = subprocess.run(
            full_command,
            shell=True,
            cwd=str(base_dir),
            capture_output=True,
            text=True
        )
        
        results['simulation'] = {
            'command': full_command,
            'success': sim_result.returncode == 0,
            'output': sim_result.stdout if sim_result.returncode == 0 else sim_result.stderr
        }
        
        if sim_result.returncode != 0:
            return jsonify({
                'success': False,
                'message': 'ONE simulation failed',
                'results': results
            }), 500
        
        # ============================================================
        # STEP 5: Auto-run post-processing pipeline
        # ============================================================
        for script_name in ['averager.py', 'analysis.py']:
            script_path = core_dir / script_name
            if script_path.exists():
                result = subprocess.run(
                    [sys.executable, str(script_path)],
                    cwd=str(base_dir),
                    capture_output=True,
                    text=True
                )
                results['post_processing'].append({
                    'script': script_name,
                    'success': result.returncode == 0,
                    'output': result.stdout if result.returncode == 0 else result.stderr
                })
        
        # Run regression if ML enabled
        if enable_ml:
            regression_script = core_dir / 'regression.py'
            if regression_script.exists():
                result = subprocess.run(
                    [sys.executable, str(regression_script)],
                    cwd=str(base_dir),
                    capture_output=True,
                    text=True
                )
                results['post_processing'].append({
                    'script': 'regression.py',
                    'success': result.returncode == 0,
                    'output': result.stdout if result.returncode == 0 else result.stderr
                })
        
        return jsonify({
            'success': True,
            'message': 'Complete pipeline executed successfully',
            'results': results
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
