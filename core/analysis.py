#!/usr/bin/env python3
"""
Smart Adaptive Analysis Tool - Automatically detects and visualizes data patterns
"""

import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import re
import numpy as np
import json
import sys
from pathlib import Path
from collections import defaultdict
from multiprocessing import Pool
import traceback
import time

# Cross-platform path resolution
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONFIG_DIR = PROJECT_ROOT / 'config'

# Import resource manager for dynamic worker optimization
try:
    from core.resource_manager import ResourceManager, get_optimal_workers
    RESOURCE_MANAGER_AVAILABLE = True
except ImportError:
    RESOURCE_MANAGER_AVAILABLE = False

def load_config(config_path=None):
    """Load configuration from JSON file (cross-platform)"""
    if config_path is None:
        config_path = CONFIG_DIR / "analysis_config.json"
    else:
        config_path = Path(config_path)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Config file '{config_path}' not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in config file: {e}")
        sys.exit(1)

class SmartFileParser:
    """Intelligently parse both averaged and raw files"""
    
    def __init__(self, config):
        self.config = config
        self.report_dir = config['directories']['report_dir']
        self.separator = config['data_separator']
        self.metrics = config['metrics']['include']
        self.ignore_fields = set(config['metrics']['ignore'])
        
    def is_average_file(self, filename):
        """Check if file is an averaged report"""
        return '_average' in filename.lower() and filename.endswith(self.config['file_patterns']['report_extension'])
    
    def get_report_type(self, filename):
        """Extract report type from filename"""
        # Try to identify report type from filename
        for report_type in self.config.get('report_types', ['MessageStatsReport', 'CCNApplicationReporter']):
            if report_type in filename:
                return report_type
        return 'Unknown'
    
    def parse_average_filename(self, filename):
        """
        Parse averaged filename to extract: report_type, router, value, grouping_type
        Example: MessageStatsReport_EpidemicRouter_10_ttl_average.txt
        Returns: {report_type, router, value, grouping_type}
        """
        # Remove extension and _average suffix
        name = filename.replace('_average.txt', '').replace('_average', '')
        parts = name.split(self.config['filename_structure']['delimiter'])
        
        if len(parts) < 3:
            return None
        
        # Extract components based on positions
        positions = self.config['filename_structure']['average_files']
        
        try:
            parsed = {
                'report_type': parts[positions['report_type_position']],
                'router': parts[positions['router_position']],
                'filename': filename,
                'source_report': self.get_report_type(filename)
            }
            
            # The grouping type is the word before "average" (e.g., "ttl" or "buffer")
            grouping_pos = positions['grouping_type_position']
            grouping_type = parts[grouping_pos] if -grouping_pos <= len(parts) else 'unknown'
            parsed['grouping_type'] = grouping_type
            
            # CRITICAL FIX: Extract the value from the position BEFORE the grouping type
            # For "Router_2_buffer_average": parts = [Report, Router, 2, buffer]
            # grouping_pos = -1 (buffer), so value is at -2 (which is 2)
            value_pos = grouping_pos - 1  # One position before the grouping type
            
            try:
                parsed['value'] = float(parts[value_pos])
            except (ValueError, IndexError):
                # Fallback: try the configured positions
                value_positions = positions.get('value_positions', [2])
                for pos in value_positions:
                    if pos < len(parts):
                        try:
                            parsed['value'] = float(parts[pos])
                            break
                        except ValueError:
                            parsed['value'] = parts[pos]
            
            return parsed
        except (IndexError, KeyError) as e:
            return None
    
    def parse_raw_filename(self, filename):
        """
        Parse raw report filename
        Example: TEST_EpidemicRouter_12_300_5M_MessageStatsReport.txt
        """
        name = filename.rsplit('.', 1)[0]
        parts = name.split(self.config['filename_structure']['delimiter'])
        
        positions = self.config['filename_structure']['raw_files']['positions']
        
        try:
            parsed = {
                'filename': filename,
                'source_report': self.get_report_type(filename)
            }
            
            for component, pos in positions.items():
                if pos < len(parts):
                    value = parts[pos]
                    # Try to extract numbers
                    match = re.search(r'(\d+)', value)
                    if match:
                        try:
                            parsed[component] = int(match.group(1))
                        except:
                            parsed[component] = value
                    else:
                        parsed[component] = value
            
            return parsed
        except Exception as e:
            print(f"  Warning: Could not parse raw file {filename}: {e}")
            return None
    
    def read_metrics(self, filepath):
        """Read metrics from a report file"""
        data = {}
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    if self.separator not in line:
                        continue
                    
                    field, value = line.strip().split(self.separator, 1)
                    field = field.strip()
                    value = value.strip()
                    
                    if field in self.ignore_fields:
                        continue
                    
                    if field in self.metrics:
                        try:
                            data[field] = float(value) if value.lower() != 'nan' else np.nan
                        except ValueError:
                            pass
            return data
        except Exception as e:
            print(f"  Error reading {filepath}: {e}")
            return {}

