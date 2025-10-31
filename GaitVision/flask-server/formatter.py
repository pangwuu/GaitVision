import pandas as pd

def format_data(raw_json):
    data_list = raw_json["data"]
    if not data_list:
        print("Nothing provided")
        return []
    
    formatted = []

    # Only include numeric rows
    numeric_rows = [
        row for row in data_list
        if pd.notna(row["Timepoint (baseline/Postinjury)"])
        and row["Timepoint (baseline/Postinjury)"] not in ["Units"]
    ]

    # Get all possible metrics, drop NaN column headers
    all_keys = [str(k) for k in data_list[0].keys() if pd.notna(k)]
    metrics = [str(k) for k in data_list[0].keys()
        # if k not in ["Timepoint (baseline/Postinjury)", all_keys[0]] and pd.notna(k)]
        if k not in ["Timepoint (baseline/Postinjury)"] and pd.notna(k)]
    

    # Units row (handle NaN properly)
    units_row = [row for row in data_list if pd.isna(row["Timepoint (baseline/Postinjury)"])]
    units_map = {}
    if units_row:
        units_row = units_row[0]
        for metric in metrics:
            val = units_row.get(metric, "")
            units_map[metric] = "" if (isinstance(val, float) and pd.isna(val)) else val

    # Build formatted output
    for metric in metrics:
        grouped = {}
        for row in numeric_rows:
            tp = row["Timepoint (baseline/Postinjury)"]
            task = row.get("Walk Task Condition (ST/HT/ DT)", "")
            val = row.get(metric)
            id = row.get("Participant ID", None)

            if isinstance(val, float) and pd.isna(val):
                continue
            try:
                val = float(val)
            except (ValueError, TypeError):
                continue

            key = (metric, task)
            if key not in grouped:
                grouped[key] = {
                    "metric": metric,
                    "units": units_map.get(metric, ""),
                    "Task condition": task,
                    "participant id": id
                }
            grouped[key][tp] = val

        formatted.extend(grouped.values())

    return formatted
