import os
import json
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Sklearn Imports
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.tree import DecisionTreeRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Cross-platform path resolution
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONFIG_DIR = PROJECT_ROOT / 'config'

# ---------------------------------------------------------
# UTILS
# ---------------------------------------------------------
def load_config(path=None):
    """Load configuration (cross-platform)"""
    if path is None:
        path = CONFIG_DIR / "regression_config.json"
    else:
        path = Path(path)
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)

# ---------------------------------------------------------
# DATA PIPELINE (Suggestion 3: Pipelines)
# ---------------------------------------------------------
class DataProcessor:
    def __init__(self, config):
        self.config = config
        
    def get_files(self):
        """Find CSV files based on config mode"""
        csv_dir = self.config['input']['csv_directory']
        if not os.path.exists(csv_dir):
            print(f"Directory '{csv_dir}' not found.")
            return []
            
        files = [f for f in os.listdir(csv_dir) if f.endswith('_metrics.csv')]
        
        mode = self.config['input'].get('mode', 'all')
        if mode == 'selected':
            selected = self.config['input'].get('active_files', [])
            files = [f for f in files if f in selected]
            
        return [os.path.join(csv_dir, f) for f in files]

    def load_and_clean(self, filepath):
        """Load data and return X, y (Unscaled - Scaling happens in Pipeline)"""
        try:
            df = pd.read_csv(filepath)
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            return None, None, None

        feat_config = self.config['features']
        target = feat_config['target']
        
        if target not in df.columns:
            return None, None, None

        # 1. Basic Cleaning (NaN/Inf removal)
        df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=[target])
        
        # 2. Feature Selection
        all_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if feat_config['selection_mode'] == 'auto':
            predictors = [c for c in all_cols if c != target]
        elif feat_config['selection_mode'] == 'exclude':
            exclude = feat_config.get('exclude', []) + [target]
            predictors = [c for c in all_cols if c not in exclude]
        else: 
            desired = feat_config['predictors']
            predictors = [c for c in desired if c in df.columns and c != target]

        if not predictors:
            return None, None, None

        # 3. Final Clean
        data = df[predictors + [target]].replace([np.inf, -np.inf], np.nan).dropna()
        
        if len(data) == 0:
            return None, None, None

        X = data[predictors]
        y = data[target]
        
        return X, y, predictors

def create_pipeline(base_model, config):
    """
    Builds a robust Sklearn Pipeline:
    Scaler -> Polynomials (Optional) -> Model
    """
    steps = []
    
    # Step 1: Scaling (If enabled)
    if config['features'].get('normalize', False):
        steps.append(('scaler', StandardScaler()))
        
    # Step 2: Interaction/Polynomial Features (Suggestion 2)
    poly_cfg = config['features'].get('polynomial_features', {})
    if poly_cfg.get('enabled', False):
        steps.append(('poly', PolynomialFeatures(
            degree=poly_cfg.get('degree', 2),
            interaction_only=poly_cfg.get('interaction_only', False),
            include_bias=poly_cfg.get('include_bias', False)
        )))
        
    # Step 3: The Estimator
    steps.append(('model', base_model))
    
    return Pipeline(steps)

# ---------------------------------------------------------
# MODEL FACTORY
# ---------------------------------------------------------
def get_base_models(config):
    """Instantiate base models (without pipeline wrappers)"""
    settings = config['model_settings']
    enabled = settings['enabled_models']
    params = settings['parameters']
    
    models = {}
    rand_state = settings['split_settings']['random_state']
    
    if enabled.get("Linear Regression"):
        models["Linear Regression"] = LinearRegression()
    if enabled.get("Ridge Regression"):
        models["Ridge Regression"] = Ridge(**params.get("Ridge Regression", {}))
    if enabled.get("Lasso Regression"):
        models["Lasso Regression"] = Lasso(**params.get("Lasso Regression", {}))
    if enabled.get("Decision Tree"):
        models["Decision Tree"] = DecisionTreeRegressor(random_state=rand_state, **params.get("Decision Tree", {}))
    if enabled.get("Random Forest"):
        models["Random Forest"] = RandomForestRegressor(random_state=rand_state, **params.get("Random Forest", {}))
    if enabled.get("Gradient Boosting"):
        models["Gradient Boosting"] = GradientBoostingRegressor(random_state=rand_state, **params.get("Gradient Boosting", {}))
    if enabled.get("KNN"):
        models["KNN"] = KNeighborsRegressor(**params.get("KNN", {}))
        
    return models