class DataOrganizer:
    """Organize data for different visualization purposes"""
    
    def __init__(self, parser):
        self.parser = parser
        self.report_dir = parser.report_dir
    
    def load_averaged_files(self):
        """
        Load averaged files and organize by grouping type
        Merges data from multiple report types based on router, grouping_type, and value
        Returns: dict of {grouping_type: DataFrame}
        """
        print("\n" + "="*70)
        print("LOADING AVERAGED FILES")
        print("="*70)
        
        grouped_averages = defaultdict(lambda: defaultdict(list))
        total_files = 0
        report_type_counts = defaultdict(int)
        
        for filename in os.listdir(self.report_dir):
            if not self.parser.is_average_file(filename):
                continue
            
            parsed = self.parser.parse_average_filename(filename)
            if parsed is None:
                continue
            
            filepath = os.path.join(self.report_dir, filename)
            metrics = self.parser.read_metrics(filepath)
            
            if metrics:
                # Create unique key for merging: (router, grouping_type, value)
                merge_key = (parsed['router'], parsed['grouping_type'], parsed['value'])
                
                # Add source report type for tracking
                report_type_counts[parsed['source_report']] += 1
                
                # Store metrics with merge key
                grouped_averages[parsed['grouping_type']][merge_key].append({
                    **parsed,
                    **metrics,
                    'merge_key': merge_key
                })
                total_files += 1
        
        print(f"Loaded {total_files} averaged files")
        print(f"Report types: {dict(report_type_counts)}")
        
        # Convert to DataFrames and merge data with same keys
        dataframes = {}
        for grouping_type, merge_data in grouped_averages.items():
            merged_records = []
            
            for merge_key, records in merge_data.items():
                # Merge all metrics from different report types with same key
                merged_record = {
                    'router': merge_key[0],
                    'grouping_type': merge_key[1],
                    'value': merge_key[2]
                }
                
                # Collect report_type and filename info
                report_types = []
                filenames = []
                
                for record in records:
                    # Merge all metrics
                    for key, value in record.items():
                        if key not in ['router', 'grouping_type', 'value', 'merge_key', 
                                      'source_report', 'filename', 'report_type']:
                            merged_record[key] = value
                    
                    if 'source_report' in record:
                        report_types.append(record['source_report'])
                    if 'filename' in record:
                        filenames.append(record['filename'])
                
                merged_record['source_reports'] = ','.join(set(report_types))
                merged_record['filenames'] = ','.join(filenames)
                merged_records.append(merged_record)
            
            if merged_records:
                df = pd.DataFrame(merged_records)
                dataframes[grouping_type] = df
                
                # Show what was merged
                sources = df['source_reports'].iloc[0] if 'source_reports' in df.columns else 'Unknown'
                unique_routers = df['router'].unique().tolist()
                print(f"  {grouping_type}: {len(df)} records, {df['value'].nunique()} unique values")
                print(f"    Routers: {', '.join(unique_routers)}")
                print(f"    Merged from: {sources}")
        
        return dataframes
    
    def load_raw_files(self):
        """
        Load raw (non-averaged) files
        Merges data from multiple report types based on common keys
        """
        print("\n" + "="*70)
        print("LOADING RAW FILES")
        print("="*70)
        
        # Group by common identifier (router, seed, etc.)
        grouped_raw = defaultdict(list)
        report_type_counts = defaultdict(int)
        
        for filename in os.listdir(self.report_dir):
            if self.parser.is_average_file(filename):
                continue
            
            if not filename.endswith(self.parser.config['file_patterns']['report_extension']):
                continue
            
            parsed = self.parser.parse_raw_filename(filename)
            if parsed is None:
                continue
            
            filepath = os.path.join(self.report_dir, filename)
            metrics = self.parser.read_metrics(filepath)
            
            if metrics:
                parsed.update(metrics)
                report_type_counts[parsed['source_report']] += 1
                
                # Create merge key from common identifiers
                # Typically: router + seed (or other unique run identifier)
                key_parts = []
                for field in ['router', 'seed', 'ttl', 'buffer']:
                    if field in parsed:
                        key_parts.append(str(parsed[field]))
                
                merge_key = '_'.join(key_parts) if key_parts else filename
                grouped_raw[merge_key].append(parsed)
        
        # Merge records with same keys
        merged_records = []
        for merge_key, records in grouped_raw.items():
            merged = {}
            
            for record in records:
                merged.update(record)
            
            merged_records.append(merged)
        
        if merged_records:
            df = pd.DataFrame(merged_records)
            print(f"Loaded {len(df)} raw files")
            print(f"Report types: {dict(report_type_counts)}")
            if 'router' in df.columns:
                print(f"Routers: {', '.join(df['router'].unique().tolist())}")
            return df
        
        print("No raw files found")
        return None

