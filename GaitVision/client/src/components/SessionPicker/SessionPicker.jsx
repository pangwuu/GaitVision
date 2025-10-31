import { useEffect, useState } from "react";
import { useData } from "../DataContext/DataContext";

export default function SessionPicker() {
  const { calibrationData, csvData, selectedPlot, setSelectedPlot } = useData();

  const [sessions, setSessions] = useState([]);

  const selected = Array.isArray(selectedPlot)
  ? selectedPlot
  : selectedPlot
    ? [selectedPlot] // wraps selectedPLot if it's a string
    : [];

  useEffect(() => {
    if (calibrationData && Array.isArray(csvData) && csvData.length > 0) {
      // get keys from the first row
      const csvAllKeys = Object.keys(csvData[0] || {});
      // remove the metadata fields
      const csvSessionKeys = csvAllKeys.filter(
        (key) => key !== "metric" && key !== "units" && key !=="Task condition" && key!== "participant id" // made sure to remove Participant ID as a possible session
      );
      const sorted = csvSessionKeys.sort();
      setSessions(sorted);

      // keep selection valid (only sessions that still exist; cap to 2)
      const valid = selected.filter((p) => sorted.includes(p)).slice(0, 2);

      // if nothing selected yet, optionally auto-select the first one
      if (valid.length === 0 && sorted.length > 0) {
        setSelectedPlot([sorted[0]]);
      } else if (valid.length !== selected.length) {
        setSelectedPlot(valid);
      }
    } else {
      setSessions([]);
      setSelectedPlot([]);
    }
  }, [calibrationData, csvData]); 

  // toggle selection, but only allow up to 4
  const handleClick = (item) => {
    if (selected.includes(item)) {
      setSelectedPlot(selected.filter((p) => p !== item));
    } else if (selected.length < 4) {
      setSelectedPlot([...selected, item]);
    }
  };

  if (sessions.length === 0) {
    return (
      <div className="compare-section">
        <h3 className="compare-title">Compare Plots</h3>
        <div className="compare-list">
          <div className="compare-empty">
            No sessions available. 
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="compare-section">
      <h3 className="compare-title">Compare Plots</h3>

      <div className="compare-list">
        {/* <div className="normalised">Population Average</div> */}
        {sessions.map((item) => {
          const index = selectedPlot.indexOf(item);
          let activeClass = "";
          if (index === 0) activeClass = "active1";
          if (index === 1) activeClass = "active2";
          if (index === 2) activeClass = "active3";
          if (index === 3) activeClass = "active4";

          return (
            <div
              key={item}
              className={`compare-item ${activeClass}`}
              onClick={() => handleClick(item)}
            >
              {item}
            </div>
          );
        })}
      </div>
    </div>
  );
}