# ---------------------------------------------------------
# VISUALIZATION
# ---------------------------------------------------------
def plot_results(y_test, y_pred, model_name, router, out_dir, config):
    """Standardized plotting function with style injection"""
    styles = config['plot_settings']['styles']
    fig_size = tuple(config['plot_settings']['figure']['size'])
    dpi_val = config['plot_settings']['figure']['dpi']
    
    # Safety cleaning
    y_test_arr = np.array(y_test)
    y_pred_arr = np.array(y_pred)
    mask = np.isfinite(y_pred_arr) & np.isfinite(y_test_arr)
    y_test_clean = y_test_arr[mask]
    y_pred_clean = y_pred_arr[mask]
    
    if len(y_test_clean) == 0: return

    fig, axes = plt.subplots(1, 3, figsize=fig_size)
    
    def apply_grid(ax):
        ax.grid(True, linestyle=styles['grid']['style'], linewidth=styles['grid']['width'], alpha=styles['grid']['alpha'])
        ax.tick_params(axis='both', labelsize=styles['fonts']['tick_label'])

    # 1. Residual Scatter
    residuals = y_test_clean - y_pred_clean
    sns.scatterplot(x=y_pred_clean, y=residuals, ax=axes[0], 
                    color=styles['colors']['residual_scatter'], edgecolor=styles['colors']['edge'], 
                    s=styles['scatter']['s'], alpha=styles['scatter']['alpha'])
    axes[0].axhline(0, color=styles['colors']['line'], linestyle='--', linewidth=2)
    axes[0].set_xlabel("Predicted Values", fontsize=styles['fonts']['axis_label'])
    axes[0].set_ylabel("Residuals", fontsize=styles['fonts']['axis_label'])
    apply_grid(axes[0])

    # 2. Actual vs Predicted
    sns.scatterplot(x=y_test_clean, y=y_pred_clean, ax=axes[1],
                    color=styles['colors']['actual_predicted'], edgecolor=styles['colors']['edge'],
                    s=styles['scatter']['s'], alpha=styles['scatter']['alpha'])
    
    if len(y_test_clean) > 1:
        min_v = max(-1e9, min(y_test_clean.min(), y_pred_clean.min()))
        max_v = min(1e9, max(y_test_clean.max(), y_pred_clean.max()))
        axes[1].plot([min_v, max_v], [min_v, max_v], color=styles['colors']['line'], linestyle='--', linewidth=2, label="Ideal")

    axes[1].set_xlabel("Actual Values", fontsize=styles['fonts']['axis_label'])
    axes[1].set_ylabel("Predicted Values", fontsize=styles['fonts']['axis_label'])
    axes[1].legend(fontsize=styles['fonts']['legend'])
    apply_grid(axes[1])

    # 3. Histogram
    p01, p99 = np.percentile(residuals, [1, 99])
    res_clip = residuals[(residuals >= p01) & (residuals <= p99)]
    if len(res_clip) == 0: res_clip = residuals

    try:
        sns.histplot(res_clip, kde=True, bins=30, ax=axes[2],
                     color=styles['colors']['residual_hist'], edgecolor="black", alpha=0.85)
        for artist in axes[2].lines: artist.set_color("black")
    except: pass

    axes[2].set_xlabel("Residuals", fontsize=styles['fonts']['axis_label'])
    apply_grid(axes[2])

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    save_path = os.path.join(out_dir, router)
    os.makedirs(save_path, exist_ok=True)
    plt.savefig(os.path.join(save_path, f"{model_name.replace(' ','_').lower()}_analysis.png"), 
                dpi=dpi_val, bbox_inches='tight', facecolor='white')
    plt.close()

