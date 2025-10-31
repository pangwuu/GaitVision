import { useState, useEffect } from 'react';
import { useData } from '../DataContext/DataContext';
import { SearchBox } from './SearchBox';
import './VariablePicker.css'; // Import the new stylesheet

// Helper component for displaying PCA suggestions
function PcaSuggestions() {
  const { pcaSuggestions } = useData();

  if (!pcaSuggestions) {
    return null;
  }

  // Sort suggestions by importance (descending) and take the top 5
  const topSuggestions = Object.entries(pcaSuggestions)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5)
    .map(([name]) => name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()));

  if (topSuggestions.length === 0) {
    return null;
  }

  return (
    <div className="pca-suggestions-box">
      <h4 className="pca-suggestions-header">Top 5 Suggested Variables</h4>
      <ul className="pca-suggestions-list">
        {topSuggestions.map(variableName => (
          <li key={variableName} className="pca-suggestion-item">
            <span class="material-symbols-outlined">
              arrow_right_alt
            </span>
            {variableName}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function VariablePicker() {
  const { calibrationData, csvData, selectedMetrics, setSelectedMetrics, selectedTask, selectedTimepoint, selectedCondition } = useData();
  const [variables, setVariables] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');

  const toggleMetric = (name) => {
    const newSelected = new Set(selectedMetrics);
    if (newSelected.has(name)) {
      newSelected.delete(name);
    } else {
      newSelected.add(name);
    }
    setSelectedMetrics(newSelected);
    console.log('Currently selected variables:', Array.from(newSelected));
  };

  useEffect(() => {
    if (calibrationData && Array.isArray(csvData)) {
      const filteredData = csvData.filter(row =>
        (!selectedTask || row["Task condition"] === selectedTask) &&
        (!selectedTimepoint || row["Timepoint"] === selectedTimepoint) &&
        (!selectedCondition || row["Condition"] === selectedCondition)
      );
      const calibrationVars = new Set(calibrationData.map(v => v.name.replace(/\s+/g, "_")));
      const csvVars = new Set(filteredData.map(item => item.metric.replace(/\s+/g, "_")));
      const commonVars = [...calibrationVars].filter(name => csvVars.has(name));
      setVariables(commonVars.sort());

      const newSelected = new Set(selectedMetrics);
      let changed = false;
      for (const metric of newSelected) {
        if (!commonVars.includes(metric)) {
          newSelected.delete(metric);
          changed = true;
        }
      }
      if (changed) {
        setSelectedMetrics(newSelected);
      }
    } else {
      setVariables([]);
    }
  }, [calibrationData, csvData, selectedTask, selectedTimepoint, selectedCondition, selectedMetrics, setSelectedMetrics]);

  // Filter variables based on search term
  // Normalize search term by replacing spaces with underscores to match backend variable format
  const normalizedSearchTerm = searchTerm.toLowerCase().replace(/\s+/g, '_');
  const filteredVariables = variables.filter(name =>
    name.toLowerCase().includes(normalizedSearchTerm)
  );

  if (variables.length === 0) {
    return (
      <div className="file-header">Selected Variables
        <div>
          No variables available for selection.
          Please use the "Calibrate and Suggest" button to obtain a list of selectable variables.
        </div>
      </div>
    );
  }

  return (
    <div className="file-info" style={{ maxHeight: '50vh', overflowY: 'auto' }}>
      <div className="file-info">
        <div className="file-header">Select Variables</div>
                {/* Search Input */}
        <SearchBox 
          onSearchChange={setSearchTerm}
          resultCount={filteredVariables.length}
          totalCount={variables.length}
        />        

        {/* PCA Suggestions Box */}
        <PcaSuggestions />
        
        {/* Variables List */}
        {filteredVariables.map((name) => {
          const isSelected = selectedMetrics.has(name);

          // Format for display only
          const displayName = name
            .replace(/_/g, ' ')          // replace underscores with spaces
            .replace(/\b\w/g, c => c.toUpperCase()); // capitalise each word

          return (
            <div
              key={name}
              className={`metric-item ${isSelected ? "selected" : ""}`}
              onClick={() => toggleMetric(name)}
            >
              <div className={`metric-radio ${isSelected ? "checked" : ""}`} />
              <div className="metric-label">{displayName}</div>
            </div>
          );
        })}
        
        <div className="scrollbar">
          <div className="scrollbar-thumb" />
        </div>
      </div>
    </div>
  );
}