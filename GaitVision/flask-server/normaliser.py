import pandas as pd

class Variable:
    def __init__(self, name: str, mean: float, stdev: float, timepoint: str = None, condition: str = None) -> None:
        self.name = name
        self.mean = mean
        self.stdev = stdev
        self.timepoint = timepoint
        self.condition = condition
    
    def to_dict(self):
        result = {'name': self.name, 'mean': self.mean, 'stdev': self.stdev}
        if self.timepoint:
            result['timepoint'] = self.timepoint
        if self.condition:
            result['condition'] = self.condition
        return result

def standardize_condition(condition):
    """Safely standardize walk task condition names"""
    if pd.isna(condition):
        return condition
    
    condition_str = str(condition).strip()
    
    # Map conditions to standard abbreviations - a bit inflexible...
    if 'single task' in condition_str.lower() or condition_str.upper() == 'ST':
        return 'ST'
    elif 'head turn' in condition_str.lower() or condition_str.upper() == 'HT':
        return 'HT'
    elif 'dual task' in condition_str.lower() or condition_str.upper() == 'DT':
        return 'DT'
    else:
        return condition_str  # Return as-is if no match

def standardize_timepoint(timepoint):
    """Safely standardize timepoint names"""
    if pd.isna(timepoint):
        return timepoint
    
    timepoint_str = str(timepoint).strip()
    
    # Extract PI-1, PI-2, etc. from various formats
    if 'post injury' in timepoint_str.lower() or 'pi' in timepoint_str.lower():
        # Look for a number
        import re
        match = re.search(r'(\d+)', timepoint_str)
        if match:
            return f'PI-{match.group(1)}'
    
    return timepoint_str 

def normalise_data(raw_df: pd.DataFrame):
    '''
    From a pandas DF of uploaded user csv data, we will return
    - Variables within the uploaded data that can be displayed
    - For each variable grouped by timepoint and condition:
      - mean
      - standard deviation
    - So data returned looks like
    {'name': 'VARIABLE NAME', 'mean': SOME NUMBER, 'stdev': SOME NUMBER, 'timepoint': PI-1 OR PI-2 PI-3, 'condition': ST, DT or HT}
    '''
    # Identify grouping columns
    timepoint_col = 'Timepoint'.lower()
    condition_col = 'Walk Task Condition'.lower()
        
    # Safely identify grouping columns by searching for keywords
    timepoint_col = next((col for col in raw_df.columns if 'timepoint' in col.lower()), None)
    condition_col = next((col for col in raw_df.columns if 'condition' in col.lower()), None)

    # Validate that we found the columns
    if timepoint_col is None:
        raise ValueError("Could not find a column containing 'timepoint'")
    if condition_col is None:
        raise ValueError("Could not find a column containing 'condition'")

    # Apply standardisation and clean the data a bit more
    raw_df[condition_col] = raw_df[condition_col].apply(standardize_condition)
    raw_df[timepoint_col] = raw_df[timepoint_col].apply(standardize_timepoint)

    # Get numeric columns (exclude grouping columns)
    numeric_cols = [col for col in raw_df.columns 
                    if col.lower().strip() not in [timepoint_col, condition_col] 
                    and 'participant id' not in col.lower()]
    
    variables = []

    # Get numeric columns (exclude grouping columns and participant ID)
    numeric_cols = [col for col in raw_df.columns
                    if col not in [timepoint_col, condition_col]
                    and 'participant' not in col.lower()
                    and not (col.lower().endswith('id') or col.lower().startswith('id') or 'participant id' in col.lower())]

    variables = []
    # Group by timepoint and condition
    grouped = raw_df.groupby([timepoint_col, condition_col])
    
    for (timepoint, condition), group in grouped:
        # Convert numeric columns to numeric type
        numeric_df = group[numeric_cols].apply(pd.to_numeric, errors="coerce")
        
        for column in numeric_df.columns:
            col_data = numeric_df[column].dropna()
            
            if len(col_data) > 0:  # Only calculate if we have data
                new_var = Variable(
                    name=column,
                    mean=float(col_data.mean()),
                    stdev=float(col_data.std()),
                    timepoint=timepoint,
                    condition=condition
                )
                variables.append(new_var.to_dict())
    
    return {"variables": variables}