def plot_importance(pipeline, feature_names_in, model_name, router, out_dir, config):
    """Extract feature names from pipeline (handling polynomials) and plot"""
    # Access the actual model step
    if 'model' not in pipeline.named_steps: return
    model = pipeline.named_steps['model']
    
    if not hasattr(model, 'feature_importances_'): return

    # Handle feature name transformation (if Polynomials exist)
    final_feature_names = feature_names_in
    if 'poly' in pipeline.named_steps:
        poly = pipeline.named_steps['poly']
        try:
            final_feature_names = poly.get_feature_names_out(feature_names_in)
        except:
            final_feature_names = [f"Feat_{i}" for i in range(model.n_features_in_)]

    # Sort top 15 features to keep plot readable (Polynomials create MANY features)
    importances = pd.Series(model.feature_importances_, index=final_feature_names)
    top_importances = importances.sort_values(ascending=False).head(15)
    
    styles = config['plot_settings']['styles']
    dpi_val = config['plot_settings']['figure']['dpi']

    plt.figure(figsize=(10, max(6, len(top_importances)*0.4)))
    top_importances.sort_values().plot(kind='barh', color='#4c72b0')
    
    plt.title(f'{model_name} Top 15 Features', fontsize=styles['fonts']['title'])
    plt.xlabel("Importance", fontsize=styles['fonts']['axis_label'])
    plt.tick_params(axis='both', labelsize=styles['fonts']['tick_label'])
    plt.grid(True, linestyle=styles['grid']['style'], alpha=0.3)
    plt.tight_layout()
    
    save_path = os.path.join(out_dir, router)
    os.makedirs(save_path, exist_ok=True)
    plt.savefig(os.path.join(save_path, f"{model_name.replace(' ','_').lower()}_importance.png"), 
                dpi=dpi_val, bbox_inches='tight')
    plt.close()

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
if __name__ == "__main__":
    config = load_config()
    processor = DataProcessor(config)
    
    files = processor.get_files()
    if not files:
        print("No CSV files found.")
        sys.exit(0)
        
    out_dir = config['output']['directory']
    os.makedirs(out_dir, exist_ok=True)
    
    print(f"Found {len(files)} datasets. Starting Analysis...")
    
    for filepath in files:
        router_name = os.path.basename(filepath).replace("_metrics.csv", "")
        print(f"\n{'='*40}\nAnalyzing: {router_name}\n{'='*40}")
        
        X, y, predictors = processor.load_and_clean(filepath)
        
        if X is None:
            print("Skipping: Invalid data.")
            continue
            
        # Config Checks
        poly_enabled = config['features'].get('polynomial_features', {}).get('enabled', False)
        if poly_enabled:
            print(f"Feature Mode: Polynomial Interactions (Degree {config['features']['polynomial_features']['degree']})")
        else:
            print("Feature Mode: Standard")

        # Split Data
        split_cfg = config['model_settings']['split_settings']
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, 
            train_size=split_cfg['train_size'],
            random_state=split_cfg['random_state']
        )
        
        base_models = get_base_models(config)
        results = []
        
        cv_config = config['model_settings'].get('cross_validation', {})
        cv_enabled = cv_config.get('enabled', False)
        
        for name, base_model in base_models.items():
            print(f"--> Processing {name}...")
            
            # Create Pipeline (Suggestion 3)
            pipeline = create_pipeline(base_model, config)
            
            try:
                # 1. Cross-Validation (Suggestion 4)
                cv_score_str = "N/A"
                if cv_enabled:
                    folds = cv_config.get('folds', 5)
                    # Note: Pipeline handles scaling for each fold automatically
                    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=folds, scoring='r2')
                    cv_mean = cv_scores.mean()
                    cv_std = cv_scores.std()
                    cv_score_str = f"{cv_mean:.4f} (±{cv_std*2:.4f})"
                    print(f"    CV Score (R²): {cv_score_str}")
                
                # 2. Final Fit on Training Data
                pipeline.fit(X_train, y_train)
                
                # 3. Evaluation on Test Data
                y_pred = pipeline.predict(X_test)
                
                # Handle Infinite Preds
                mask = np.isfinite(y_pred)
                if not mask.all():
                    y_pred[~mask] = np.mean(y_train)
                
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                mae = mean_absolute_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                
                results.append({
                    "Model": name,
                    "CV R2 (Mean)": cv_score_str,
                    "Test R2": r2,
                    "Test RMSE": rmse,
                    "Test MAE": mae
                })
                
                # 4. Plots
                plot_results(y_test, y_pred, name, router_name, out_dir, config)
                plot_importance(pipeline, predictors, name, router_name, out_dir, config)
                
            except Exception as e:
                print(f"    Error: {e}")
                # import traceback
                # traceback.print_exc()
                
        # Summary
        if results:
            res_df = pd.DataFrame(results).sort_values("Test R2", ascending=False)
            print("\nPerformance Summary:")
            print(res_df[['Model', 'CV R2 (Mean)', 'Test R2', 'Test RMSE']])
            res_df.to_csv(os.path.join(out_dir, router_name, "performance_summary.csv"), index=False)
            
    print(f"\nAnalysis complete. Check '{out_dir}' for results.")