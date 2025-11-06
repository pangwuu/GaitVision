import React, { useState }  from "react";
import jsPDF from "jspdf";
import html2canvas from "html2canvas";
import autoTable from "jspdf-autotable";
import { tableStyles } from "./tableStyle";
import { useData } from "../DataContext/DataContext";
import logo from './pdf_logo_header.png';

// Helper function to build printable values
function toPrintable(v){
      if (v === undefined || v === null) return "N/A";
      if (typeof v === "string") return v;
      if (Array.isArray(v)) return v.length ? v.join("\n") : "N/A";
      if (v instanceof Set) return Array.from(v).length ? Array.from(v).join("\n") : "N/A";;
      if (typeof v === "object") {
        // simple object -> JSON (short)
        try {
          const s = JSON.stringify(v);
          return s.length > 200 ? s.slice(0, 197) + "..." : s;
        } catch {
          return String(v);
        }
      }
      return String(v);
}


// Z-score helper
export const calculateZScore = (metricName, value, calibrationData, selectedTask) => {
  if (!calibrationData) return null;

  const timepointToUse = "Baseline"; // Using baseline to calculate population average - to be used to determine z-score
  let calibData = calibrationData.find(
    (item) =>
      item.name === metricName &&
      (!selectedTask || item.condition === selectedTask) &&
      (!timepointToUse || item.timepoint === timepointToUse)
  );

  if (!calibData) {
    calibData = calibrationData.find((item) => item.name === metricName);
    if (!calibData) return null;
  }

  return ((value - calibData.mean) / calibData.stdev).toFixed(2);
};

