import React, { useEffect, useRef, useMemo } from "react";
import { Chart } from "chart.js";
import "chart.js/auto";
import { useData } from "../DataContext/DataContext";

const baselineName = "Baseline";

function getLabels(data) {
    return data.map(d => {
    const maxLen = 15; // Maximum number of words in one line
    const words = d.metric.split(" ");
    let lines = [];
    let line = "";
    for (let w of words) {
        if ((line + " " + w).trim().length <= maxLen) {
        line = (line + " " + w).trim();
        } else {
        lines.push(line);
        line = w;
        }
    }
    if (line) lines.push(line);
    return (d.units !== '') ? [...lines, `(${d.units})`]: [...lines];
    });
}

function getDatasets(data, selectedPlot, calibrationData, selectedTask, selectedTimepoint) {
    if (!data || data.length === 0 || !selectedPlot) return [];


    // Helper function to calculate z-score, now context-aware
    const calculateZScore = (metricName, value, plotName) => {
        if (!calibrationData) {
            console.warn('Calibration data not loaded');
            return null;
        }
        
        // Force comparison to Baseline values
        const timepointToUse = baselineName;

        let calibData = calibrationData.find(item => 
            item.name === metricName &&
            (!selectedTask || item.condition === selectedTask) &&
            (!timepointToUse || item.timepoint === timepointToUse)
        );
        
        if (!calibData) {
            // Fallback to find by name only if context-specific is not found
            calibData = calibrationData.find(item => item.name === metricName);
            if (calibData) {
                console.warn(`No specific calibration data for ${metricName} could be found using baseline data. Using averages from all timepoints`);
            } else {
                console.warn(`No calibration data found for metric: ${metricName}`);
                return null;
            }
        }
        
        const zScore = (value - calibData.mean) / calibData.stdev;

        return zScore;
    };

    const datasets = [];
    const plotsArray = Array.isArray(selectedPlot) ? selectedPlot : [selectedPlot];
    const colors = [
    "rgba(76, 175, 80)",    // active1 — green (#4caf50)
    "rgba(33, 150, 243)",   // active2 — blue (#2196f3)
    "rgba(184, 134, 11)",   // active3 — dark yellow (#B8860B)
    "rgba(199, 21, 133)"    // active4 — dark pink (#C71585)
    ];


    
    datasets.push({
        label: "Population Average",
        data: data.map(() => 2.5), // The z-score of 0 is transformed to 2.5
        borderColor: "rgba(255, 0, 0, 1)",
        backgroundColor: "rgba(255, 0, 0, 0)",
        borderDash: [6, 3],
        pointBackgroundColor: "rgba(255, 0, 0, 1)",
        pointBorderColor: "rgba(255, 0, 0, 1)",
        pointHoverBackgroundColor: "rgba(255, 0, 0, 1)",
        pointHoverBorderColor: "rgba(255, 0, 0, 1)",
        borderWidth: 2,
        pointRadius: 0,
    });
    
    plotsArray.forEach((plot, idx) => {
        if (!data[0] || !(plot in data[0])) return;

        // Pass the plot name to calculateZScore
        const zScores = data.map(d => calculateZScore(d.metric, d[plot], plot));

        const transformedValues = zScores.map(z => {
            if (z === null) return 2.5; // Default to population average if z-score fails
            const cappedZ = Math.max(-3, Math.min(3, z));
            return 0.5 * cappedZ + 2.5;
        });

        const pointRadii = zScores.map(z => (z !== null && (z > 3 || z < -3)) ? 7 : 4);
        const pointStyles = zScores.map(z => (z !== null && (z > 3 || z < -3)) ? 'star' : 'circle');
        const pointBorderWidths = zScores.map(z => (z !== null && (z > 3 || z < -3)) ? 2 : 1);

        const color = colors[idx % colors.length];

        datasets.push({
            label: plot,
            data: transformedValues,
            borderColor: color,
            backgroundColor: color.replace(")", ",0.4)"),
            pointBackgroundColor: color,
            pointBorderColor: color,
            pointHoverBackgroundColor: color,
            pointHoverBorderColor: color.replace(")", ",1)"),
            pointRadius: pointRadii,
            pointStyle: pointStyles,
            pointBorderWidth: pointBorderWidths,
            borderWidth: 0,
        });
    });
    return datasets;
}

