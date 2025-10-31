"""
Module to run the PCA analysis as a whole. Outputs are shown in the results folder
This is the PCA code modified for a Flask web app - all GUI code removed, matplotlib backend set to Agg
MEMORY OPTIMIZED VERSION with diagnostics and aggressive cleanup
"""

import sys
import os
# CRITICAL: Set matplotlib backend BEFORE any other matplotlib imports
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest
import numpy as np
from typing import Dict
from datetime import datetime
from pca import pca
from matplotlib.backends.backend_pdf import PdfPages
from factor_analyzer.rotator import Rotator 
import gc
import psutil

# Ensure pyplot is also using Agg backend
plt.ioff()  # Turn off interactive mode

# Custom Exceptions for clear error feedback
class DataProcessingError(Exception):
    """Custom exception for errors during data loading and cleaning."""
    pass

class PCACalculationError(Exception):
    """Custom exception for errors during the PCA computation."""
    pass

class PCAAnalysisPipeline:
    def __init__(self, csv_file: str, rotation_option: str, results_dir: str = "results") -> None:
        self.csv_file = csv_file
        self.raw_df = None
        self.numeric_df = None
        self.pca_model = None
        self.pca_results = {}
        self.n_components = None
        self.loadings = None
        self.loadings_path = None
        self.pdf_path = None
        self.rotation_method = rotation_option

        # Setup results directory
        self.results_dir = results_dir
        os.makedirs(self.results_dir, exist_ok=True)

        # Log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(self.results_dir, f"results_{timestamp}.txt")

        self.timestamp = timestamp

    def _log(self, text: str) -> None:
        """Write message to console and log file."""
        print(text)
        try:
            with open(self.log_file, "a", encoding='utf-8') as f:
                f.write(text + "\n")
        except Exception as e:
            print(f"Warning: Could not write to log file: {e}")

    def create_numeric_df(self) -> pd.DataFrame:

        def _remove_outliers_iforest(df: pd.DataFrame, contamination=0.05):
            iso = IsolationForest(contamination=contamination, random_state=42)
            mask = iso.fit_predict(df) != -1
            print(f"Removed {len(df) - np.sum(mask)} outliers (kept {np.sum(mask)})")
            return df[mask]
                
        """Load CSV file and convert to numeric DataFrame with preprocessing."""
        
        try:
            # Log file size
            file_size_mb = os.path.getsize(self.csv_file) / (1024 * 1024)
            self._log(f"CSV file size: {file_size_mb:.2f} MB")            
            self.raw_df = pd.read_csv(self.csv_file)
        except FileNotFoundError:
            raise DataProcessingError(f"Could not find the uploaded file for processing.")
        except Exception as e:
            raise DataProcessingError(f"Failed to read the CSV file. It might be malformed. Original error: {e}")

        try:            
            # Convert everything possible to numeric
            self.numeric_df = self.raw_df.apply(pd.to_numeric, errors="coerce")

            # Drop columns/rows that are completely empty
            self.numeric_df = self.numeric_df.dropna(axis=1, how="all").dropna(axis=0, how="all")

            # Check if dataframe is empty after dropping NaNs
            if self.numeric_df.empty:
                raise DataProcessingError(
                    "The uploaded CSV is empty or contains no data after removing empty rows/columns."
                )

            # Fill missing values with column mean
            self.numeric_df = self.numeric_df.fillna(self.numeric_df.mean())

            # Check for columns that are still all NaN
            if self.numeric_df.isnull().all().any():
                raise DataProcessingError(
                    "Some columns contain only non-numeric data and could not be processed. Please clean the data."
                )

            # Drop participant id columns (case insensitive)
            self.numeric_df = self.numeric_df.drop(columns=[col for col in self.numeric_df.columns if 'participant id' in col.lower()], errors='ignore')

            # Reset the index to be 0-based
            self.numeric_df = self.numeric_df.reset_index(drop=True)

            # remove outliers
            if not self.numeric_df.empty:
                self.numeric_df = _remove_outliers_iforest(self.numeric_df)

            if self.numeric_df.empty:
                raise DataProcessingError(
                    "After removing outliers, the dataset is empty. The contamination setting might be too high or the data is very uniform."
                )
            
            # OPTIMIZATION: Downcast numeric types to save memory
            # This can reduce memory by 50-75% for large datasets
            self._log("Downcasting numeric types to reduce memory...")
            for col in self.numeric_df.columns:
                col_type = self.numeric_df[col].dtype
                if col_type == 'float64':
                    self.numeric_df[col] = pd.to_numeric(self.numeric_df[col], downcast='float')
                elif col_type == 'int64':
                    self.numeric_df[col] = pd.to_numeric(self.numeric_df[col], downcast='integer')

            if self.numeric_df.empty:
                raise DataProcessingError(
                    "After removing outliers, the dataset is empty. The contamination setting might be too high or the data is very uniform."
                )

            # Log processed dataframe size
            processed_memory = self.numeric_df.memory_usage(deep=True).sum() / (1024 * 1024)
            self._log(f"Processed DataFrame memory: {processed_memory:.2f} MB")
            self._log(f"Processed numeric DataFrame shape: {self.numeric_df.shape}")
            
            return self.numeric_df
        except (ValueError, TypeError) as e:
            self._log(f"Error in while processing dataframe: {e}")
            raise DataProcessingError(f"A data conversion error occurred. Please check for non-numeric data in your CSV. Original error: {e}")

    def fit_pca(self, variance_threshold: float=0.80) -> None:
        """Fit PCA on the standardized numeric data."""
        if self.numeric_df is None:
            raise DataProcessingError("Dataframe not created. Cannot fit PCA.")

        try:
            # Ensure there is data to process
            if self.numeric_df.shape[1] < 1:
                raise PCACalculationError("Cannot perform PCA with zero columns. Please check your CSV file.")

            self.pca_model = pca(variance_threshold, normalize=True, random_state=42)
            
            # return PCA results
            self.pca_results = self.pca_model.fit_transform(self.numeric_df)

            # Check if we have enough components
            n_components = len(self.pca_results.get('explained_var', []))
            if n_components < 3:
                raise DataProcessingError(
                    f"PCA produced only {n_components} component(s). At least 3 components are required for analysis. "
                    "This may indicate insufficient variance in your data or too few variables."
                )

            if self.rotation_method != '':
                self.rotate_pca()
            
        except ValueError as e:
            self._log(f"Error in fit_pca: {e}")
            if "Input contains NaN" in str(e):
                raise PCACalculationError(
                    "PCA failed due to missing or non-numeric values after cleaning. Please check your data quality."
                )
            if "must be at least 2" in str(e):
                 raise PCACalculationError(
                    f"PCA requires at least 2 samples (rows), but received {self.numeric_df.shape[0]}. Please provide more data."
                )
            raise PCACalculationError(f"A value-related error occurred during PCA. Original error: {e}")
        except Exception as e:
            self._log(f"An unexpected error occurred in fit_pca: {e}")
            raise PCACalculationError(f"An unexpected error occurred during PCA calculation. Original error: {e}")

    def rotate_pca(self) -> None:
        """
        Rotate the PCA loadings and keep the same DataFrame structure so downstream
        code (to_csv, .iloc, .index, etc.) continues to work.
        """
        try:
            original_loadings = self.pca_model.results['loadings']
            
            self._log(f"Original loadings shape: {original_loadings.shape}")
            self._log(f"Original loadings type: {type(original_loadings)}")
            self._log(f"Sample loadings values:\n{original_loadings.iloc[:5, :3]}")
            
            # Check what keys are actually available in results
            self._log(f"Available keys in pca_model.results: {list(self.pca_model.results.keys())}")
            
            # Check if loadings are actually there and non-zero
            if isinstance(original_loadings, pd.DataFrame):
                self._log(f"Loadings sum: {original_loadings.sum().sum()}")
                self._log(f"Loadings max: {original_loadings.max().max()}")
                self._log(f"Loadings min: {original_loadings.min().min()}")
            
            # Check rotation method validity
            self._log(f"Attempting rotation with method: '{self.rotation_method}'")

            # Capture index/columns if loadings is a DataFrame
            if isinstance(original_loadings, pd.DataFrame):
                orig_index = original_loadings.index
                orig_columns = original_loadings.columns
                loadings_array = original_loadings.values
            else:
                orig_index = orig_columns = None
                loadings_array = np.asarray(original_loadings)

            self._log(f"Loadings array shape: {loadings_array.shape}")
            self._log(f"Loadings array sample:\n{loadings_array[:5, :3]}")
            
            # Check if we have valid data for rotation
            if loadings_array.size == 0:
                raise PCACalculationError("Loadings array is empty")
            
            if np.all(loadings_array == 0):
                raise PCACalculationError("All loadings are zero - cannot rotate")
                
            if loadings_array.shape[1] < 2:
                raise PCACalculationError(f"Need at least 2 components for rotation, got {loadings_array.shape[1]}")

            # Check if we need to transpose the matrix
            if loadings_array.shape[0] < loadings_array.shape[1]:
                self._log(f"Matrix appears to be components × variables ({loadings_array.shape}), transposing...")
                loadings_array = loadings_array.T
                transposed = True
            else:
                self._log(f"Matrix appears to be variables × components ({loadings_array.shape}), using as-is")
                transposed = False

            # Apply rotation
            rotator = Rotator(method=self.rotation_method)
            
            self._log(f"Applying {self.rotation_method} rotation to shape {loadings_array.shape}...")
            rotated_array = rotator.fit_transform(loadings_array)
            
            # Transpose back if we transposed earlier
            if transposed:
                self._log("Transposing result back to original orientation")
                rotated_array = rotated_array.T
            
            self._log(f"Rotated array shape: {rotated_array.shape}")
            self._log(f"Rotated array sample:\n{rotated_array[:5, :3]}")

            # Convert back to DataFrame when possible (preserve index/columns)
            if orig_index is not None and orig_columns is not None:
                rotated_df = pd.DataFrame(rotated_array, index=orig_index, columns=orig_columns)
                self.pca_model.results['loadings'] = rotated_df
                
                self._log(f"Successfully applied {self.rotation_method} rotation")
                self._log(f"Rotated loadings DataFrame shape: {rotated_df.shape}")
                self._log(f"Sample rotated values:\n{rotated_df.iloc[:5, :3]}")
            else:
                # keep as ndarray if no labels available
                self.pca_model.results['loadings'] = rotated_array
                self._log(f"Applied rotation to array format")

        except Exception as e:
            # Log the actual exception to help debugging
            self._log(f"Rotation failed for '{self.rotation_method}': {str(e)}")
            self._log(f"Exception type: {type(e).__name__}")
            
            # Import traceback for more detailed error info
            import traceback
            self._log(f"Full traceback:\n{traceback.format_exc()}")
            
            self._log("Continuing with unrotated PCA loadings")

    def get_most_important_variables(self) -> Dict:
        """Perform PCA analysis and return the results with scree plot."""
        if self.pca_model is None:
            self.fit_pca()

        try:
            # Get results from the pca wrapper
            results = {
                'explained_variance_ratio': self.pca_results['variance_ratio'],
                'loadings': self.pca_model.results['loadings'],
                'cumulative_variance': self.pca_results['explained_var'],
                'n_components': len(self.pca_results['explained_var']),
                'pca_scores': self.pca_results['PC']
            }
            
            self.pca_results = results
            
            return results

        except Exception as e:
            self._log(f"Error in get_most_important_variables: {e}")
            raise

    def display_important_variables(self, num_vars: int = 6, threshold: float = 80) -> int:
        """Display the most important variables for each PC and log results."""

        try:
            loadings = self.pca_results['loadings']

            # Components needed for variance threshold
            cumvar = self.pca_results['cumulative_variance']
            self.n_components = np.argmax(cumvar >= threshold/100) + 1
            self._log(f"Components needed for {threshold}% variance: {self.n_components}")
            self._log("=" * 60)

            # Save loadings to CSV
            loadings_path = os.path.join(self.results_dir, f'pca_loadings_{self.timestamp}.csv')
            loadings.to_csv(loadings_path)
            self.loadings = loadings
            self.loadings_path = loadings_path
            self._log(f"PCA loadings saved to {loadings_path}")

            # Log top variables per component
            for i in range(min(num_vars, loadings.shape[1])):
                variance_explained = self.pca_results['explained_variance_ratio'][i] * 100
                self._log(f"\nPC{i+1} (explains {variance_explained:.2f}% variance):")
                self._log("-" * 50)

                pc_loadings = loadings.iloc[:, i].copy()
                sorted_vars = pc_loadings.abs().sort_values(ascending=False)

                top_n = min(len(sorted_vars), num_vars)
                for j in range(top_n):
                    var_name = sorted_vars.index[j]
                    actual_loading = pc_loadings[var_name]
                    abs_loading = sorted_vars.iloc[j]
                    self._log(f"  {j+1:2d}. {var_name:<20}: {actual_loading:+.4f} (|{abs_loading:.4f}|)")

            return int(self.n_components)
        except Exception as e:
            self._log(f"Error in display_important_variables: {e}")
            raise
    
    def calculate_weighted_variable_importance(self, min_significance: float=0.3):
        """Calculate weighted importance scores for each VARIABLE using absolute loadings"""
        if self.pca_results is None:
            self.get_most_important_variables()
    
        loadings_raw = self.pca_results['loadings']
        loadings = loadings_raw.T
        variance_ratios = self.pca_results['explained_variance_ratio']
        
        self._log(f"Original loadings shape (PCs x variables): {loadings_raw.shape}")
        self._log(f"Transposed loadings shape (variables x PCs): {loadings.shape}")
        self._log(f"Variance ratios: {variance_ratios[:5]}...")
        
        results = {}
        
        for variable_name in loadings.index:
            variable_loadings = loadings.loc[variable_name]
            min_length = min(len(variable_loadings), len(variance_ratios))
            
            weighted = 0
            for i in range(min_length):
                loading = variable_loadings.iloc[i]
                variance = variance_ratios[i]
                
                if abs(loading) > min_significance:
                    weighted += abs(loading) * variance
            
            results[variable_name] = weighted
        
        sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
        self.total_weight = sum(x[1] for x in sorted_results)
        sorted_top_20 = sorted_results[:20]
        
        self.weighted_importance = sorted_top_20
        
        self._log(f"Total weight: {self.total_weight}")
        self._log("Top 5 weighted variables:")
        for i, (var, weight) in enumerate(sorted_top_20[:5]):
            pct = (weight / self.total_weight * 100) if self.total_weight > 0 else 0
            self._log(f"  {i+1}. {var}: {weight:.6f} ({pct:.2f}%)")
        
        return results

    def add_loadings_to_pdf(self, pdf: PdfPages, loadings_df: pd.DataFrame) -> None:
        """Add PCA loadings table from DataFrame to PDF with rotated column headers."""
        plt.ioff()
        
        df = loadings_df

        fig_width = max(8.5, len(df.columns) * 1.2)
        fig, ax = plt.subplots(figsize=(fig_width, 11))
        ax.axis('off')

        fig.suptitle('PCA Loadings Matrix', fontsize=14, fontweight='bold', y=0.95)

        col_width = 0.9 / len(df.columns)
        table = ax.table(
            cellText=df.round(4).values,
            rowLabels=df.index,
            colLabels=df.columns,
            cellLoc='center',
            loc='upper center',
            colWidths=[col_width] * len(df.columns)
        )

        table.auto_set_font_size(False)
        table.set_fontsize(8)

        for (row, col), cell in table.get_celld().items():
            if row == 0:
                cell.get_text().set_rotation(45)
                cell.set_height(0.1)
                cell.set_facecolor('#4CAF50')
                cell.set_text_props(weight='bold', color='white')            
            if row > 0:
                cell.set_facecolor("#D5FFD7" if row % 2 == 0 else '#ffffff')

        pdf.savefig(fig, bbox_inches='tight', dpi=150)
        plt.close(fig)
        del fig, ax
        gc.collect()
    
    def add_variable_importance_to_pdf(self, pdf: PdfPages, weighted_importance_list: list) -> None:
        """Add Variable Importance table from weighted importance scores to PDF."""
        plt.ioff()

        df = pd.DataFrame(weighted_importance_list, columns=["Variable", "Importance"])
        df["Importance"] = df["Importance"].astype(float) * 100 / self.total_weight
        df["Importance"] = df["Importance"].map(lambda x: f"{x:.2f}%")
        df = df.set_index("Variable")

        fig_width = max(8.5, 6)
        fig, ax = plt.subplots(figsize=(fig_width, 11))
        ax.axis('off')
        
        fig.suptitle('Variable Importance Rankings', fontsize=14, fontweight='bold', y=0.95)
        fig.text(0.5, 0.90, 'Top 20 Variables by Weighted PCA Loadings', 
            fontsize=12, ha='center', style='italic')
        
        col_width = 0.3
        table = ax.table(
            cellText=df.values,
            rowLabels=df.index,
            colLabels=df.columns,
            cellLoc='center',
            loc='upper center',
            colWidths=[col_width]
        )
        
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        
        for (row, col), cell in table.get_celld().items():
            if row == 0:
                cell.set_height(0.06)
                cell.set_facecolor('#FF6B35')
                cell.set_text_props(weight='bold', color='white')
            elif row > 0:
                cell.set_facecolor("#FFE5D9" if row % 2 == 0 else '#ffffff')
                cell.set_height(0.04)
            
            if col == -1:
                cell.set_text_props(weight='bold')
        
        pdf.savefig(fig, bbox_inches='tight', dpi=150)
        plt.close(fig)
        del fig, ax
        gc.collect()

        # Explanation page
        fig, ax = plt.subplots(figsize=(8.5, 11))
        ax.axis('off')
        
        title = "Variable Importance Score Calculation Method"
        explanation_text = (
            "1. Taking the absolute value of each variable's loading on\n"
            "each PC\n"
            "2. Weighting by that PC's variance explained\n"
            "3. Summing across all PCs for each variable\n"
            "4. Converting to percentages of total importance\n"
            "\nIf you see a list of nan values, it means that the program\n"
            "failed to extract variable importance. The number of\n"
            "PCs could be too low."
        )
        
        ax.text(0.1, 0.95, title, fontsize=14, fontweight='bold', ha='left', va='top')
        ax.text(0.12, 0.85, explanation_text, fontsize=12, ha='left', va='top',
            bbox=dict(boxstyle="round,pad=1.0", facecolor="lightyellow", alpha=0.8))
        
        pdf.savefig(fig, bbox_inches='tight', dpi=150)
        plt.close(fig)
        del fig, ax
        gc.collect()

    def create_pdf_report(self, df_shape: tuple, colour_variable: str | None=None) -> None:        
        """Create comprehensive PDF report with all analysis results."""
        plt.ioff()

        csv_name = os.path.basename(self.csv_file).replace(".csv", "")
        
        pdf_path = os.path.join(self.results_dir, f"PCA Analysis Report {csv_name}_{self.timestamp}.pdf")    
        if self.rotation_method:
            pdf_path = os.path.join(self.results_dir, f"PCA Analysis Report {csv_name}_{self.rotation_method}_{self.timestamp}.pdf")
        
        self.pdf_path = pdf_path
        
        # Determine adaptive feature count based on dataset size
        n_features = df_shape[1]  # Use the saved shape instead of self.numeric_df
        if n_features > 100:
            n_feat_to_show = 10
        elif n_features > 50:
            n_feat_to_show = 15
        else:
            n_feat_to_show = min(20, n_features)
        
        # CRITICAL: Make copies of data we need BEFORE deleting pca_model
        loadings_copy = self.loadings.copy()
        weighted_importance_copy = self.weighted_importance.copy() if hasattr(self, 'weighted_importance') else None
        total_weight_copy = self.total_weight if hasattr(self, 'total_weight') else None
        
        with PdfPages(pdf_path) as pdf:
            
            # Page 1: Table of Contents
            fig, ax = plt.subplots(figsize=(8.5, 11))
            ax.axis('off')

            toc_data = [
                ["Page", "Content"],
                ["1", "Table of contents"],
                ["2", "Scree plot"],
                ["3", "Scatterplot on PC1 and PC2"],
                ["4", "3D Scatterplot on PC1, PC2 and PC3"],
                ["5", "Biplot on PC1 and PC2"],
                ["6", "Loadings on the top principal components"],
                ["7", "Variables of greatest impact on variance"],
                ["8", "Other log results"]
            ]

            table = ax.table(cellText=toc_data, colLabels=None, loc='center', cellLoc='left', colWidths=[0.1, 0.8])
            table.auto_set_font_size(True)
            table.scale(1, 2)

            rotation_method_string = 'No rotation method applied'
            if self.rotation_method != '':
                rotation_method_string = f'Rotation method applied: {self.rotation_method}'

            ax.set_title(f"PCA Analysis Table of Contents\n({os.path.basename(self.csv_file)})\n{rotation_method_string}", fontsize=14, fontweight='bold')

            pdf.savefig(fig, bbox_inches='tight', dpi=150)
            plt.close(fig)
            del fig, ax
            gc.collect()

            # Page 2: Scree plot
            fig, ax = self.pca_model.plot(
                figsize=(16, 12),
                title='Scree Plot - Explained Variance per Component',
                xsteps=2,
            )
            ax.tick_params(axis='x', rotation=30)
            plt.tight_layout()
            pdf.savefig(fig, bbox_inches='tight', dpi=150)
            plt.close(fig)
            del fig, ax
            gc.collect()

            # Page 3: 2D Scatter
            fig, ax = self.pca_model.scatter(
                density=True,
                s=10,
                alpha=0.8,
                figsize=(16, 12),
                fontsize=15,
                title="2D Scatterplot - PC1 vs PC2"
            )
            pdf.savefig(fig, bbox_inches='tight', dpi=150)
            plt.close(fig)
            del fig, ax
            gc.collect()

            # Page 4: 3D Scatter
            fig, ax = self.pca_model.scatter3d(
                gradient='#FFFFFF',
                edgecolor=None,
                fontsize=15,
                s=10,
                alpha=0.2,
                figsize=(16, 12),
                title="3D Scatterplot - PC1, PC2, PC3"
            )
            try:
                pdf.savefig(fig, bbox_inches='tight', dpi=150)
            except Exception:
                pass
            plt.close(fig)
            del fig, ax
            gc.collect()

            # Page 5: Biplot
            try:
                fig, ax = self.pca_model.biplot(
                    n_feat=n_feat_to_show,
                    s=10,
                    alpha=0.2,
                    figsize=(16, 12),
                    arrowdict={
                        'alpha': 0.7,
                        'fontsize': 15,
                        'color_strong': '#CC0000',
                        'color_weak': '#CC0000',
                        'color_text': 'black',
                    },
                    title=f'Biplot - Top {n_feat_to_show} Features (PC1 vs PC2)',
                    legend=True,
                    grid=True
                )
                pdf.savefig(fig, bbox_inches='tight', dpi=150)
                plt.close(fig)
                del fig, ax
                gc.collect()
            except Exception:
                pass

            self._log("Deleting pca_model to free memory before generating tables...")
            self.pca_model = None
            gc.collect()

            # Page 6: Variable loadings (using copy)
            self.add_loadings_to_pdf(pdf, loadings_copy)

            # Page 7: Most important variables (using copy)
            if weighted_importance_copy:
                # Temporarily restore total_weight for the function
                original_total_weight = self.total_weight if hasattr(self, 'total_weight') else None
                self.total_weight = total_weight_copy
                try:
                    self.add_variable_importance_to_pdf(pdf, weighted_importance_copy)
                except Exception as e:
                    self._log(str(e))
                finally:
                    # Restore or delete
                    if original_total_weight is not None:
                        self.total_weight = original_total_weight
                    else:
                        delattr(self, 'total_weight')

            # Final page: Analysis Log
            with open(self.log_file, "r", encoding='utf-8') as f:
                log_file_lines = f.readlines()

            fig, ax = plt.subplots(figsize=(8.5, 11))
            ax.axis('off')
            log_text = '\n'.join(log_file_lines)
            ax.text(0.05, 0.95, log_text, transform=ax.transAxes, 
                    fontsize=8, verticalalignment='top', fontfamily='monospace')
            ax.set_title('Analysis Log', fontsize=14, fontweight='bold')
            pdf.savefig(fig, bbox_inches='tight', dpi=150)
            plt.close(fig)
            del fig, ax
            gc.collect()
            
        # Delete the copies after PDF is complete
        del loadings_copy
        if weighted_importance_copy:
            del weighted_importance_copy
        if total_weight_copy:
            del total_weight_copy
        gc.collect()
            
        self._log(f"Comprehensive PDF report saved to {pdf_path}")
        self._log(f"Note: Biplot limited to top {n_feat_to_show} features to reduce crowding")

    def run_full_pipeline(self, num_vars: int = 6) -> Dict:
        """Execute the complete PCA analysis pipeline with aggressive memory management."""

        # Track starting memory

        try:
            self._log("Starting PCA Analysis Pipeline...")
            self._log("=" * 60)

            self._log("\nStep 1: Loading and preprocessing data...")
            self.create_numeric_df()
            
            # Capture shape NOW before any potential deletion
            df_shape = self.numeric_df.shape

            self._log("\nStep 2: Fitting PCA model...")
            self.fit_pca()
            
            # CRITICAL: Delete numeric_df immediately after PCA fitting
            # The pca_model has all the data it needs internally
            self._log("Deleting numeric_df after PCA fit (no longer needed)...")
            numeric_df_shape = self.numeric_df.shape  # Save shape for later
            self.numeric_df = None
            gc.collect()

            self._log("\nStep 3: Performing PCA analysis...")
            pca_results = self.get_most_important_variables()

            self._log(f"\nStep 4: Displaying top {num_vars} variables per component...")
            n_components = self.display_important_variables(num_vars)

            self._log("\nStep 5: Calculating weighted variable importance...")
            try:
                self.calculate_weighted_variable_importance()
            except Exception as e:
                self._log(f"Warning in weighted importance calculation: {str(e)}")

            self._log(f"\nStep 6: Creating comprehensive PDF report...")
            self.create_pdf_report(df_shape)
            
            total_variance = pca_results['cumulative_variance'][-1]
            pdf_path = self.pdf_path

            self._log("\nStep 7: Aggressive memory cleanup...")
            
            # DELETE all large objects
            self.numeric_df = None
            self.raw_df = None
            self.loadings = None
            self.weighted_importance = None
            self.pca_results = None
            self.pca_model = None  # Should already be None from PDF creation
            
            # Return minimal data structure
            return {
                'n_components': n_components,
                'numeric_df_shape': df_shape,
                'total_variance_explained': total_variance,
                'pdf_path': pdf_path
            }
            
        except Exception as e:
            self._log(f"Error in run_full_pipeline: {e}")
            
            # Cleanup on error
            self._log("Cleaning up memory after error...")
            self.numeric_df = None
            self.raw_df = None
            self.pca_model = None
            self.loadings = None
            self.weighted_importance = None
            self.pca_results = None
            
            raise