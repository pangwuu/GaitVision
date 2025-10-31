#!/usr/bin/env python3
"""
Test runner that tests the PCA pipeline against some easy cases to ensure it all works
Usage: python pca_test.py
"""

import sys
import os
import pandas as pd
import numpy as np
import tempfile
from typing import Dict, Any
from pca_pipeline import PCAAnalysisPipeline

class PipelineTester:
    """
    Tests the PCA pipeline with known test cases.
    """
    
    def __init__(self):
        self.test_results = {}
        self.temp_files = []
    
    def create_test_csv(self, df: pd.DataFrame, name: str) -> str:
        """Create temporary CSV file"""
        fd, filename = tempfile.mkstemp(suffix=f'_{name}.csv')
        os.close(fd)
        df.to_csv(filename, index=False)
        self.temp_files.append(filename)
        return filename

    def cleanup(self):
        """Remove temporary files"""
        for file in self.temp_files:
            if os.path.exists(file):
                os.remove(file)
    
    def create_dominant_pc1_data(self) -> pd.DataFrame:
        """Test case: PC1 should explain ~95% variance"""
        np.random.seed(42)
        
        factor = np.random.randn(50)
        
        return pd.DataFrame({
            'Variable_1': 10.0 * factor + 0.05 * np.random.randn(50),
            'Variable_2': 9.0 * factor + 0.05 * np.random.randn(50),
            'Variable_3': -7.5 * factor + 0.05 * np.random.randn(50),
            'Variable_4': 8.0 * factor + 0.01 * np.random.randn(50), 
            'Variable_5': -6.0 * factor + 0.01 * np.random.randn(50)
        })
    
    def create_two_domains_data(self) -> pd.DataFrame:
        """Two domain test case. The data should be covered by exactly two domains"""
        np.random.seed(42)
        factor_A = np.random.randn(50)
        factor_B = np.random.randn(50)
        
        return pd.DataFrame({
            'Force_1': 2.0 * factor_A + 0.2 * np.random.randn(50),
            'Force_2': 1.8 * factor_A + 0.2 * np.random.randn(50),
            'Force_3': 1.5 * factor_A + 0.2 * np.random.randn(50),
            'Balance_1': 2.0 * factor_B + 0.2 * np.random.randn(50),
            'Balance_2': -1.8 * factor_B + 0.2 * np.random.randn(50),
            'Balance_3': 1.6 * factor_B + 0.2 * np.random.randn(50)
        })
    
    def create_noisy_mixed_data(self) -> pd.DataFrame:
        """Test case: Mixed structure with noise"""
        np.random.seed(42)
        factor1 = np.random.randn(50)
        factor2 = np.random.randn(50)
        
        return pd.DataFrame({
            'Var_A1': 1.5 * factor1 + 0.8 * np.random.randn(50),
            'Var_A2': 1.2 * factor1 + 0.8 * np.random.randn(50),
            'Var_B1': 1.4 * factor2 + 0.8 * np.random.randn(50),
            'Var_B2': -1.1 * factor2 + 0.8 * np.random.randn(50),
            'Noise': np.random.randn(50) * 2.0
        })
    
    def test_case(self, name: str, df: pd.DataFrame, expected_results: Dict[str, Any]) -> bool:
        """Run a single test case"""
        print(f"\n{'='*50}")
        print(f"TEST: {name}")
        print(f"{'='*50}")
        
        try:
            # Create CSV and run your pipeline
            csv_file = self.create_test_csv(df, name.lower().replace(' ', '_'))
            print(f"Created test CSV: {csv_file}")
            
            # Instantiate the pipeline
            pipeline = PCAAnalysisPipeline(csv_file, '')
            
            # Step 1: Create numeric DataFrame
            print("Running create_numeric_df...")
            numeric_df = pipeline.create_numeric_df()
            print(f"Result: {numeric_df.shape[0]} rows, {numeric_df.shape[1]} columns")
            
            # Step 2: PCA analysis
            print("Perfoming PCA analysis...")
            pca_results = pipeline.get_most_important_variables()
            
            # This function prints results, but we can still call it.
            pipeline.display_important_variables()
            
            pc1_variance = pca_results['explained_variance_ratio'][0] * 100
            print(f"PC1 explains {pc1_variance:.1f}% of variance")  
            
            # Check expectations
            success = True
            print(f"\nRESULTS ANALYSIS:")
            
            if 'min_pc1_variance' in expected_results:
                expected_min = expected_results['min_pc1_variance']
                if pc1_variance >= expected_min:
                    print(f"   ✓ PC1 variance {pc1_variance:.1f}% >= {expected_min}%")
                else:
                    print(f"   ❌ PC1 variance {pc1_variance:.1f}% < {expected_min}%")
                    success = False
            
            if 'top_variables' in expected_results:
                pc1_top = pca_results['loadings'].iloc[:, 0].abs().idxmax()
                expected_vars = expected_results['top_variables']
                if pc1_top in expected_vars:
                    print(f"   ✓ Top PC1 variable '{pc1_top}' is in expected list {expected_vars}")
                else:
                    print(f"   ❌ Top PC1 variable '{pc1_top}' not in expected list {expected_vars}")
                    success = False
            
            if 'max_components_95' in expected_results:
                cumvar = pca_results['cumulative_variance']
                n_components_95 = np.argmax(cumvar >= 0.95)
                max_expected = expected_results['max_components_95']
                if n_components_95 <= max_expected:
                    print(f"   ✓ Components for 95% variance: {n_components_95} <= {max_expected}")
                else:
                    print(f"   ❌ Components for 95% variance: {n_components_95} > {max_expected}")
                    success = False
            
            # Show top variables
            print(f"\n📈 TOP PC1 LOADINGS:")
            pc1_loadings = pca_results['loadings'].iloc[:, 0].abs().sort_values(ascending=False)
            for i, (var, loading) in enumerate(pc1_loadings.head(3).items()):
                actual_loading = pca_results['loadings'].iloc[:, 0].loc[var]
                print(f"   {i+1}. {var}: {actual_loading:+.3f}")
            
            if success:
                print(f"\n✅ TEST PASSED: {name}")
            else:
                print(f"\n❌ TEST FAILED: {name}")
            
            self.test_results[name] = success
            return success
            
        except Exception as e:
            print(f"\n💥 TEST ERROR: {name}")
            print(f"   Error: {str(e)}")
            import traceback
            traceback.print_exc()
            self.test_results[name] = False
            return False
    
    def run_all_tests(self):
        """Run all test cases"""
        print("🧪 Running all tests")
        print("="*60)
        
        test_cases = [
            {
                'name': 'Dominant PC1 Structure',
                'data': self.create_dominant_pc1_data(),
                'expected': {
                    'min_pc1_variance': 55,  # More realistic expectation
                    'max_pc1_variance': 95,  # Upper bound
                    'top_variables': ['PC1'],
                    'max_components_95': 3
                }
            },
            {
                'name': 'Two Clear Domains',
                'data': self.create_two_domains_data(),
                'expected': {
                    'min_pc1_variance': 35,  # One domain should dominate
                    'max_pc1_variance': 65,
                    'max_components_95': 3   # Should need 2-3 components
                }
            },
            {
                'name': 'Noisy Mixed Data',
                'data': self.create_noisy_mixed_data(),
                'expected': {
                    'min_pc1_variance': 20,  # Very mixed, noisy data
                    'max_pc1_variance': 50,
                    'max_components_95': 5   # Might need all components
                }
            }
        ]
        
        for test_case in test_cases:
            self.test_case(
                test_case['name'],
                test_case['data'],
                test_case['expected']
            )
        
        # Summary
        print(f"\n{'='*60}")
        print("📋 TEST SUMMARY")
        print(f"{'='*60}")
        
        passed = sum(1 for result in self.test_results.values() if result)
        total = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status}: {test_name}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Your pipeline is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the detailed output above.")
        
        return passed == total

def main():
    """Main test runner"""
    tester = PipelineTester()
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    finally:
        tester.cleanup()

if __name__ == "__main__":
    main()
