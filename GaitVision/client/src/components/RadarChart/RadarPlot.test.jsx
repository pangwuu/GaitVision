// src/components/RadarChart/RadarPlot.test.jsx
import React from "react";
import { render, screen, cleanup, waitFor } from "@testing-library/react";

// Mock Chart.js
jest.mock("chart.js", () => ({ Chart: jest.fn() }));
jest.mock("chart.js/auto", () => ({}));

// Mock DataContext
jest.mock("../DataContext/DataContext.jsx", () => ({
  useData: jest.fn(),
  DataProvider: ({ children }) => <div>{children}</div>,
}));
const { useData: mockUseData } = require("../DataContext/DataContext.jsx");

import { Chart } from "chart.js";
import RadarPlot, { __test__ } from "./RadarPlot";
const { getLabels, getDatasets, getChartOptions, filteredData } = __test__;

// === SHARED TEST DATA ===
const athleteCsv = [
  {"metric": "Average Athlete Load", "units": "g", "Task condition": "ST", "Baseline": 0.1324, "PI-1": 0.1260, "PI-2": 0.2318, "PI-3": 0.9074},
  {"metric": "Average Double Support Ratio", "units": "ratio", "Task condition": "ST", "Baseline": 0.6275, "PI-1": 0.9970, "PI-2": 0.9946, "PI-3": 0.7263},
  {"metric": "Average Duty Factor", "units": "ratio", "Task condition": "ST", "Baseline": 0.6481, "PI-1": 0.8097, "PI-2": 0.9630, "PI-3": 0.8814}
];

const calibrationData = [
  {"name": "Average Athlete Load", "mean": 0.15, "stdev": 0.05, "condition": "ST", "timepoint": "Baseline"},
  {"name": "Average Double Support Ratio", "mean": 0.65, "stdev": 0.15, "condition": "ST", "timepoint": "Baseline"},
  {"name": "Average Duty Factor", "mean": 0.70, "stdev": 0.10, "condition": "ST", "timepoint": "Baseline"}
];