class PlotStrategy:
    """Determine what plots to generate based on available data"""
    
    def __init__(self, config):
        self.config = config
        self.thresholds = config['plot_thresholds']
    
    def analyze_averaged_data(self, averaged_dfs):
        """Determine plot strategy for averaged data"""
        strategy = {
            'line_plots': [],      # List of (grouping_type, df)
            'surface_plots': []    # List of ((grouping_type1, grouping_type2), (df1, df2))
        }
        
        # Line plots: one per grouping type with enough variation
        for grouping_type, df in averaged_dfs.items():
            if df['value'].nunique() >= self.thresholds['min_values_for_line']:
                strategy['line_plots'].append((grouping_type, df))
        
        # Surface plots: pairs of grouping types with enough points
        suitable_for_surface = []
        for grouping_type, df in averaged_dfs.items():
            if df['value'].nunique() >= self.thresholds['min_values_for_surface']:
                suitable_for_surface.append((grouping_type, df))
        
        # Create pairs for surface plots
        if len(suitable_for_surface) >= 2:
            for i in range(len(suitable_for_surface)):
                for j in range(i + 1, len(suitable_for_surface)):
                    type1, df1 = suitable_for_surface[i]
                    type2, df2 = suitable_for_surface[j]
                    strategy['surface_plots'].append(((type1, type2), (df1, df2)))
        
        return strategy