export default function PdfDownloader({ targetRef, data}) {
  const [message, setMessage] = useState("");
  const { calibrationData, csvData, selectedMetrics, selectedPlot, selectedTask } = useData();
  
  
  // Convert values to printable
  const printableMetrics = toPrintable(selectedMetrics);
  const printablePlot = toPrintable(selectedPlot);
  const printableTask = toPrintable(selectedTask);

  const handleDownload = async () => {
    
    // If CSV or normalized data not ready OR user has not selected display overlays
    if (!data || !Array.isArray(data) || data.length === 0 || printableMetrics === "N/A") {
      setMessage("Please generate plot first!");
      setTimeout(() => setMessage(""), 3000);
      return;
    }
    
    const element = document.querySelector(`.${targetRef}`); // set as mid-panel in app.jsx (referring to panel with radar plot generated)
    if (!element) {
      console.error("Target element not found:", targetRef);
      setMessage("Please generate plot first!");
      setTimeout(() => setMessage(""), 3000);
      return;
    }

    // Create PDF
        const pdf = new jsPDF({
          orientation: "portrait",
          unit: "pt",
          format: "a4",
        });
    
    const pdfWidth = pdf.internal.pageSize.getWidth();
    const pdfHeight = pdf.internal.pageSize.getHeight();
    const margin = 55;
    pdf.setFont("helvetica");
        
    // Title Section
      // Logo
    pdf.addImage(logo, 'PNG', pdfWidth - (197+margin), 30, 197, 45);

      // Participant ID
    pdf.setFontSize(16)
    const p_ID = csvData.find(row => row["participant id"] != null)?.["participant id"] ?? null;

    pdf.text(`Participant ID: ${p_ID}`, margin, 50, {align: "left"} );
      // Date
    pdf.setFontSize(14)
    const now = new Date();
    const formatted_date = `${String(now.getDate()).padStart(2,'0')} ${now.toLocaleString('default', { month: 'long' })} ${now.getFullYear()}`
    pdf.text(formatted_date, margin,70,{align: "left"});
    
    pdf.setDrawColor(25, 83, 95)
    pdf.setLineWidth(1);
    pdf.line(margin, 83, (pdfWidth - margin), 83);
    
    // Tracking Y pos:
    let yPos = 120;
    
    // Body
      // Title
    pdf.setFontSize(18);
    pdf.setFont("helvetica","bold");
    pdf.text("Gait Metrics Analysis Report", pdfWidth / 2, yPos, { align: "center" });
    pdf.setFont("helvetica","normal");

    yPos = yPos + 30;
    
      // Chart Overview
    pdf.setFontSize(14)
    pdf.text("Chart Overview", margin, yPos, {align: "left"});
    yPos = yPos + 21;
        // Walk Task Condition
    pdf.setFontSize(12)
    pdf.text('Walk Task Condition:', 2* margin, yPos, {align: "left"});
    let task;
    switch(printableTask){
      case "ST":
        task = "Standard Task";
        break;
      case "HT":
        task = "Head-turn Task";
        break;
      case "DT":
        task = "Dual Task";
        break;
      default:
        task = "unknown";
    };
    pdf.text(`${task} (${printableTask})`,  pdfWidth/2 - margin, yPos,{align: "left"});
    yPos = yPos + 18;
        // Time Points
    pdf.text('Displayed Time Points:', 2*margin, yPos, {align: "left"});
    (printablePlot.split('\n')).forEach((line, i) => {
      let timePoint;
      if (line === "Baseline") {
        timePoint = "Baseline";
      } else {
        // match PI-X pattern
        const match = line.match(/^PI-(\d+)$/);
        if (match) {
          const number = parseInt(match[1], 10);
          const week = number === 1 ? "Week" : "Weeks"
          timePoint = `${number} ${week} Post Injury (${line})`;
        } else {
          timePoint = line;
        }
      }
      pdf.text(timePoint,  pdfWidth/2 - margin, yPos + i * 16, {align: "left"});
    });
    yPos += (16 * selectedPlot.length) + 6;

    // Don't know if I should include this or not
    // // Selected Metrics
    // const selectedMetricsArray = Array.isArray(selectedMetrics) ? selectedMetrics : Array.from(selectedMetrics);
    // pdf.text('Selected Metrics:', 2* margin, yPos, { align: "left" });
    // selectedMetricsArray.forEach((line, i) => {
    //   pdf.text(line.replace(/_/g, " "), pdfWidth/2 - margin , yPos + i * 16, { align: "left" });
    // });
    // yPos += (16 * selectedMetricsArray.length) + 6;

    // Radar Chart
      // Capture the element as a canvas
    const canvas = await html2canvas(element, { scale: 2 });
    const imgData = canvas.toDataURL("image/png");
      // Image
    const ratio = Math.min(
      (pdfWidth - 1.5* margin) / canvas.width, 
      (pdfHeight - yPos - 0.5* margin) / canvas.height
    );

    const imgWidth = canvas.width * ratio;
    const imgHeight = canvas.height * ratio;
    
    pdf.addImage(
      imgData,
      "PNG",
      (pdfWidth - imgWidth) / 2,
      yPos,
      imgWidth,
      imgHeight
    );
    yPos += imgHeight;
   
    pdf.addPage();
    yPos = margin

    // Table
    pdf.setFontSize(14)
    pdf.text("Chart Data Points", margin, yPos, {align: "left"});
    yPos += 18;
    
    if (csvData && csvData.length > 0) {
      const timepoints = Object.keys(csvData[0]).filter(
        (key) => !["metric", "units", "Task condition", "participant id"].includes(key)
      );
      const columns = [
        { header: "Gait Metric", dataKey: "metric" },
        { header: "Unit", dataKey: "unit" },
        { header: "Population Avg", dataKey: "popAvg" },
        ...timepoints.map((tp) => ({ header: tp, dataKey: tp })),
      ];
      const metricsToInclude = Array.isArray(selectedMetrics)
        ? selectedMetrics
        : Array.from(selectedMetrics);
      const normalizedMetrics = metricsToInclude.map((m) => m.replace(/_/g, " ")); // Normalize metric names (replace underscores with spaces)

      const rows = csvData
        .filter(
          (row) =>
            row.metric !== "Participant ID" &&
            normalizedMetrics.includes(row.metric) &&
            (!selectedTask || row["Task condition"] === selectedTask)
        )
        .map((row) => {
          const metricName = row.metric;
          const unit = row.units || "";

          // Always use Baseline for population average
          const popAvg = (() => {
            if (!calibrationData) return "N/A";

            const timepointToUse = "Baseline";
            let calibData = calibrationData.find(
              (item) =>
                item.name === metricName &&
                (!selectedTask || item.condition === selectedTask) &&
                (!timepointToUse || item.timepoint === timepointToUse)
            );

            if (!calibData) {
              // fallback to any metric record
              calibData = calibrationData.find((item) => item.name === metricName);
              if (!calibData) return "N/A";
            }

            return calibData.mean.toFixed(2);
          })();
          
          const timepointValues = {};
          for (const tp of timepoints) {
            const rawValue = row[tp];
            const num = parseFloat(rawValue);
            const value = isNaN(num) ? "–" : num.toFixed(2);
            const z = calculateZScore(metricName, num, calibrationData, selectedTask);
            
            timepointValues[tp] =
              value !== "–" && z !== null ? `${value}\n(Z=${z})` : "N/A";
          }
          return { metric: metricName, unit, popAvg, ...timepointValues };
        });

      autoTable(pdf, {
        startY: yPos,
        margin: { left: margin, right: margin },
        head: [columns.map((col) => col.header)],
        body: rows.map((row) => columns.map((col) => row[col.dataKey])),
        ...tableStyles,
      });
    
    }

    // Save File
    
    const timestamp = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}_` +
                      `${String(now.getHours()).padStart(2,'0')}-${String(now.getMinutes()).padStart(2,'0')}`;
    // Save PDF with participant ID and timestamp
    pdf.save(`GaitAnalysisReport_PID-${p_ID}_${timestamp}.pdf`);
  };

  return (
    <div>
      <button className="btn" onClick={handleDownload}>
        Download report 
      <span className="material-symbols-outlined">
        download
      </span>
      </button>
      {message && 
                <div style={{ color: "red", marginTop: "10px" }}>{message}
                </div>
      }
    </div>
  );
}