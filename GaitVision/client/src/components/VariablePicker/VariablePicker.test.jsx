// src/components/VariablePicker/VariablePicker.test.jsx
import React from "react";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";

// --- Mock useData from DataContext ---
jest.mock("../DataContext/DataContext.jsx", () => ({
  useData: jest.fn(),
}));
import { useData } from "../DataContext/DataContext.jsx";

import VariablePicker from "./VariablePicker.jsx";

describe("<VariablePicker />", () => {
  let setSelectedMetricsMock;

  beforeEach(() => {
    setSelectedMetricsMock = jest.fn();
    // Hide warnings during tests
    jest.spyOn(console, "warn").mockImplementation(() => {});
    jest.spyOn(console, "log").mockImplementation(() => {});

    useData.mockReturnValue({
      calibrationData: [
        { name: "Stride Length" },
        { name: "Step Width" },
        { name: "Velocity" },
      ],
      csvData: [
        { metric: "Stride_Length", "Task condition": "Walk_10m", Timepoint: "T1", Condition: "Pre" },
        { metric: "Step_Width", "Task condition": "Walk_10m", Timepoint: "T1", Condition: "Pre" },
        { metric: "HeartRate", "Task condition": "Walk_20m", Timepoint: "T1", Condition: "Pre" },
      ],
      selectedMetrics: new Set(["Stride_Length"]),
      setSelectedMetrics: setSelectedMetricsMock,
      selectedTask: "Walk_10m",
      selectedTimepoint: "T1",
      selectedCondition: "Pre",
    });
  });

  afterEach(() => {
    cleanup();
    jest.clearAllMocks();
  });

  test("renders common variables between calibrationData and csvData", () => {
    render(<VariablePicker />);

    // Expected common metrics are Stride_Length and Step_Width
    expect(screen.getByText("Stride_Length")).toBeInTheDocument();
    expect(screen.getByText("Step_Width")).toBeInTheDocument();
    expect(screen.queryByText("Velocity")).not.toBeInTheDocument(); // Not in CSV
    expect(screen.queryByText("HeartRate")).not.toBeInTheDocument(); // Not in calibrationData
  });

  test("renders empty message when calibrationData is null", () => {
    useData.mockReturnValue({
      calibrationData: null,
      csvData: [],
      selectedMetrics: new Set(),
      setSelectedMetrics: setSelectedMetricsMock,
      selectedTask: null,
      selectedTimepoint: null,
      selectedCondition: null,
    });

    render(<VariablePicker />);

    expect(
      screen.getByText(/No variables avaliable for selection/i)
    ).toBeInTheDocument();
  });

  // ------------------------------------------------------------
  // 3️⃣ Toggles metric selection when clicked
  // ------------------------------------------------------------
  test("clicking a variable toggles its selection state", () => {
    render(<VariablePicker />);

    const stride = screen.getByText("Stride_Length");
    const step = screen.getByText("Step_Width");

    // Click to toggle selection
    fireEvent.click(step);
    expect(setSelectedMetricsMock).toHaveBeenCalled();

    // Click again to deselect
    fireEvent.click(stride);
    expect(setSelectedMetricsMock).toHaveBeenCalledTimes(2);
  });

  test("filters variables based on task/timepoint/condition", () => {
    useData.mockReturnValue({
      calibrationData: [
        { name: "Velocity" },
        { name: "HeartRate" },
        { name: "Stride Length" },
      ],
      csvData: [
        { metric: "Velocity", "Task condition": "Walk_10m", Timepoint: "T1", Condition: "Pre" },
        { metric: "HeartRate", "Task condition": "Walk_20m", Timepoint: "T2", Condition: "Post" },
      ],
      selectedMetrics: new Set(),
      setSelectedMetrics: setSelectedMetricsMock,
      selectedTask: "Walk_10m",
      selectedTimepoint: "T1",
      selectedCondition: "Pre",
    });

    render(<VariablePicker />);

    // Only Velocity matches filters
    expect(screen.getByText("Velocity")).toBeInTheDocument();
    expect(screen.queryByText("HeartRate")).not.toBeInTheDocument();
  });

  test("removes previously selected metrics if no longer valid", () => {
    useData.mockReturnValue({
      calibrationData: [{ name: "Stride Length" }],
      csvData: [
        { metric: "Stride_Length", "Task condition": "Walk_10m", Timepoint: "T1", Condition: "Pre" },
      ],
      selectedMetrics: new Set(["Nonexistent_Var"]),
      setSelectedMetrics: setSelectedMetricsMock,
      selectedTask: "Walk_10m",
      selectedTimepoint: "T1",
      selectedCondition: "Pre",
    });

    render(<VariablePicker />);

    // Should call setter to remove invalid variable
    expect(setSelectedMetricsMock).toHaveBeenCalled();
    const callArgs = Array.from(setSelectedMetricsMock.mock.calls[0][0]);
    expect(callArgs).not.toContain("Nonexistent_Var");
  });

  test("handles non-array csvData without crashing", () => {
    useData.mockReturnValue({
      calibrationData: [{ name: "Velocity" }],
      csvData: null, // invalid
      selectedMetrics: new Set(),
      setSelectedMetrics: setSelectedMetricsMock,
      selectedTask: null,
      selectedTimepoint: null,
      selectedCondition: null,
    });

    render(<VariablePicker />);

    expect(
      screen.getByText(/No variables avaliable for selection/i)
    ).toBeInTheDocument();
  });
});
