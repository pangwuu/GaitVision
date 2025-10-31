"""
Module to run the PCA analysis as a whole. Outputs are shown in the results folder
"""

import sys
import os
import pandas as pd
from sklearn.preprocessing import StandardScaler
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest
import numpy as np
from typing import Dict
from datetime import datetime
from pca import pca
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox
import platform
from matplotlib.backends.backend_pdf import PdfPages
from factor_analyzer.rotator import Rotator 
import subprocess

class PCAAnalysisPipeline:
    def __init__(self, csv_file: str, rotation_option: str, results_dir: str = "results") -> None:
        self.csv_file = csv_file
        self.raw_df = None
        self.numeric_df = None
        self.scaler = StandardScaler()
        self.pca_model = None
        self.X_scaled = None
        self.X_pca = None
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
            self.raw_df = pd.read_csv(self.csv_file)
        except FileNotFoundError:
            self._log(f"ERROR: CSV file {self.csv_file} not found!")
            sys.exit(1)

        try:
            # Convert everything possible to numeric
            self.numeric_df = self.raw_df.apply(pd.to_numeric, errors="coerce")

            # Drop columns/rows that are completely empty
            self.numeric_df = self.numeric_df.dropna(axis=1, how="all").dropna(axis=0, how="all")

            # Fill missing values with column mean
            self.numeric_df = self.numeric_df.fillna(self.numeric_df.mean())

            # Drop participant id columns (case insensitive)
            self.numeric_df = self.numeric_df.drop(columns=[col for col in self.numeric_df.columns if 'participant id' in col.lower()])

            # Reset the index to be 0-based
            self.numeric_df = self.numeric_df.reset_index(drop=True)

            # remove outliers
            self.numeric_df = _remove_outliers_iforest(self.numeric_df)

            self._log(f"\nProcessed numeric DataFrame shape: {self.numeric_df.shape}")
            return self.numeric_df
        except Exception as e:
            self._log(f"Error in while processing dataframe: {e}")
            raise

    def fit_pca(self, variance_threshold: float=0.80) -> None:
        """Fit PCA on the standardized numeric data."""
        if self.numeric_df is None:
            raise ValueError("Must run create_numeric_df() first")

        try:
            self.pca_model = pca(variance_threshold, normalize=True, random_state=42)
            
            # return PCA results
            self.pca_results = self.pca_model.fit_transform(self.numeric_df)

            if self.rotation_method != '':
                self.rotate_pca()
            
        except Exception as e:
            self._log(f"Error in fit_pca: {e}")
            raise

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
                raise ValueError("Loadings array is empty")
            
            if np.all(loadings_array == 0):
                raise ValueError("All loadings are zero - cannot rotate")
                
            if loadings_array.shape[1] < 2:
                raise ValueError(f"Need at least 2 components for rotation, got {loadings_array.shape[1]}")

            # Check if we need to transpose the matrix
            # Rotator expects variables × components, but some PCA libraries give components × variables
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
            # Don't modify the original loadings if rotation fails

    def get_most_important_variables(self) -> Dict:
        """Perform PCA analysis and return the results with scree plot."""
        if self.pca_model is None:
            self.fit_pca()

        try:

            # Create scree plot using the pca wrapper's built-in method
            # fig, ax = self.pca_model.plot()
            # scree_path = os.path.join(self.results_dir, f"scree_plot_{self.timestamp}.png")
            # # plt.savefig(scree_path, dpi=300, bbox_inches="tight")
            # self._log(f"Scree plot saved to {scree_path}")
            # plt.close()

            # Get results from the pca wrapper
            
            results = {
                'explained_variance_ratio': self.pca_results['variance_ratio'],  # Individual ratios
                'loadings': self.pca_model.results['loadings'],
                'cumulative_variance': self.pca_results['explained_var'],       # Cumulative variance
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
    
    def create_scatterplot(self, colour_variable=None) -> None:
        """
        Creates a scatterplot with colours for the data
        """
        
        if self.pca_results is None:
            self.fit_pca()

        try:
            # Set matplotlib backend for headless environments
            plt.switch_backend('Agg')

            # Create 2D scatterplot using the pca wrapper's built-in method
            fig, ax = self.pca_model.scatter(density=True)
            
            biplot_path = os.path.join(self.results_dir, f"scatterplot_2d_{self.timestamp}.png")
            plt.savefig(biplot_path, dpi=300, bbox_inches="tight")
            self._log(f"2D Scatterplot saved to {biplot_path}")
            plt.close()

            # Create 3D scatterplot using the pca wrapper's built-in method
            fig, ax = self.pca_model.scatter3d(gradient='#FFFFFF', edgecolor=None)
            
            scatter3d_path = os.path.join(self.results_dir, f"scatterplot_3d_{self.timestamp}.png")
            plt.savefig(scatter3d_path, dpi=300, bbox_inches="tight")
            self._log(f"3D Scatterplot saved to {scatter3d_path}")
            plt.close()            

        except Exception as e:
            self._log(f"Error in create_biplot: {e}")
            raise
    
    def calculate_weighted_variable_importance(self, min_significance: float=0.3):
        """
        Calculate weighted importance scores for each VARIABLE using absolute loadings
        weighted by each PC's variance explained.
        
        Assumes loadings matrix is variables x PCs (variables as rows, PCs as columns)
        
        Returns:
        pd.Series: Variable importance scores sorted in descending order
        """
        if self.pca_results is None:
            self.get_most_important_variables()
    
        # Get loadings and variance ratios
        loadings_raw = self.pca_results['loadings']  # This is PCs × variables
        loadings = loadings_raw.T  # Transpose to get variables × PCs
        variance_ratios = self.pca_results['explained_variance_ratio']
        
        self._log(f"Original loadings shape (PCs x variables): {loadings_raw.shape}")
        self._log(f"Transposed loadings shape (variables x PCs): {loadings.shape}")
        self._log(f"Variance ratios: {variance_ratios[:5]}...")  # Show first 5
        
        results = {}
        
        # Iterate over variables (rows in the loadings matrix)
        for variable_name in loadings.index:  # This gets variable names from row index
            variable_loadings = loadings.loc[variable_name]  # Get the row for this variable
            
            # Ensure we don't exceed available components
            min_length = min(len(variable_loadings), len(variance_ratios))
            
            # Calculate weighted importance
            weighted = 0
            for i in range(min_length):
                loading = variable_loadings.iloc[i]  # Loading for PC i
                variance = variance_ratios[i]        # Variance explained by PC i
                
                # Only include if loading is significant
                if abs(loading) > min_significance:
                    weighted += abs(loading) * variance
            
            results[variable_name] = weighted
        
        # Sort results
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

    def add_loadings_to_pdf(self, pdf: PdfPages) -> None:
        """Add PCA loadings table from CSV to PDF with rotated column headers."""

        # Load CSV
        df = self.loadings

        # Dynamically set figure width based on columns
        fig_width = max(8.5, len(df.columns) * 1.2)  # 1.2 inch per column
        fig, ax = plt.subplots(figsize=(fig_width, 11))
        ax.axis('off')

        # Add title at top
        fig.suptitle('PCA Loadings Matrix', fontsize=14, fontweight='bold', y=0.95)

        # Create table
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

        # Optional: alternating row colors
        for (row, col), cell in table.get_celld().items():
            # Rotate and colour column headers
            if row == 0:  # header row
                cell.get_text().set_rotation(45)
                # cell.get_text().set_ha()  # align text to the right
                cell.set_height(0.1)  # make header cells taller
                cell.set_facecolor('#4CAF50')
                cell.set_text_props(weight='bold', color='white')            
            if row > 0:  # skip header
                cell.set_facecolor("#D5FFD7" if row % 2 == 0 else '#ffffff')

        # Save to PDF
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def add_variable_importance_to_pdf(self, pdf: PdfPages) -> None:
        """Add Variable Importance table from weighted importance scores to PDF."""
        
        # Check if we have weighted importance calculated
        if not hasattr(self, 'weighted_importance') or self.weighted_importance is None:
            self._log("No weighted importance scores available. Calculating now...")
            self.calculate_weighted_variable_importance()
        
        # Get total importance for the top 20 variables
        
        if not hasattr(self, "total_weight") or self.total_weight is None:
            self._log("No total weight - this should never happen")
            sys.exit(5)

        # Convert to DataFrame (Variable | Importance %)
        df = pd.DataFrame(self.weighted_importance, columns=["Variable", "Importance"])
        df["Importance"] = df["Importance"].astype(float) * 100 / self.total_weight  # convert to %
        df["Importance"] = df["Importance"].map(lambda x: f"{x:.2f}%")

        # Reindex to put variable names as row labels
        df = df.set_index("Variable")

        # Dynamically set figure width (only 1 data column, so simpler)
        fig_width = max(8.5, 6)  # Fixed width since we only have one data column
        fig, ax = plt.subplots(figsize=(fig_width, 11))
        ax.axis('off')
        
        # Add title at top
        fig.suptitle('Variable Importance Rankings', fontsize=14, fontweight='bold', y=0.95)
        
        # Add subtitle/explanation
        fig.text(0.5, 0.90, 'Top 20 Variables by Weighted PCA Loadings', 
            fontsize=12, ha='center', style='italic')
        
        # Create table
        col_width = 0.3  # Single column for percentages
        table = ax.table(
            cellText=df.values,
            rowLabels=df.index,
            colLabels=df.columns,
            cellLoc='center',
            loc='upper center',
            colWidths=[col_width]
        )
        
        table.auto_set_font_size(False)
        table.set_fontsize(10)  # Slightly larger font since we have more space
        
        # Style the table
        for (row, col), cell in table.get_celld().items():
            # Style column headers
            if row == 0:  # header row
                cell.set_height(0.06)  # make header cells taller
                cell.set_facecolor('#FF6B35')  # Orange header to distinguish from loadings
                cell.set_text_props(weight='bold', color='white')
            elif row > 0:  # data rows
                # Alternating row colors
                cell.set_facecolor("#FFE5D9" if row % 2 == 0 else '#ffffff')
                cell.set_height(0.04)
            
            # Make variable names bold in row labels (first column)
            if col == -1:  # row label column
                cell.set_text_props(weight='bold')
        
        # Save rankings page to PDF
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()

        # Create new page for explanation
        fig, ax = plt.subplots(figsize=(8.5, 11))
        ax.axis('off')
        
        title = "Variable Importance Score Calculation Method"
        explanation_text = (
            "1. Taking the absolute value of each variable's loading on each PC\n"
            "2. Weighting by that PC's variance explained\n" 
            "3. Summing across all PCs for each variable\n"
            "4. Converting to percentages of total importance"
        )
        
        # Add title with larger font and bold
        ax.text(0.1, 0.95, title, fontsize=14, fontweight='bold', ha='left', va='top')
        
        # Add explanation text below
        ax.text(0.1, 0.85, explanation_text, fontsize=12, ha='left', va='top',
            bbox=dict(boxstyle="round,pad=1.0", facecolor="lightyellow", alpha=0.8))
        
        # Save explanation page to PDF
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()

    def create_pdf_report(self, colour_variable: str | None=None) -> None:        
        """Create comprehensive PDF report with all analysis results."""

        csv_name = os.path.basename(self.csv_file).replace(".csv", "")
        
        pdf_path = os.path.join(self.results_dir, f"PCA Analysis Report {csv_name}_{self.timestamp}.pdf")    
        if self.rotation_method:
            pdf_path = os.path.join(self.results_dir, f"PCA Analysis Report {csv_name}_{self.rotation_method}_{self.timestamp}.pdf")
        
        self.pdf_path = pdf_path
        
        with PdfPages(pdf_path) as pdf:
            
            # Page 1: Summary and Data Overview            
            fig, ax = plt.subplots(figsize=(8.5, 11))
            ax.axis('off')

            # Table of contents data
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

            # Create table
            table = ax.table(cellText=toc_data, colLabels=None, loc='center', cellLoc='left', colWidths=[0.1, 0.8])
            table.auto_set_font_size(True)
            table.scale(1, 2)

            # Rotation method string
            rotation_method_string = 'No rotation method applied'
            if self.rotation_method != '':
                rotation_method_string = f'Rotation method applied: {self.rotation_method}'

            # Add title
            ax.set_title(f"PCA Analysis Table of Contents\n({os.path.basename(self.csv_file)})\n{rotation_method_string}", fontsize=14, fontweight='bold')

            pdf.savefig(fig, bbox_inches='tight')
            plt.close()
            
            # Page 2: Scree Plot
            fig, ax = self.pca_model.plot()
            pdf.savefig(fig, bbox_inches='tight')

            fig, ax = self.pca_model.scatter(density=True, title="Scatterplot with comparative density on P1 and P2")
            pdf.savefig(fig, bbox_inches='tight')

            fig, ax = self.pca_model.scatter3d(gradient='#FFFFFF', edgecolor=None, title="3D scatterplot with comparative density on P1 and P2")
            pdf.savefig(fig, bbox_inches='tight')    

            # Page 3: Biplot
            fig, ax = self.pca_model.biplot()
            pdf.savefig(fig, bbox_inches='tight')

            # Page 4: Variable loadings
            self.add_loadings_to_pdf(pdf)

            # Page 5: Most important variables
            try:
                self.add_variable_importance_to_pdf(pdf)
            except Exception as e:
                self._log(str(e))

            # Final page: Analysis Log
            with open(self.log_file, "r", encoding='utf-8') as f:
                log_file_lines = f.readlines()

            fig, ax = plt.subplots(figsize=(8.5, 11))
            ax.axis('off')
            log_text = '\n'.join(log_file_lines)
            ax.text(0.05, 0.95, log_text, transform=ax.transAxes, 
                    fontsize=8, verticalalignment='top', fontfamily='monospace')
            ax.set_title('Analysis Log', fontsize=14, fontweight='bold')
            pdf.savefig(fig, bbox_inches='tight')
            plt.close()            
            
        self._log(f"Comprehensive PDF report saved to {pdf_path}")

    def run_full_pipeline(self, num_vars: int = 6) -> Dict:
        """Execute the complete PCA analysis pipeline."""

        try:
            self._log("Starting PCA Analysis Pipeline...")
            self._log("=" * 60)

            # Step 1: Create numeric dataframe
            self._log("\nStep 1: Loading and preprocessing data...")
            self.create_numeric_df()

            self.fit_pca()

            # Step 2: PCA analysis
            self._log("\nStep 2: Performing PCA analysis...")
            pca_results = self.get_most_important_variables()

            # Step 3: Display important variables
            self._log(f"\nStep 3: Displaying top {num_vars} variables per component...")
            n_components = self.display_important_variables(num_vars)

            # Step 4: Create biplot
            # self._log(f"\nStep 4: Creating clustering analysis and radar chart...")
            # self.create_scatterplot()

            # Page 5: Try to get the most important variables by sum of squared method
            try:
                self.calculate_weighted_variable_importance()
            except Exception as e:
                self._log(str(e))

            # Add this at the end of run_full_pipeline, before the success log
            self._log(f"\nStep 4: Creating comprehensive PDF report...")
            self.create_pdf_report()                

            self._log("\nPipeline completed successfully!")
            self._log("=" * 60)

            return {
                'pca_results': pca_results,
                'n_components': n_components,
                'numeric_df_shape': self.numeric_df.shape,
                'total_variance_explained': pca_results['cumulative_variance'][-1]
            }
        except Exception as e:
            self._log(f"Error in run_full_pipeline: {e}")
            raise

def show_error_dialog(title, message): # pragma: no cover
    """Show error dialog."""
    try:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec_()
    except Exception as e:
        print(f"Could not show error dialog: {e}")

def notify_done(): # pragma: no cover
    try:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Analysis Complete")
        msg.setText("Your PCA analysis has finished!\n\nResults have been saved to the 'Documents/PCA_Analysis/results' folder.")
        msg.exec_()
    except Exception as e:
        print(f"Could not show completion dialog: {e}")

def get_csv_file_path(): # pragma: no cover
    """Opens a file dialog for the user to select a CSV file and returns the path."""
    try:
        selected_template, _ = QFileDialog.getOpenFileName(
            None,
            "Select the CSV file you wish to analyse",
            "",
            "CSV Files (*.csv)",
            options=QFileDialog.DontUseNativeDialog
        )
        return selected_template
    except Exception as e:
        print(f"Error in file dialog: {e}")
        return None

def main():

    # Optional when running from command line - first command line argument is the file and we skip all GUI steps
    HEADLESS = False
    error = False

    # Headless mode when an ABSOLUTE filepath is given as 1st command line argument
    selected_path = None
    test_mode = False
    
    # Headless mode specs
    if len(sys.argv) >= 2:
        selected_path = sys.argv[1]
        HEADLESS = True
    
    # Test mode specifications
    if len(sys.argv) >= 3:
        test_arg = sys.argv[2]
        if test_arg == '--test':
            test_mode = True
            # tests can only be run headless
            HEADLESS = True

    # Initialize QApplication properly
    if not HEADLESS: # pragma: no cover
        if not QApplication.instance():
            app = QApplication(sys.argv)
        else:
            app = QApplication.instance()

    # Must be stored here as executable doesn't have access to the directory where the executable is stored
    work_dir = os.path.join(os.path.expanduser('~'), 'Documents', 'PCA_Analysis')
    os.makedirs(work_dir, exist_ok=True)
    os.chdir(work_dir)
    
    try:
        # Get file path
        if not HEADLESS: # pragma: no cover
            selected_path = get_csv_file_path()
        
        if not selected_path:
            print("No file selected. Exiting.")
            return
    except Exception as e:
        error_msg = f"An error occurred during selection of the file path: {str(e)}"
        print(error_msg)
        if not HEADLESS: # pragma: no cover
            show_error_dialog("File path Error", error_msg)
        sys.exit(2)
    
    try:
        rotation_options = ['', 'varimax', 'promax']

        for rotation_option in rotation_options:
            # Run the analysis
            pipeline = PCAAnalysisPipeline(selected_path, rotation_option)
            if test_mode:
                pipeline = PCAAnalysisPipeline(selected_path, rotation_option, 'test_results')

            filename = os.path.basename(selected_path)
            pipeline._log(f"Starting analysis of: {filename}")
            results = pipeline.run_full_pipeline()
            pipeline._log("Analysis completed successfully!") 

            if not test_mode: # pragma: no cover
                work_dir = os.path.join(work_dir, 'results')
                
                try:
                    if platform.system() == "Windows":
                        os.startfile(pipeline.pdf_path)
                    elif platform.system() == "Darwin":
                        subprocess.run(["open", pipeline.pdf_path])
                    else:
                        subprocess.run(["xdg-open", pipeline.pdf_path])  
                except Exception as e:
                    print(f"An error occured when trying to open the pdf summary. Please open results manually at {work_dir}")
        
    except Exception as e:
        error_msg = f"An error occurred during analysis: {str(e)}"
        error = True
        print(error_msg)
        if not HEADLESS: # pragma: no cover
            show_error_dialog("Analysis Error", error_msg)
            sys.exit(3)   

    # Show completion dialog
    if not HEADLESS and not error: # pragma: no cover
        notify_done()
    
if __name__ == "__main__":
    main()
    sys.exit(0)