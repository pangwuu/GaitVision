"""
This module contains the refactored PCA logic, designed to be used within the Flask backend.
It accepts a pandas DataFrame directly and returns calculated variable importances.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from pca import pca
from typing import Dict

class PCAAnalysis:
    """A simplified and backend-friendly version of the PCA pipeline."""
    def __init__(self, dataframe: pd.DataFrame) -> None:
        self.raw_df = dataframe
        self.numeric_df = None
        self.pca_model = None
        self.pca_results = {}

    def create_numeric_df(self) -> pd.DataFrame:
        """Converts the raw DataFrame into a preprocessed numeric DataFrame."""
        
        def _remove_outliers_iforest(df: pd.DataFrame, contamination=0.05):
            """Safely removes outliers using IsolationForest."""
            if df.empty or df.shape[1] == 0:
                return df
            
            iso = IsolationForest(contamination=contamination, random_state=42)
            mask = iso.fit_predict(df) != -1
            print(f"Removed {len(df) - np.sum(mask)} outliers (kept {np.sum(mask)})")
            return df[mask]

        try:
            # Convert everything possible to numeric
            self.numeric_df = self.raw_df.apply(pd.to_numeric, errors="coerce")

            # Drop columns/rows that are completely empty
            self.numeric_df = self.numeric_df.dropna(axis=1, how="all").dropna(axis=0, how="all")

            # Fill missing values with column mean
            self.numeric_df = self.numeric_df.fillna(self.numeric_df.mean())

            # Drop participant id columns (case insensitive), ignore errors if not found
            self.numeric_df = self.numeric_df.drop(
                columns=[col for col in self.numeric_df.columns if 'participant id' in col.lower()],
                errors='ignore'
            )

            self.numeric_df = self.numeric_df.reset_index(drop=True)
            self.numeric_df = _remove_outliers_iforest(self.numeric_df)
            
            return self.numeric_df
        except Exception as e:
            print(f"Error while processing dataframe: {e}")
            raise

    def fit_pca(self, variance_threshold: float = 0.80) -> None:
        """Fits PCA on the standardized numeric data."""
        if self.numeric_df is None:
            raise ValueError("Numeric DataFrame not created. Run create_numeric_df() first.")

        try:
            self.pca_model = pca(normalize=True, random_state=42, n_components = variance_threshold)
            self.pca_results = self.pca_model.fit_transform(self.numeric_df)
        except Exception as e:
            print(f"Error in fit_pca: {e}")
            raise

    def get_most_important_variables(self) -> Dict:
        """Extracts key results after fitting PCA."""
        if not self.pca_results:
            self.fit_pca()

        try:
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
            print(f"Error in get_most_important_variables: {e}")
            raise

    def calculate_weighted_variable_importance(self, min_significance: float = 0.3) -> Dict:
        """Calculates a weighted importance score for each variable."""
        # This method depends on the structure created by get_most_important_variables.
        # We check for a key that method creates and run it if it's missing.
        if 'explained_variance_ratio' not in self.pca_results:
            self.get_most_important_variables()

        try:
            loadings_raw = self.pca_results['loadings']
            loadings = loadings_raw.T  # Transpose to get variables × PCs
            variance_ratios = self.pca_results['explained_variance_ratio']
            
            results = {}
            for variable_name in loadings.index:
                variable_loadings = loadings.loc[variable_name]
                min_length = min(len(variable_loadings), len(variance_ratios))
                
                weighted_importance = 0
                for i in range(min_length):
                    loading = variable_loadings.iloc[i]
                    variance = variance_ratios[i]
                    
                    if abs(loading) > min_significance:
                        weighted_importance += abs(loading) * variance
                
                results[variable_name] = weighted_importance
            
            return results
        except Exception as e:
            print(f"Error calculating variable importance: {e}")
            raise

def get_pca_suggestions(dataframe: pd.DataFrame) -> Dict:
    """
    High-level function to run the PCA pipeline on a DataFrame and get variable importance.
    
    Args:
        dataframe (pd.DataFrame): The input data.

    Returns:
        Dict: A dictionary of variables and their importance scores.
    """
    try:
        pipeline = PCAAnalysis(dataframe)
        pipeline.create_numeric_df()
        pipeline.fit_pca()
        suggestions = pipeline.calculate_weighted_variable_importance()
        
        # Sort suggestions for cleaner output
        sorted_suggestions = dict(sorted(suggestions.items(), key=lambda item: item[1], reverse=True))
        
        return sorted_suggestions
    except Exception as e:
        print(f"Error during PCA suggestion generation: {e}")
        raise
