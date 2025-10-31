import { useState } from 'react';
import './SearchBox.css'; // Import the CSS file

export function SearchBox({ onSearchChange, resultCount, totalCount }) {
  const [searchTerm, setSearchTerm] = useState('');

  const handleChange = (e) => {
    const value = e.target.value;
    setSearchTerm(value);
    onSearchChange(value);
  };

  const handleClear = () => {
    setSearchTerm('');
    onSearchChange('');
  };

  return (
    <div className="search-box-container">
      <div className="search-input-wrapper">
        <span className="material-symbols-outlined search-icon">
            search
        </span>
        <input
          type="text"
          placeholder="Search variables..."
          value={searchTerm}
          onChange={handleChange}
          className="search-input"
        />
        {searchTerm && (
          <button
            onClick={handleClear}
            className="search-clear-btn"
          >
        <span className="material-symbols-outlined">
        backspace
        </span>
          </button>
        )}
      </div>
      {searchTerm && (
        <div className="search-results-count">
          {resultCount} of {totalCount} variables
        </div>
      )}
    </div>
  );
}