class PlotGenerator:
    """Generate all visualization types"""
    
    def __init__(self, config, output_dir):
        self.config = config
        self.output_dir = output_dir
        self.metrics = config['metrics']['include']
        self.grouping_labels = config.get('grouping_labels', {})
    
    def get_axis_label(self, grouping_type):
        """Get proper axis label for a grouping type"""
        return self.grouping_labels.get(grouping_type, grouping_type.replace('_', ' ').title())
    
    def create_line_plot(self, job_data):
        """Create line plot from averaged data"""
        try:
            grouping_type, df, metric, settings = job_data
            
            fig, ax = plt.subplots(figsize=tuple(settings['size']))
            
            # Get marker styles and colors
            marker_styles = settings['markers']
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
            
            plotted_routers = []
            for i, router in enumerate(sorted(df['router'].unique())):  # Sort for consistency
                router_df = df[df['router'] == router].sort_values('value')
                
                # Check if metric exists and has valid data
                if not router_df.empty and metric in router_df.columns:
                    # Remove NaN values
                    router_df_clean = router_df.dropna(subset=[metric, 'value'])
                    
                    if len(router_df_clean) > 0:
                        ax.plot(router_df_clean['value'], router_df_clean[metric],
                               marker=marker_styles[i % len(marker_styles)],
                               markersize=settings['marker_size'],
                               markeredgewidth=2,
                               markeredgecolor='white',
                               color=colors[i % len(colors)],
                               label=router, 
                               linestyle='-',
                               linewidth=2.5,
                               zorder=3,  # Ensure markers are on top
                               alpha=0.9)
                        plotted_routers.append(router)
            
            if not plotted_routers:
                plt.close(fig)
                return False
            
            x_label = self.get_axis_label(grouping_type)
            ax.set_xlabel(x_label, fontsize=settings['font_sizes']['axis_label'])
            ax.set_ylabel(metric.replace('_', ' ').title(),
                         fontsize=settings['font_sizes']['axis_label'])
            ax.grid(True, linestyle='--', alpha=0.4, zorder=0)  # Grid behind everything
            
            # Create legend with proper styling
            legend = ax.legend(title='Router', 
                              fontsize=settings['font_sizes']['legend'],
                              title_fontsize=settings['font_sizes']['legend'],
                              loc='best',
                              framealpha=0.95,
                              edgecolor='black')
            
            ax.tick_params(axis='both', labelsize=settings['font_sizes']['ticks'])
            
            output_path = os.path.join(self.output_dir, f"{metric}_{grouping_type}_line.png")
            fig.tight_layout()
            fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            
            print(f"  ✓ Line: {metric} vs {x_label}")
            return True
        except Exception as e:
            print(f"  ✗ Line plot failed: {e}")
            import traceback
            traceback.print_exc()
            plt.close('all')
            return False
    
    def create_surface_plot(self, job_data):
        """Create 3D surface plot from two averaged datasets"""
        try:
            grouping_types, dfs, metric, settings = job_data
            type1, type2 = grouping_types
            df1, df2 = dfs
            
            # Find common routers
            routers = set(df1['router'].unique()) & set(df2['router'].unique())
            
            for router in routers:
                r_df1 = df1[df1['router'] == router]
                r_df2 = df2[df2['router'] == router]
                
                if r_df1.empty or r_df2.empty or metric not in r_df1.columns or metric not in r_df2.columns:
                    continue
                
                # Create pivot table
                vals1 = sorted(r_df1['value'].unique())
                vals2 = sorted(r_df2['value'].unique())
                
                if len(vals1) < 2 or len(vals2) < 2:
                    continue
                
                X, Y = np.meshgrid(vals1, vals2)
                Z = np.zeros((len(vals2), len(vals1)))
                
                # Fill Z matrix
                for i, v2 in enumerate(vals2):
                    for j, v1 in enumerate(vals1):
                        val1 = r_df1[r_df1['value'] == v1][metric].values
                        val2 = r_df2[r_df2['value'] == v2][metric].values
                        if len(val1) > 0 and len(val2) > 0:
                            Z[i, j] = (val1[0] + val2[0]) / 2
                
                # Handle NaN values
                if np.isnan(Z).any():
                    Z = np.nan_to_num(Z, nan=np.nanmean(Z[~np.isnan(Z)]))
                
                fig = plt.figure(figsize=tuple(settings['size']))
                ax = fig.add_subplot(111, projection='3d')
                
                surf = ax.plot_surface(X, Y, Z,
                                      cmap=settings['style']['cmap'],
                                      edgecolor=settings['style']['edge_color'],
                                      linewidth=settings['style']['line_width'],
                                      alpha=settings['style']['alpha'])
                
                x_label = self.get_axis_label(type1)
                y_label = self.get_axis_label(type2)
                
                ax.set_xlabel(x_label, labelpad=20, fontsize=settings['font_sizes']['axis_label'])
                ax.set_ylabel(y_label, labelpad=20, fontsize=settings['font_sizes']['axis_label'])
                ax.set_zlabel(metric.replace('_', ' ').title(), labelpad=40,
                            fontsize=settings['font_sizes']['axis_label'])
                
                ax.tick_params(axis='x', labelsize=settings['font_sizes']['ticks'])
                ax.tick_params(axis='y', labelsize=settings['font_sizes']['ticks'])
                ax.tick_params(axis='z', labelsize=settings['font_sizes']['ticks'])
                
                ax.view_init(elev=settings['view']['elev'], azim=settings['view']['azim'])
                
                cbar = fig.colorbar(surf, ax=ax, shrink=0.8, aspect=18, pad=0.1)
                cbar.ax.tick_params(labelsize=settings['font_sizes']['colorbar'])
                
                output_path = os.path.join(self.output_dir, f"{router}_{metric}_3d_{type1}_{type2}.png")
                fig.tight_layout()
                fig.savefig(output_path, dpi=300, bbox_inches='tight')
                plt.close(fig)
                
                print(f"  ✓ Surface: {router} {metric} ({x_label} vs {y_label})")
            
            return True
        except Exception as e:
            print(f"  ✗ Surface plot failed: {e}")
            plt.close('all')
            return False
    
    def create_violin_plot(self, job_data):
        """Create violin plot from averaged data"""
        try:
            grouping_type, df, metric, settings = job_data
            
            if 'router' not in df.columns or metric not in df.columns:
                return False
            
            fig, ax = plt.subplots(figsize=tuple(settings['size']))
            
            sns.violinplot(data=df, x=metric, y='router',
                          hue='router',
                          palette=settings['style']['palette'],
                          inner=settings['style']['inner'],
                          linewidth=settings['style']['line_width'],
                          width=settings['style']['width'],
                          legend=False,
                          ax=ax)
            
            # Style quartile lines
            for line in ax.lines:
                line.set_color('black')
                line.set_linewidth(settings['style']['quartile_line_width'])
            
            ax.set_xlabel(metric.replace('_', ' ').title(),
                         fontsize=settings['font_sizes']['axis_label'])
            ax.set_ylabel('Router', fontsize=settings['font_sizes']['axis_label'])
            ax.tick_params(axis='both', labelsize=settings['font_sizes']['ticks'])
            ax.grid(False)
            
            output_path = os.path.join(self.output_dir, f"violin_{grouping_type}_{metric}.png")
            fig.tight_layout()
            fig.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            
            print(f"  ✓ Violin: {metric} ({grouping_type})")
            return True
        except Exception as e:
            print(f"  ✗ Violin plot failed: {e}")
            plt.close('all')
            return False
    
    def create_heatmap(self, job_data):
        """Create correlation heatmap from raw data"""
        try:
            router, router_df, metrics, output_dir, settings = job_data
            
            if router_df.shape[0] < 2:
                return False
            
            fig, ax = plt.subplots(figsize=((len(metrics)*2.5)+2, len(metrics)*2.5))
            corr = router_df[metrics].corr()
            
            im = sns.heatmap(corr, annot=True, cmap=settings['style']['cmap'],
                       vmin=settings['style']['vmin'], vmax=settings['style']['vmax'],
                       annot_kws={"size": settings['font_sizes']['annotations']},
                       ax=ax)
            
            # Title the colorbar (label it 'Correlation')
            cbar = ax.collections[0].colorbar
            cbar.set_label('Correlation', fontsize=settings['font_sizes']['colorbar'],
                           rotation=270, labelpad=12)
            cbar.ax.tick_params(labelsize=settings['font_sizes']['colorbar'])
            ax.tick_params(axis='both', labelsize=settings['font_sizes']['ticks'])
            
            output_path = os.path.join(output_dir, f"{router}_correlation.png")
            fig.tight_layout()
            fig.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            
            print(f"  ✓ Heatmap: {router}")
            return True
        except Exception as e:
            print(f"  ✗ Heatmap failed: {e}")
            plt.close('all')
            return False
    
    def create_pairplot(self, job_data):
        """Create pairplot from raw data"""
        try:
            df, metrics, output_dir, settings = job_data
            
            if 'router' not in df.columns:
                return False
            
            plot_cols = [m for m in metrics if m in df.columns] + ['router']
            
            g = sns.pairplot(df[plot_cols], hue='router',
                           diag_kind=settings['style']['diag_kind'],
                           palette=settings['style']['palette'],
                           plot_kws={'alpha': settings['style']['alpha'],
                                   's': settings['style']['marker_size']})
            
            for ax in g.axes.flatten():
                if ax is not None:
                    ax.tick_params(labelsize=settings['font_sizes']['ticks'])
                    ax.grid(False)
            
            output_path = os.path.join(output_dir, "pairplot.png")
            g.fig.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close(g.fig)
            
            print(f"  ✓ Pairplot")
            return True
        except Exception as e:
            print(f"  ✗ Pairplot failed: {e}")
            plt.close('all')
            return False