describe("<RadarPlot />", () => {
  let destroyMock;

  beforeEach(() => {
    HTMLCanvasElement.prototype.getContext = jest.fn(() => ({}));
    destroyMock = jest.fn();
    Chart.mockImplementation(() => ({
      destroy: destroyMock,
      update: jest.fn(),
    }));
    jest.spyOn(console, "log").mockImplementation(() => {});
    jest.spyOn(console, "warn").mockImplementation(() => {});
  });

  afterEach(() => {
    cleanup();
    jest.clearAllMocks();
  });

  // === UNIT TESTS ===
  describe("RadarPlot unit helpers", () => {
    test("getLabels wraps long names and appends units", () => {
      const labels = getLabels([
        { metric: "Very Long Metric Name That Exceeds", units: "cm" },
        { metric: "Short", units: "" },
      ]);
      expect(labels[0].some(l => l.includes("(cm)"))).toBe(true);
      expect(labels[1]).toEqual(["Short"]);
    });

    test("getDatasets computes valid z-scores for athlete metrics", () => {
      const ds = getDatasets(athleteCsv, ["Baseline"], calibrationData, "ST", "Baseline");
      const baseline = ds.find(d => d.label === "Baseline");
      baseline.data.forEach(v => expect(v).toBeGreaterThan(0));
    });

    test("getDatasets caps z-scores at ±3 and marks outliers", () => {
      const extremeData = [{ metric: "X", units: "", Baseline: 1000 }];
      const extremeCalib = [{ name: "X", mean: 0, stdev: 1, condition: "Walk", timepoint: "Baseline" }];
      const ds = getDatasets(extremeData, ["Baseline"], extremeCalib, "Walk", "T1");
      const baseline = ds.find(d => d.label === "Baseline");
      expect(baseline.data[0]).toBeCloseTo(4.0, 4);
      expect(baseline.pointStyle[0]).toBe("star");
    });

    test("getDatasets falls back to 2.5 when no calibration", () => {
      const missingCalib = [{ name: "Other", mean: 10, stdev: 2 }];
      const ds = getDatasets([{ metric: "Unknown", units: "", Baseline: 42 }], ["Baseline"], missingCalib, "Walk", "T1");
      const baseline = ds.find(d => d.label === "Baseline");
      expect(baseline.data[0]).toBe(2.5);
    });

    test("getChartOptions tooltip returns full label and z-score", () => {
      const data = [{ metric: "Average Athlete Load", units: "g", Baseline: 0.15 }];
      const options = getChartOptions(data, calibrationData, "ST", ["Baseline"]);
      const { title, label } = options.plugins.tooltip.callbacks;
      const t = title([{ dataIndex: 0, chart: { data: { rawLabels: ["Average Athlete Load (g)"], labels: [["Average", "Athlete", "Load", "(g)"]] } } }]);
      expect(t).toBe("Average Athlete Load (g)");
      const lines = label({ dataIndex: 0, dataset: { label: "Baseline" } });
      expect(lines[0]).toMatch(/Baseline:\s*0\.15/);
      expect(lines[1]).toMatch(/Z-Score:\s*/);
    });

    test("handles missing tooltip value gracefully", () => {
      const data = [{ metric: "Average Athlete Load", units: "g", Baseline: null }];
      const options = getChartOptions(data, calibrationData, "ST", ["Baseline"]);
      const { label } = options.plugins.tooltip.callbacks;

      const result = label({ dataIndex: 0, dataset: { label: "Baseline" } });
      expect(result === undefined || result[0].includes("Baseline")).toBe(true);
    });
  });

  // === COMPONENT TESTS ===
  describe("RadarPlot component behaviour", () => {
    beforeEach(() => jest.clearAllMocks());

    // ✅ FIX: data missing for guide test
    test("shows guide when data/calibration/selection missing", () => {
      mockUseData.mockReturnValue({
        csvData: [], // 👈 no CSV data
        calibrationData: [],
        selectedMetrics: new Set(),
        selectedPlot: [],
        selectedTask: null,
        selectedTimepoint: null,
        selectedCondition: null,
      });

      render(<RadarPlot />);
      expect(screen.getByText((text) => text.includes("Steps to Generate the Radar Chart"))).toBeInTheDocument();
      expect(Chart).not.toHaveBeenCalled();
    });

    // ✅ Chart render test - fully populated
    test("renders radar chart with all timepoints (Baseline, PI-1, PI-2, PI-3)", async () => {
      mockUseData.mockReturnValue({
        csvData: athleteCsv,
        calibrationData,
        selectedMetrics: new Set([
          "Average_Athlete_Load",
          "Average_Double_Support_Ratio",
          "Average_Duty_Factor",
        ]),
        selectedPlot: ["Baseline", "PI-1", "PI-2", "PI-3"],
        selectedTask: "ST",
        selectedTimepoint: null,
        selectedCondition: null,
      });

      render(<RadarPlot />);
      await waitFor(() => expect(Chart).toHaveBeenCalled());
      const config = Chart.mock.calls[0][1];
      const dsLabels = config.data.datasets.map(d => d.label);
      expect(dsLabels).toEqual(expect.arrayContaining(["Population Average", "Baseline", "PI-1", "PI-2", "PI-3"]));
    });

    test("shows warning when specific calibration missing but general exists", () => {
      const calibGeneralOnly = [
        { name: "Average Athlete Load", mean: 0.15, stdev: 0.05 },
        { name: "Average Duty Factor", mean: 0.7, stdev: 0.1 },
      ];
      mockUseData.mockReturnValue({
        csvData: athleteCsv,
        calibrationData: calibGeneralOnly,
        selectedMetrics: new Set(["Average_Athlete_Load", "Average_Double_Support_Ratio"]),
        selectedPlot: ["Baseline"],
        selectedTask: "ST",
        selectedTimepoint: null,
        selectedCondition: null,
      });
      render(<RadarPlot />);
      expect(screen.getByText(/Using general averages/i)).toBeInTheDocument();
    });

    test("handles invalid selectedPlot gracefully", () => {
      mockUseData.mockReturnValue({
        csvData: athleteCsv,
        calibrationData,
        selectedMetrics: new Set(["Average_Athlete_Load"]),
        selectedPlot: ["NonExistingPlot"],
        selectedTask: "ST",
        selectedTimepoint: null,
        selectedCondition: null,
      });
      render(<RadarPlot />);
      const config = Chart.mock.calls[0][1];
      const ds = config.data.datasets.map(d => d.label);
      expect(ds).toEqual(["Population Average"]);
    });
  });

  test("renders chart even when one timepoint is missing", () => {
    const partialCsv = athleteCsv.map(row => {
      const newRow = { ...row };
      delete newRow["PI-2"]; // giả lập mất dữ liệu cho một timepoint
      return newRow;
    });

    mockUseData.mockReturnValue({
      csvData: partialCsv,
      calibrationData,
      selectedMetrics: new Set([
        "Average_Athlete_Load",
        "Average_Double_Support_Ratio",
        "Average_Duty_Factor",
      ]),
      selectedPlot: ["Baseline", "PI-1", "PI-2", "PI-3"],
      selectedTask: "ST",
      selectedTimepoint: null,
      selectedCondition: null,
    });

    render(<RadarPlot />);
    const config = Chart.mock.calls[0][1];
    const dsLabels = config.data.datasets.map(d => d.label);

    expect(dsLabels).toContain("Baseline");
    expect(dsLabels).toContain("PI-1");
    expect(dsLabels).toContain("PI-3");
    expect(dsLabels).not.toContain("PI-2");
  });
});