function getChartOptions(data, calibrationData, selectedTask, selectedPlot) {

    // Helper function to calculate z-score, now context-aware
    const calculateZScore = (metricName, value, datasetLabel) => {
        if (!calibrationData) return null;
        
        // Force comparison to baseline
        const timepointToUse = baselineName;
        
        let calibData = calibrationData.find(item => 
            item.name === metricName &&
            (!selectedTask || item.condition === selectedTask) &&
            (!timepointToUse || item.timepoint === timepointToUse)
        );


        if (!calibData) {
            calibData = calibrationData.find(item => item.name === metricName);
            if (!calibData) return null;
        }

        return (value - calibData.mean) / calibData.stdev;
    };

    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { position: "bottom" },
            tooltip: {
                callbacks: {
                    title: function (context) {
                        if (!context || context.length === 0) return '';
                            const chart = context[0].chart;
                            const index = context[0].dataIndex;

                        // Use full, uncropped label
                        if (chart.data.rawLabels && chart.data.rawLabels[index]) {
                            return chart.data.rawLabels[index];
                        }
                        // Fallback to wrapped label if needed
                        return chart.data.labels[index] || '';
                    },
                    label: function(context) {
                        const idx = context.dataIndex;
                        const datasetLabel = context.dataset.label || "";
                        const d = data[idx];
                        const rawValue = d[datasetLabel];
                        
                        if (datasetLabel === "Population Average") {
                            return "Population Average (Z-Score: 0)";
                        }

                        // Pass the dataset label (plot name) to calculateZScore
                        const zScore = calculateZScore(d.metric, rawValue, datasetLabel);
                        if (zScore !== null && rawValue!== null) {
                            return [
                                `${datasetLabel}: ${rawValue.toFixed(2)}`,
                                `Z-Score: ${zScore.toFixed(2)}`
                            ];
                        }
                    }
                }
            },
        },
        scales: {
            r: {
                min: 1,
                max: 4,
                angleLines: { display: false },
                grid: { color: "#BEBDB8", lineWidth: 2 },
                pointLabels: { color: "#333", font: { size: 14 } },
                ticks: { 
                    color: "#666",
                    stepSize: 0.5,
                    callback: function(value, index, ticks) {
                        const originalZ = 2 * value - 5;
                        // Only show integer z-scores
                        if (originalZ % 1 === 0) {
                            return originalZ;
                        }
                    }
                },
            },
        },
    };
}

function createRadarChart(ctx, data, selectedPlot, calibrationData, selectedTask, selectedTimepoint) {
    const fullLabels = data.map(d => d.units ? `${d.metric} (${d.units})` : d.metric);

    return new Chart(ctx, {
        type: "radar",
        data: {
            labels: getLabels(data), // wrapped labels for display
            rawLabels: fullLabels,   // full labels for tooltip
            datasets: getDatasets(data, selectedPlot, calibrationData, selectedTask, selectedTimepoint),
        },
        options: getChartOptions(data, calibrationData, selectedTask, selectedPlot),
    });
}

