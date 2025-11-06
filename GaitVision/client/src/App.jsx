import "./App.css";
import CsvUploader from "./components/CsvUploader/CsvUploader.jsx";
import RadarPlot from "./components/RadarChart/RadarPlot.js";
import PdfDownloader from "./components/PdfDownloader/PdfDownloader.jsx";
import Calibrator from "./components/Calibrator/Calibrator.jsx";
import VariablePicker from "./components/VariablePicker/VariablePicker.jsx";
import { useData } from "./components/DataContext/DataContext.jsx";
import SessionPicker from "./components/SessionPicker/SessionPicker.jsx";
import TaskPicker from "./components/TaskPicker/TaskPicker.jsx";


export default function App() {
  // Changed to use DataContext to find necessary data
  const { csvData } = useData();
  
  
  return (
    <div>
      <h1>
        <span className="gait">Gait</span>
        <span className="vision">Vision</span>
      </h1>

      <div className="content">
        <div className="left-panel">
          <div className="calibrator">
            <Calibrator />
          </div>
          
          <div className="csv-upload">
            <CsvUploader />
          </div>

          <div>
            <VariablePicker />
          </div>

          
        </div>        

        <div className="mid-panel">
          <div className="radar-plot">
            <RadarPlot data={csvData}/>
          </div>
        </div>

        <div className="right-panel">
          <TaskPicker />
          <SessionPicker />

          <div className="download-section">
            <PdfDownloader targetRef="mid-panel" data={csvData} />
          </div>
          </div>
      </div>
    </div>
  );
}