def execute_plot_job(job_info):
    """Dispatcher for multiprocessing"""
    job_type, job_data, generator = job_info
    
    try:
        if job_type == 'line':
            return generator.create_line_plot(job_data)
        elif job_type == 'surface':
            return generator.create_surface_plot(job_data)
        elif job_type == 'violin':
            return generator.create_violin_plot(job_data)
        elif job_type == 'heatmap':
            return generator.create_heatmap(job_data)
        elif job_type == 'pairplot':
            return generator.create_pairplot(job_data)
    except Exception as e:
        print(f"Error in plot job: {e}")
        traceback.print_exc()
        return False

def main():
    # Load configuration
    if len(sys.argv) > 1:
        config = load_config(sys.argv[1])
    else:
        config = load_config()
    
    print("="*70)
    print("SMART ADAPTIVE ANALYSIS TOOL")
    print("="*70)
    
    # Setup
    parser = SmartFileParser(config)
    organizer = DataOrganizer(parser)
    strategy_analyzer = PlotStrategy(config)
    
    plots_dir = config['directories']['plots_dir']
    os.makedirs(plots_dir, exist_ok=True)
    
    # Load data
    averaged_dfs = organizer.load_averaged_files()
    raw_df = organizer.load_raw_files()
    
    # Analyze and determine strategy
    print("\n" + "="*70)
    print("ANALYZING DATA")
    print("="*70)
    
    avg_strategy = strategy_analyzer.analyze_averaged_data(averaged_dfs)
    
    print(f"Line plots: {len(avg_strategy['line_plots'])} grouping types")
    print(f"Surface plots: {len(avg_strategy['surface_plots'])} combinations")
    print(f"Violin plots: {len(avg_strategy['line_plots'])} grouping types")
    if raw_df is not None:
        print(f"Heatmaps: {len(raw_df['router'].unique()) if 'router' in raw_df.columns else 0} routers")
        print(f"Pairplot: 1")
        print(f"CSV exports: {len(raw_df['router'].unique()) if 'router' in raw_df.columns else 0} routers")
    
    # Queue plot jobs
    plot_jobs = []
    plot_gen = PlotGenerator(config, plots_dir)
    
    # Line plots from averaged data
    if config['enabled_plots']['line_plots']:
        for grouping_type, df in avg_strategy['line_plots']:
            for metric in config['metrics']['include']:
                if metric in df.columns:
                    job = ('line', (grouping_type, df, metric, config['plot_settings']['line_plots']), plot_gen)
                    plot_jobs.append(job)
    
    # Surface plots from averaged data
    if config['enabled_plots']['3d_surface']:
        for grouping_types, dfs in avg_strategy['surface_plots']:
            for metric in config['metrics']['include']:
                job = ('surface', (grouping_types, dfs, metric, config['plot_settings']['3d_surface']), plot_gen)
                plot_jobs.append(job)
    
    # Violin plots from averaged data (one per grouping type)
    if config['enabled_plots']['violin_plots']:
        for grouping_type, df in avg_strategy['line_plots']:
            for metric in config['metrics']['include']:
                if metric in df.columns:
                    job = ('violin', (grouping_type, df, metric, config['plot_settings']['violin_plots']), plot_gen)
                    plot_jobs.append(job)
    
    # Heatmaps from raw data
    if config['enabled_plots']['heatmaps'] and raw_df is not None and 'router' in raw_df.columns:
        for router in raw_df['router'].unique():
            router_df = raw_df[raw_df['router'] == router]
            job = ('heatmap', (router, router_df, config['metrics']['include'], plots_dir, config['plot_settings']['heatmaps']), plot_gen)
            plot_jobs.append(job)
    
    # Pairplot from raw data
    if config['enabled_plots']['pairplot'] and raw_df is not None:
        job = ('pairplot', (raw_df, config['metrics']['include'], plots_dir, config['plot_settings']['pairplot']), plot_gen)
        plot_jobs.append(job)
    
    # Execute plots
    print("\n" + "="*70)
    print(f"GENERATING VISUALIZATIONS")
    print("="*70)
    
    if plot_jobs:
        print(f"Processing {len(plot_jobs)} plots...")
        start_time = time.time()
        
        # Dynamic worker calculation using ResourceManager
        if RESOURCE_MANAGER_AVAILABLE:
            rm = ResourceManager(safety_enabled=True)
            num_processes = min(rm.get_optimal_workers(), len(plot_jobs))
            rm.log_status()
        else:
            num_processes = min(4, len(plot_jobs))
        
        with Pool(processes=num_processes) as pool:
            results = pool.map(execute_plot_job, plot_jobs)
        
        successful = sum(1 for r in results if r)
        elapsed = time.time() - start_time
        
        print(f"Completed {successful}/{len(plot_jobs)} plots in {elapsed:.2f}s")
    
    # Export CSV from raw data
    if config['enabled_plots']['export_csv'] and raw_df is not None and 'router' in raw_df.columns:
        print("\n" + "="*70)
        print("EXPORTING DATA")
        print("="*70)
        for router in raw_df['router'].unique():
            router_df = raw_df[raw_df['router'] == router]
            csv_path = os.path.join(plots_dir, f"{router}_metrics.csv")
            router_df.to_csv(csv_path, index=False)
            print(f"Exported: {router}_metrics.csv")
    
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)

if __name__ == '__main__':
    main()