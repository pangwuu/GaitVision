import pytest
import pandas as pd
import numpy as np
from normaliser import Variable, standardize_condition, standardize_timepoint, normalise_data

class TestVariable:
    """Test the Variable class"""
    
    def test_variable_initialization_minimal(self):
        """Test Variable creation with minimal parameters"""
        var = Variable(name="Speed", mean=1.2, stdev=0.3)
        assert var.name == "Speed"
        assert var.mean == 1.2
        assert var.stdev == 0.3
        assert var.timepoint is None
        assert var.condition is None
    
    def test_variable_initialization_full(self):
        """Test Variable creation with all parameters"""
        var = Variable(
            name="Speed",
            mean=1.2,
            stdev=0.3,
            timepoint="PI-1",
            condition="ST"
        )
        assert var.name == "Speed"
        assert var.mean == 1.2
        assert var.stdev == 0.3
        assert var.timepoint == "PI-1"
        assert var.condition == "ST"
    
    def test_variable_to_dict_minimal(self):
        """Test to_dict method with minimal parameters"""
        var = Variable(name="Speed", mean=1.2, stdev=0.3)
        result = var.to_dict()
        assert result == {'name': 'Speed', 'mean': 1.2, 'stdev': 0.3}
    
    def test_variable_to_dict_full(self):
        """Test to_dict method with all parameters"""
        var = Variable(
            name="Speed",
            mean=1.2,
            stdev=0.3,
            timepoint="PI-1",
            condition="ST"
        )
        result = var.to_dict()
        assert result == {
            'name': 'Speed',
            'mean': 1.2,
            'stdev': 0.3,
            'timepoint': 'PI-1',
            'condition': 'ST'
        }


class TestStandardizeCondition:
    """Test the standardize_condition function"""
    
    def test_single_task_variations(self):
        """Test various single task condition formats"""
        assert standardize_condition("single task") == "ST"
        assert standardize_condition("Single Task") == "ST"
        assert standardize_condition("SINGLE TASK") == "ST"
        assert standardize_condition("ST") == "ST"
        assert standardize_condition("st") == "ST"
        assert standardize_condition("  single task  ") == "ST"
    
    def test_head_turn_variations(self):
        """Test various head turn condition formats"""
        assert standardize_condition("head turn") == "HT"
        assert standardize_condition("Head Turn") == "HT"
        assert standardize_condition("HEAD TURN") == "HT"
        assert standardize_condition("HT") == "HT"
        assert standardize_condition("ht") == "HT"
        assert standardize_condition("  head turn  ") == "HT"
    
    def test_dual_task_variations(self):
        """Test various dual task condition formats"""
        assert standardize_condition("dual task") == "DT"
        assert standardize_condition("Dual Task") == "DT"
        assert standardize_condition("DUAL TASK") == "DT"
        assert standardize_condition("DT") == "DT"
        assert standardize_condition("dt") == "DT"
        assert standardize_condition("  dual task  ") == "DT"
    
    def test_nan_handling(self):
        """Test that NaN values are handled properly"""
        assert pd.isna(standardize_condition(pd.NA))
        assert pd.isna(standardize_condition(np.nan))
    
    def test_unknown_condition(self):
        """Test that unknown conditions are returned as-is"""
        assert standardize_condition("Unknown") == "Unknown"
        assert standardize_condition("Custom Task") == "Custom Task"


class TestStandardizeTimepoint:
    """Test the standardize_timepoint function"""
    
    def test_post_injury_variations(self):
        """Test various post injury timepoint formats"""
        assert standardize_timepoint("post injury 1") == "PI-1"
        assert standardize_timepoint("Post Injury 2") == "PI-2"
        assert standardize_timepoint("POST INJURY 3") == "PI-3"
        assert standardize_timepoint("pi 1") == "PI-1"
        assert standardize_timepoint("PI 2") == "PI-2"
        assert standardize_timepoint("pi-3") == "PI-3"
    
    def test_nan_handling(self):
        """Test that NaN values are handled properly"""
        assert pd.isna(standardize_timepoint(pd.NA))
        assert pd.isna(standardize_timepoint(np.nan))
    
    def test_unknown_timepoint(self):
        """Test that unknown timepoints are returned as-is"""
        assert standardize_timepoint("Baseline") == "Baseline"
        assert standardize_timepoint("Follow-up") == "Follow-up"


