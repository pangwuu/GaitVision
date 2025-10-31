"""
Module to run the PCA analysis as a whole. Outputs are shown in the results folder
"""

import sys
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
import numpy as np
from typing import Dict
from pca import pca

class PCAAnalysisPipelineSimplified:
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
            print(f"ERROR: CSV file {self.csv_file} not found!")
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

            print(f"\nProcessed numeric DataFrame shape: {self.numeric_df.shape}")
            return self.numeric_df
        except Exception as e:
            print(f"Error in while processing dataframe: {e}")
            raise

    def fit_pca(self, variance_threshold: float=0.80) -> None:
        """Fit PCA on the standardized numeric data."""
        if self.numeric_df is None:
            raise ValueError("Must run create_numeric_df() first")

        try:
            self.pca_model = pca(variance_threshold, normalize=True, random_state=42)
            
            # return PCA results
            self.pca_results = self.pca_model.fit_transform(self.numeric_df)
            
        except Exception as e:
            print(f"Error in fit_pca: {e}")
            raise

    def get_most_important_variables(self) -> Dict:
        """Perform PCA analysis and return the results with scree plot."""
        if self.pca_model is None:
            self.fit_pca()

        try:
            
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
            print(f"Error in get_most_important_variables: {e}")
            raise

    def display_important_variables(self, num_vars: int = 6, threshold: float = 80) -> int:

        try:
            loadings = self.pca_results['loadings']

            # Components needed for variance threshold
            cumvar = self.pca_results['cumulative_variance']
            self.n_components = np.argmax(cumvar >= threshold/100) + 1

            self.loadings = loadings
            
            return int(self.n_components)
        except Exception as e:
            print(f"Error in display_important_variables: {e}")
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
        
        print(f"Original loadings shape (PCs x variables): {loadings_raw.shape}")
        print(f"Transposed loadings shape (variables x PCs): {loadings.shape}")
        print(f"Variance ratios: {variance_ratios[:5]}...")  # Show first 5
        
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
        
        return results

    def run_full_pipeline(self, num_vars: int = 6):
        """Execute the complete PCA analysis pipeline."""

        try:
            print("Starting PCA Analysis Pipeline...")
            print("=" * 60)

            # Step 1: Create numeric dataframe
            print("\nStep 1: Loading and preprocessing data...")
            self.create_numeric_df()

            self.fit_pca()

            # Step 2: PCA analysis
            print("\nStep 2: Performing PCA analysis...")
            pca_results = self.get_most_important_variables()

            # Step 3: Display important variables
            print(f"\nStep 3: Displaying top {num_vars} variables per component...")
            n_components = self.display_important_variables(num_vars)

            # Step 4: Create biplot
            # print(f"\nStep 4: Creating clustering analysis and radar chart...")
            # self.create_scatterplot()

            # Page 5: Try to get the most important variables by sum of squared method
            try:
                self.calculate_weighted_variable_importance()
            except Exception as e:
                print(str(e))
            
            print(self.weighted_importance)

        except Exception as e:
            print(f"Error in run_full_pipeline: {e}")
            raise

def main():
    selected_path = ''

    try:
        rotation_options = ['']

        for rotation_option in rotation_options:
            # Run the analysis
            pipeline = PCAAnalysisPipelineSimplified(selected_path, rotation_option)
            pipeline.run_full_pipeline()

    except Exception as e:
        error_msg = f"An error occurred during analysis: {str(e)}"
        error = True
        print(error_msg)

    
if __name__ == "__main__":
    main()
    sys.exit(0)