export default function RadarPlot() {
    const { csvData, selectedMetrics, selectedPlot, calibrationData, selectedTask, selectedTimepoint, selectedCondition } = useData();
    const [showCalibWarning, setShowCalibWarning] = React.useState(false);
    const canvasRef = useRef(null);
    const chartRef = useRef(null);

    const filteredData = useMemo(() => {
        if (!Array.isArray(csvData) || !selectedMetrics || selectedMetrics.size === 0) {
            return [];
        }
        const selectedArray = [...selectedMetrics];
        return csvData.filter(item =>
            selectedArray.includes(item.metric.replace(/\s+/g, "_")) &&
            (!selectedTask || item["Task condition"] === selectedTask) &&
            (!selectedTimepoint || item["Timepoint"] === selectedTimepoint) &&
            (!selectedCondition || item["Condition"] === selectedCondition)
        );
    }, [csvData, selectedMetrics, selectedTask, selectedTimepoint, selectedCondition]);

    useEffect(() => {
        if (!calibrationData || filteredData.length === 0 || !selectedPlot || selectedPlot.length === 0) {
            setShowCalibWarning(false);
            return;
        }

        let fallbackUsed = false;
        for (const plot of selectedPlot) {
            if (fallbackUsed) break;
            for (const metricData of filteredData) {
                const metricName = metricData.metric;
                const timepointToUse = plot;

                const hasSpecific = calibrationData.some(item => 
                    item.name === metricName &&
                    (!selectedTask || item.condition === selectedTask) &&
                    (!timepointToUse || item.timepoint === timepointToUse)
                );

                if (!hasSpecific) {
                    const hasGeneral = calibrationData.some(item => item.name === metricName);
                    if (hasGeneral) {
                        fallbackUsed = true;
                        break;
                    }
                }
            }
        }
        setShowCalibWarning(fallbackUsed);
    }, [filteredData, calibrationData, selectedTask, selectedPlot]);

    useEffect(() => {
        if (!canvasRef.current) return;
        const ctx = canvasRef.current.getContext("2d");

        if (chartRef.current) {
            chartRef.current.destroy();
        }


        // if (filteredData.length < 3 ) {
        //     chartRef.current = null;
        // } else {
        //     chartRef.current = createRadarChart(ctx, filteredData, selectedPlot, calibrationData, selectedTask, selectedTimepoint);
        // }
        chartRef.current = createRadarChart(ctx, filteredData, selectedPlot, calibrationData, selectedTask, selectedTimepoint);

        return () => {
            if (chartRef.current) {
                chartRef.current.destroy();
            }
        };
    }, [filteredData, selectedPlot, calibrationData, selectedTask, selectedTimepoint]);

    return (
        <div style={{ width: "40vw", margin: "0 auto", textAlign: "center" }}>
            <h2 style={{ fontSize: 18, margin: "4px 0" }}>Gait Radar Chart</h2>
            {showCalibWarning && (
                <div
                    style={{
                        color: "#856404",
                        backgroundColor: "#fff3cd",
                        border: "1px solid #ffeeba",
                        padding: "10px",
                        borderRadius: "5px",
                        marginBottom: "15px",
                    }}
                >
                    Warning: Specific calibration data not found for the current context. Using general averages.
                </div>
            )}
            
            {(!csvData || csvData.length === 0 || !calibrationData || calibrationData.length === 0 || selectedMetrics.size === 0) ? (
                <div
                    style={{
                        width: "100%",
                        aspectRatio: "1.1 / 1",
                        color: "#333",
                        backgroundColor: "#f8f9fa",
                        textAlign: "left",
                        fontSize: "16px",
                        lineHeight: "1.8",
                    }}
                >
                    <h3 style={{ textAlign: "center", color: "#005f73", marginBottom: "10px" }}>
                        Steps to Generate the Radar Chart
                    </h3>
                    <ul style={{ paddingLeft: "50px" }}>
                        <li><strong>Step 1:</strong> Upload the <em>Calibration Data</em> to get the recommended variables from PCA analysis.</li>
                        <li><strong>Step 2:</strong> Upload the <em>Patient CSV file</em>.</li>
                        <li><strong>Step 3:</strong> Select variables from the list.</li>
                        <li><strong>Step 4:</strong> Select the <em>Walk task condition</em>.</li>
                        <li><strong>Step 5:</strong> Select the <em>Compare plots</em>.</li>
                        <li><strong>Step 6:</strong> Download the report.</li>
                    </ul>
                    <p style={{ textAlign: "center", marginTop: "15px", color: "#6c757d" }}>
                        Once all steps are completed, your radar chart will appear here.
                    </p>
                </div>
            ) : (
                <div
                    style={{
                        width: "100%",
                        aspectRatio: "1.1 / 1",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        flexDirection: "column",
                    }}
                >
                    <canvas ref={canvasRef} style={{ width: "100%", height: "100%" }} />
                </div>
            )}
        </div>
    );
    
}

export const __test__ = { getLabels, getDatasets, getChartOptions };