class TestNormaliseData:
    """Test the normalise_data function"""
    
    def test_basic_calculation_single_group(self):
        """Test basic mean and stdev calculations for a single group"""
        df = pd.DataFrame({
            'Participant ID': [1, 2, 3, 4, 5],
            'Timepoint': ['PI-1', 'PI-1', 'PI-1', 'PI-1', 'PI-1'],
            'Walk Task Condition': ['ST', 'ST', 'ST', 'ST', 'ST'],
            'Speed': [1.0, 2.0, 3.0, 4.0, 5.0]
        })
        
        result = normalise_data(df)
        variables = result['variables']
        
        assert len(variables) == 1
        assert variables[0]['name'] == 'Speed'
        assert variables[0]['mean'] == 3.0
        assert variables[0]['stdev'] == pytest.approx(np.std([1, 2, 3, 4, 5], ddof=1))
        assert variables[0]['timepoint'] == 'PI-1'
        assert variables[0]['condition'] == 'ST'
    
    def test_multiple_conditions(self):
        """Test calculations across multiple conditions"""
        df = pd.DataFrame({
            'Participant ID': [1, 2, 3, 4, 5, 6],
            'Timepoint': ['PI-1'] * 6,
            'Walk Task Condition': ['ST', 'ST', 'ST', 'DT', 'DT', 'DT'],
            'Speed': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        })
        
        result = normalise_data(df)
        variables = result['variables']
        
        assert len(variables) == 2
        
        # Check ST group
        st_var = next(v for v in variables if v['condition'] == 'ST')
        assert st_var['mean'] == 2.0
        assert st_var['stdev'] == pytest.approx(1.0)
        
        # Check DT group
        dt_var = next(v for v in variables if v['condition'] == 'DT')
        assert dt_var['mean'] == 5.0
        assert dt_var['stdev'] == pytest.approx(1.0)
    
    def test_multiple_timepoints(self):
        """Test calculations across multiple timepoints"""
        df = pd.DataFrame({
            'Participant ID': [1, 2, 3, 4, 5, 6],
            'Timepoint': ['PI-1', 'PI-1', 'PI-1', 'PI-2', 'PI-2', 'PI-2'],
            'Walk Task Condition': ['ST'] * 6,
            'Speed': [1.0, 2.0, 3.0, 7.0, 8.0, 9.0]
        })
        
        result = normalise_data(df)
        variables = result['variables']
        
        assert len(variables) == 2
        
        # Check PI-1 group
        pi1_var = next(v for v in variables if v['timepoint'] == 'PI-1')
        assert pi1_var['mean'] == 2.0
        assert pi1_var['stdev'] == pytest.approx(1.0)
        
        # Check PI-2 group
        pi2_var = next(v for v in variables if v['timepoint'] == 'PI-2')
        assert pi2_var['mean'] == 8.0
        assert pi2_var['stdev'] == pytest.approx(1.0)
    
    def test_multiple_variables(self):
        """Test calculations with multiple numeric variables"""
        df = pd.DataFrame({
            'Participant ID': [1, 2, 3],
            'Timepoint': ['PI-1', 'PI-1', 'PI-1'],
            'Walk Task Condition': ['ST', 'ST', 'ST'],
            'Speed': [1.0, 2.0, 3.0],
            'Cadence': [100.0, 110.0, 120.0],
            'Stride Length': [0.5, 0.6, 0.7]
        })
        
        result = normalise_data(df)
        variables = result['variables']
        
        assert len(variables) == 3
        
        # Check all three variables exist
        var_names = {v['name'] for v in variables}
        assert var_names == {'Speed', 'Cadence', 'Stride Length'}
        
        # Check Speed calculations
        speed_var = next(v for v in variables if v['name'] == 'Speed')
        assert speed_var['mean'] == 2.0
        assert speed_var['stdev'] == pytest.approx(1.0)
        
        # Check Cadence calculations
        cadence_var = next(v for v in variables if v['name'] == 'Cadence')
        assert cadence_var['mean'] == 110.0
        assert cadence_var['stdev'] == pytest.approx(10.0)
    
    def test_complex_grouping(self):
        """Test calculations with multiple timepoints, conditions, and variables"""
        df = pd.DataFrame({
            'Participant ID': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            'Timepoint': ['PI-1', 'PI-1', 'PI-1', 'PI-1', 'PI-1', 'PI-1',
                         'PI-2', 'PI-2', 'PI-2', 'PI-2', 'PI-2', 'PI-2'],
            'Walk Task Condition': ['ST', 'ST', 'DT', 'DT', 'HT', 'HT',
                                   'ST', 'ST', 'DT', 'DT', 'HT', 'HT'],
            'Speed': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0],
            'Cadence': [100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210]
        })
        
        result = normalise_data(df)
        variables = result['variables']
        
        # Should have 2 timepoints * 3 conditions * 2 variables = 12 entries
        assert len(variables) == 12
        
        # Check a specific group: PI-1, ST, Speed
        pi1_st_speed = next(v for v in variables 
                           if v['timepoint'] == 'PI-1' 
                           and v['condition'] == 'ST' 
                           and v['name'] == 'Speed')
        assert pi1_st_speed['mean'] == 1.5
        assert pi1_st_speed['stdev'] == pytest.approx(np.std([1.0, 2.0], ddof=1))
        
        # Check another group: PI-2, HT, Cadence
        pi2_ht_cadence = next(v for v in variables 
                             if v['timepoint'] == 'PI-2' 
                             and v['condition'] == 'HT' 
                             and v['name'] == 'Cadence')
        assert pi2_ht_cadence['mean'] == 205.0
        assert pi2_ht_cadence['stdev'] == pytest.approx(np.std([200, 210], ddof=1))
    
    def test_condition_standardization_in_normalise(self):
        """Test that condition standardization works in normalise_data"""
        df = pd.DataFrame({
            'Participant ID': [1, 2, 3],
            'Timepoint': ['PI-1', 'PI-1', 'PI-1'],
            'Walk Task Condition': ['single task', 'Single Task', 'ST'],
            'Speed': [1.0, 2.0, 3.0]
        })
        
        result = normalise_data(df)
        variables = result['variables']
        
        # All should be grouped together as ST
        assert len(variables) == 1
        assert variables[0]['condition'] == 'ST'
        assert variables[0]['mean'] == 2.0
    
    def test_timepoint_standardization_in_normalise(self):
        """Test that timepoint standardization works in normalise_data"""
        df = pd.DataFrame({
            'Participant ID': [1, 2, 3],
            'Timepoint': ['post injury 1', 'Post Injury 1', 'PI-1'],
            'Walk Task Condition': ['ST', 'ST', 'ST'],
            'Speed': [1.0, 2.0, 3.0]
        })
        
        result = normalise_data(df)
        variables = result['variables']
        
        # All should be grouped together as PI-1
        assert len(variables) == 1
        assert variables[0]['timepoint'] == 'PI-1'
        assert variables[0]['mean'] == 2.0
    
    def test_participant_id_variations(self):
        """Test that participant ID columns are excluded regardless of case"""
        df = pd.DataFrame({
            'participant id': [1, 2, 3],
            'Timepoint': ['PI-1', 'PI-1', 'PI-1'],
            'Walk Task Condition': ['ST', 'ST', 'ST'],
            'Speed': [1.0, 2.0, 3.0]
        })
        
        result = normalise_data(df)
        variables = result['variables']
        
        # Should only have Speed, not participant id
        assert len(variables) == 1
        assert variables[0]['name'] == 'Speed'
    
    def test_precise_calculations(self):
        """Test precise statistical calculations"""
        # Known values for verification
        values = [10.5, 12.3, 15.7, 9.8, 14.2]
        expected_mean = np.mean(values)
        expected_stdev = np.std(values, ddof=1)
        
        df = pd.DataFrame({
            'Participant ID': list(range(len(values))),
            'Timepoint': ['PI-1'] * len(values),
            'Walk Task Condition': ['ST'] * len(values),
            'Measurement': values
        })
        
        result = normalise_data(df)
        variables = result['variables']
        
        assert len(variables) == 1
        assert variables[0]['mean'] == pytest.approx(expected_mean)
        assert variables[0]['stdev'] == pytest.approx(expected_stdev)
    
    def test_single_value_group(self):
        """Test calculation when a group has only one value"""
        df = pd.DataFrame({
            'Participant ID': [1],
            'Timepoint': ['PI-1'],
            'Walk Task Condition': ['ST'],
            'Speed': [5.0]
        })
        
        result = normalise_data(df)
        variables = result['variables']
        
        assert len(variables) == 1
        assert variables[0]['mean'] == 5.0
        # Standard deviation of single value should be NaN or 0
        assert np.isnan(variables[0]['stdev']) or variables[0]['stdev'] == 0.0
    
    def test_missing_timepoint_column_raises_error(self):
        """Test that missing timepoint column raises ValueError"""
        df = pd.DataFrame({
            'Participant ID': [1, 2, 3],
            'Walk Task Condition': ['ST', 'ST', 'ST'],
            'Speed': [1.0, 2.0, 3.0]
        })
        
        with pytest.raises(ValueError, match="Could not find a column containing 'timepoint'"):
            normalise_data(df)
    
    def test_missing_condition_column_raises_error(self):
        """Test that missing condition column raises ValueError"""
        df = pd.DataFrame({
            'Participant ID': [1, 2, 3],
            'Timepoint': ['PI-1', 'PI-1', 'PI-1'],
            'Speed': [1.0, 2.0, 3.0]
        })
        
        with pytest.raises(ValueError, match="Could not find a column containing 'condition'"):
            normalise_data(df)
    
    def test_column_name_case_insensitivity(self):
        """Test that column detection is case-insensitive"""
        df = pd.DataFrame({
            'PARTICIPANT ID': [1, 2, 3],
            'TIMEPOINT': ['PI-1', 'PI-1', 'PI-1'],
            'WALK TASK CONDITION': ['ST', 'ST', 'ST'],
            'Speed': [1.0, 2.0, 3.0]
        })
        
        result = normalise_data(df)
        variables = result['variables']
        
        assert len(variables) == 1
        assert variables[0]['name'] == 'Speed'
        assert variables[0]['mean'] == 2.0