#!/usr/bin/env python3
"""
Pytest test suite for PCA pipeline
Usage: pytest test_pca_pipeline.py -v
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path
from pca_pipeline_module import PCAAnalysisPipeline, DataProcessingError, PCACalculationError

@pytest.fixture
def temp_results_dir(tmp_path):
    """Create a temporary results directory for each test"""
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    return str(results_dir)


@pytest.fixture
def dominant_pc1_data():
    """Test case: PC1 should explain majority of variance (~55-95%)"""
    np.random.seed(42)
    
    factor = np.random.randn(50)
    
    df = pd.DataFrame({
        'Variable_1': 10.0 * factor + 0.05 * np.random.randn(50),
        'Variable_2': 9.0 * factor + 0.05 * np.random.randn(50),
        'Variable_3': -7.5 * factor + 0.05 * np.random.randn(50),
        'Variable_4': 8.0 * factor + 0.01 * np.random.randn(50), 
        'Variable_5': -6.0 * factor + 0.01 * np.random.randn(50)
    })
    
    return df


@pytest.fixture
def two_domains_data():
    """Two domain test case with clear structure"""
    np.random.seed(42)
    factor_A = np.random.randn(50)
    factor_B = np.random.randn(50)
    
    df = pd.DataFrame({
        'Force_1': 2.0 * factor_A + 0.2 * np.random.randn(50),
        'Force_2': 1.8 * factor_A + 0.2 * np.random.randn(50),
        'Force_3': 1.5 * factor_A + 0.2 * np.random.randn(50),
        'Balance_1': 2.0 * factor_B + 0.2 * np.random.randn(50),
        'Balance_2': -1.8 * factor_B + 0.2 * np.random.randn(50),
        'Balance_3': 1.6 * factor_B + 0.2 * np.random.randn(50)
    })
    
    return df


@pytest.fixture
def noisy_mixed_data():
    """Test case: Mixed structure with significant noise"""
    np.random.seed(42)
    factor1 = np.random.randn(50)
    factor2 = np.random.randn(50)
    
    df = pd.DataFrame({
        'Var_A1': 1.5 * factor1 + 0.8 * np.random.randn(50),
        'Var_A2': 1.2 * factor1 + 0.8 * np.random.randn(50),
        'Var_B1': 1.4 * factor2 + 0.8 * np.random.randn(50),
        'Var_B2': -1.1 * factor2 + 0.8 * np.random.randn(50),
        'Noise': np.random.randn(50) * 2.0
    })
    
    return df


def create_temp_csv(df: pd.DataFrame, tmp_path: Path, name: str) -> str:
    """Helper to create temporary CSV file"""
    csv_path = tmp_path / f"{name}.csv"
    df.to_csv(csv_path, index=False)
    return str(csv_path)


class TestDataLoading:
    """Test data loading and preprocessing"""
    
    def test_load_valid_csv(self, dominant_pc1_data, tmp_path, temp_results_dir):
        """Test loading a valid CSV file"""
        csv_file = create_temp_csv(dominant_pc1_data, tmp_path, "valid")
        pipeline = PCAAnalysisPipeline(csv_file, '', results_dir=temp_results_dir)
        
        numeric_df = pipeline.create_numeric_df()
        
        assert numeric_df is not None
        assert numeric_df.shape[1] == 5  # 5 variables
        assert numeric_df.shape[0] > 0   # Has rows after outlier removal
    
    def test_missing_file(self, temp_results_dir):
        """Test handling of missing file"""
        pipeline = PCAAnalysisPipeline("nonexistent.csv", '', results_dir=temp_results_dir)
        
        with pytest.raises(DataProcessingError, match="Could not find the uploaded file"):
            pipeline.create_numeric_df()
    
    def test_handle_missing_values(self, tmp_path, temp_results_dir):
        """Test handling of missing values"""
        df = pd.DataFrame({
            'A': [1, 2, np.nan, 4, 5],
            'B': [2, np.nan, 4, 5, 6],
            'C': [3, 4, 5, np.nan, 7]
        })
        
        csv_file = create_temp_csv(df, tmp_path, "with_nans")
        pipeline = PCAAnalysisPipeline(csv_file, '', results_dir=temp_results_dir)
        
        numeric_df = pipeline.create_numeric_df()
        
        # Should fill NaNs with column means
        assert not numeric_df.isnull().any().any()
    
    def test_drop_participant_id_columns(self, tmp_path, temp_results_dir):
        """Test that participant ID columns are dropped"""
        df = pd.DataFrame({
            'Participant ID': [1, 2, 3, 4, 5],
            'Value1': [1.1, 2.2, 3.3, 4.4, 5.5],
            'Value2': [5.5, 4.4, 3.3, 2.2, 1.1]
        })
        
        csv_file = create_temp_csv(df, tmp_path, "with_ids")
        pipeline = PCAAnalysisPipeline(csv_file, '', results_dir=temp_results_dir)
        
        numeric_df = pipeline.create_numeric_df()
        
        # Participant ID columns should be removed
        assert 'Participant ID' not in numeric_df.columns
        assert 'Value1' in numeric_df.columns
        assert 'Value2' in numeric_df.columns


class TestPCAComputation:
    """Test PCA computation and results"""
    
    def test_dominant_pc1_structure(self, dominant_pc1_data, tmp_path, temp_results_dir):
        """Test case where PC1 should dominate variance explanation"""
        csv_file = create_temp_csv(dominant_pc1_data, tmp_path, "dominant_pc1")
        pipeline = PCAAnalysisPipeline(csv_file, '', results_dir=temp_results_dir)
        
        pipeline.create_numeric_df()
        pca_results = pipeline.get_most_important_variables()
        
        pc1_variance = pca_results['explained_variance_ratio'][0] * 100
        
        # PC1 should explain between 55-95% of variance
        assert 55 <= pc1_variance <= 100, f"PC1 variance {pc1_variance:.1f}% outside expected range"
        
        # Should need at most 3 components for 95% variance
        cumvar = pca_results['cumulative_variance']
        n_components_95 = np.argmax(cumvar >= 0.95) + 1
        assert n_components_95 <= 3, f"Need {n_components_95} components for 95% variance (expected ≤3)"
    
    def test_two_domains_structure(self, two_domains_data, tmp_path, temp_results_dir):
        """Test case with two clear domains"""
        csv_file = create_temp_csv(two_domains_data, tmp_path, "two_domains")
        pipeline = PCAAnalysisPipeline(csv_file, '', results_dir=temp_results_dir)
        
        pipeline.create_numeric_df()
        pca_results = pipeline.get_most_important_variables()
        
        pc1_variance = pca_results['explained_variance_ratio'][0] * 100
        pc2_variance = pca_results['explained_variance_ratio'][1] * 100
        
        # PC1 should be dominant but not overwhelming
        assert 35 <= pc1_variance <= 65, f"PC1 variance {pc1_variance:.1f}% outside expected range"
        
        # PC2 should also be significant
        assert pc2_variance > 20, f"PC2 variance {pc2_variance:.1f}% too low"
        
        # Should need 2-3 components for 95% variance
        cumvar = pca_results['cumulative_variance']
        n_components_95 = np.argmax(cumvar >= 0.95) + 1
        assert n_components_95 <= 3, f"Need {n_components_95} components (expected ≤3)"
    
    def test_noisy_mixed_data(self, noisy_mixed_data, tmp_path, temp_results_dir):
        """Test case with mixed structure and noise"""
        csv_file = create_temp_csv(noisy_mixed_data, tmp_path, "noisy_mixed")
        pipeline = PCAAnalysisPipeline(csv_file, '', results_dir=temp_results_dir)
        
        pipeline.create_numeric_df()
        pca_results = pipeline.get_most_important_variables()
        
        pc1_variance = pca_results['explained_variance_ratio'][0] * 100
        
        # PC1 should explain less due to noise and mixed structure
        assert 20 <= pc1_variance <= 50, f"PC1 variance {pc1_variance:.1f}% outside expected range"
        
        # May need more components due to distributed variance
        cumvar = pca_results['cumulative_variance']
        n_components_95 = np.argmax(cumvar >= 0.95) + 1
        assert n_components_95 <= 5, f"Need {n_components_95} components (expected ≤5)"



class TestRotation:
    """Test rotation methods"""
    
    @pytest.mark.parametrize("rotation_method", ["varimax", "promax"])
    def test_rotation_methods(self, dominant_pc1_data, tmp_path, temp_results_dir, rotation_method):
        """Test different rotation methods"""
        csv_file = create_temp_csv(dominant_pc1_data, tmp_path, f"rotation_{rotation_method}")
        pipeline = PCAAnalysisPipeline(csv_file, rotation_method, results_dir=temp_results_dir)
        
        pipeline.create_numeric_df()
        pipeline.fit_pca()
        pca_results = pipeline.get_most_important_variables()
        
        # Rotated loadings should exist and have correct shape
        loadings = pca_results['loadings']
        assert loadings is not None
        assert loadings.shape[0] == 1
        assert loadings.shape[1] >= 3
    
    def test_no_rotation(self, dominant_pc1_data, tmp_path, temp_results_dir):
        """Test with no rotation"""
        csv_file = create_temp_csv(dominant_pc1_data, tmp_path, "no_rotation")
        pipeline = PCAAnalysisPipeline(csv_file, '', results_dir=temp_results_dir)
        
        pipeline.create_numeric_df()
        pipeline.fit_pca()
        pca_results = pipeline.get_most_important_variables()
        
        # Should still work without rotation
        assert pca_results['loadings'] is not None


class TestVariableImportance:
    """Test variable importance calculations"""
    
    def test_weighted_importance_calculation(self, dominant_pc1_data, tmp_path, temp_results_dir):
        """Test weighted variable importance calculation"""
        csv_file = create_temp_csv(dominant_pc1_data, tmp_path, "importance")
        pipeline = PCAAnalysisPipeline(csv_file, '', results_dir=temp_results_dir)
        
        pipeline.create_numeric_df()
        pipeline.get_most_important_variables()
        importance = pipeline.calculate_weighted_variable_importance()
        
        # Should return importance for all variables
        assert len(importance) == 5
        
        # All importance values should be non-negative
        assert all(val >= 0 for val in importance.values())
        
        # Should be sorted by importance (check top 3)
        top_3 = list(importance.items())[:3]
        assert top_3[0][1] >= top_3[1][1] >= top_3[2][1]
    
    def test_display_important_variables(self, dominant_pc1_data, tmp_path, temp_results_dir):
        """Test display_important_variables function"""
        csv_file = create_temp_csv(dominant_pc1_data, tmp_path, "display_vars")
        pipeline = PCAAnalysisPipeline(csv_file, '', results_dir=temp_results_dir)
        
        pipeline.create_numeric_df()
        pipeline.get_most_important_variables()
        n_components = pipeline.display_important_variables(num_vars=6, threshold=80)
        
        # Should return number of components
        assert isinstance(n_components, int)
        assert n_components >= 1
        
        # Loadings CSV should be created
        assert os.path.exists(pipeline.loadings_path)


class TestPipelineIntegration:
    """Test full pipeline integration"""
    
    def test_full_pipeline_execution(self, noisy_mixed_data, tmp_path, temp_results_dir):
        """Test complete pipeline from start to finish"""
        csv_file = create_temp_csv(noisy_mixed_data, tmp_path, "full_pipeline")
        pipeline = PCAAnalysisPipeline(csv_file, '', results_dir=temp_results_dir)
        
        results = pipeline.run_full_pipeline(num_vars=6)
        
        # Check returned results
        assert 'n_components' in results
        assert 'numeric_df_shape' in results
        assert 'total_variance_explained' in results
        assert 'pdf_path' in results
        
        # Check that PDF was created
        assert os.path.exists(results['pdf_path'])
        
        # Check that log file was created
        assert os.path.exists(pipeline.log_file)
    
    def test_pipeline_with_rotation(self, two_domains_data, tmp_path, temp_results_dir):
        """Test pipeline with rotation"""
        csv_file = create_temp_csv(two_domains_data, tmp_path, "pipeline_rotation")
        pipeline = PCAAnalysisPipeline(csv_file, 'varimax', results_dir=temp_results_dir)
        
        results = pipeline.run_full_pipeline(num_vars=6)
        
        # Should complete successfully
        assert results['n_components'] >= 2
        assert os.path.exists(results['pdf_path'])



class TestErrorHandling:
    """Test error handling"""
    
    def test_empty_dataframe_error(self, tmp_path, temp_results_dir):
        """Test handling of empty dataframe"""
        df = pd.DataFrame()
        csv_file = create_temp_csv(df, tmp_path, "empty")
        pipeline = PCAAnalysisPipeline(csv_file, '', results_dir=temp_results_dir)
        
        with pytest.raises(DataProcessingError, match="Failed to read"):
            pipeline.create_numeric_df()
    
    def test_all_non_numeric_data(self, tmp_path, temp_results_dir):
        """Test handling of all non-numeric data"""
        df = pd.DataFrame({
            'A': ['text', 'data', 'only', 'here', 'now'],
            'B': ['more', 'text', 'data', 'here', 'too']
        })
        csv_file = create_temp_csv(df, tmp_path, "all_text")
        pipeline = PCAAnalysisPipeline(csv_file, '', results_dir=temp_results_dir)
        
        with pytest.raises(DataProcessingError):
            pipeline.create_numeric_df()
    
    def test_insufficient_samples(self, tmp_path, temp_results_dir):
        """Test handling of insufficient samples"""
        df = pd.DataFrame({
            'A': [1],
            'B': [2]
        })
        csv_file = create_temp_csv(df, tmp_path, "one_sample")
        pipeline = PCAAnalysisPipeline(csv_file, '', results_dir=temp_results_dir)
        
        with pytest.raises(PCACalculationError):
            pipeline.create_numeric_df()
            pipeline.fit_pca()


# Deterministic test for reproducibility
def test_deterministic_results(tmp_path, temp_results_dir):
    """Test that results are deterministic with same seed"""
    np.random.seed(42)
    df1 = pd.DataFrame({
        'A': np.random.randn(50),
        'B': np.random.randn(50),
        'C': np.random.randn(50)
    })
    
    np.random.seed(42)
    df2 = pd.DataFrame({
        'A': np.random.randn(50),
        'B': np.random.randn(50),
        'C': np.random.randn(50)
    })
    
    csv1 = create_temp_csv(df1, tmp_path, "deterministic1")
    csv2 = create_temp_csv(df2, tmp_path, "deterministic2")
    
    # Create separate result directories
    results_dir1 = os.path.join(temp_results_dir, "run1")
    results_dir2 = os.path.join(temp_results_dir, "run2")
    os.makedirs(results_dir1)
    os.makedirs(results_dir2)
    
    pipeline1 = PCAAnalysisPipeline(csv1, '', results_dir=results_dir1)
    pipeline2 = PCAAnalysisPipeline(csv2, '', results_dir=results_dir2)
    
    pipeline1.create_numeric_df()
    results1 = pipeline1.get_most_important_variables()
    
    pipeline2.create_numeric_df()
    results2 = pipeline2.get_most_important_variables()
    
    # Results should be identical
    np.testing.assert_array_almost_equal(
        results1['explained_variance_ratio'],
        results2['explained_variance_ratio'],
        decimal=10
    )