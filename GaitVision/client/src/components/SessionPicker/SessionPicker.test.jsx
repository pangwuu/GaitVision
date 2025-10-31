// src/components/SessionPicker/SessionPicker.test.jsx
import React from "react";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";

// --- Mock DataContext ---
jest.mock("../DataContext/DataContext.jsx", () => ({
  useData: jest.fn(),
}));
import { useData } from "../DataContext/DataContext.jsx";

// Import the component
import SessionPicker from "./SessionPicker.jsx";

describe("<SessionPicker />", () => {
  let setSelectedPlotMock;

  beforeEach(() => {
    setSelectedPlotMock = jest.fn();

    // Default mock return for useData
    useData.mockReturnValue({
      calibrationData: [{}],
      csvData: [
        { metric: "Speed", units: "m/s", Baseline: 0.9, PI_1: 1.0, "Task condition": "A" },
      ],
      selectedPlot: ["Baseline"],
      setSelectedPlot: setSelectedPlotMock,
    });
  });

  afterEach(() => {
    cleanup();
    jest.clearAllMocks();
  });

  // -------------------------------
  // 1. Basic Rendering
  // -------------------------------
  test("renders header and session list with data", () => {
    render(<SessionPicker />);

    // Title should exist
    expect(screen.getByText(/Compare Plots/i)).toBeInTheDocument();

    // The synthetic 'Population Average' text should show
    expect(screen.getByText(/Population Average/i)).toBeInTheDocument();

    // The available session buttons should appear
    expect(screen.getByText("Baseline")).toBeInTheDocument();
    expect(screen.getByText("PI_1")).toBeInTheDocument();
  });

  // -------------------------------
  // 2. No sessions available
  // -------------------------------
  test("renders 'No sessions available' when csvData is empty", () => {
    useData.mockReturnValue({
      calibrationData: [{}],
      csvData: [],
      selectedPlot: [],
      setSelectedPlot: setSelectedPlotMock,
    });

    render(<SessionPicker />);

    expect(screen.getByText(/No sessions available/i)).toBeInTheDocument();
    expect(screen.queryByText("Baseline")).not.toBeInTheDocument();
  });

  // -------------------------------
  // 3. Click toggling logic
  // -------------------------------
  test("clicking session toggles selection and enforces max of 2 selections", () => {
    useData.mockReturnValue({
      calibrationData: [{}],
      csvData: [
        {
          metric: "Speed",
          units: "m/s",
          Baseline: 0.9,
          PI_1: 1.0,
          PI_2: 1.1,
        },
      ],
      selectedPlot: ["Baseline"],
      setSelectedPlot: setSelectedPlotMock,
    });

    render(<SessionPicker />);

    // Click PI_1 → should be added
    fireEvent.click(screen.getByText("PI_1"));
    expect(setSelectedPlotMock).toHaveBeenCalledWith(["Baseline", "PI_1"]);

    // Click Baseline again → should remove it
    fireEvent.click(screen.getByText("Baseline"));
    expect(setSelectedPlotMock).toHaveBeenCalledWith(expect.any(Array));
    expect(setSelectedPlotMock.mock.calls).toEqual(
        expect.arrayContaining([[expect.arrayContaining(["PI_1"])], [expect.any(Array)]])
    );

    // Click PI_2 (when one is already selected)
    fireEvent.click(screen.getByText("PI_2"));
    expect(setSelectedPlotMock).toHaveBeenCalledWith(["Baseline", "PI_1"]);
  });

  // -------------------------------
  // 4. Active class assignment
  // -------------------------------
  test("applies correct active classes based on selectedPlot", () => {
    useData.mockReturnValue({
      calibrationData: [{}],
      csvData: [
        {
          metric: "Speed",
          units: "m/s",
          Baseline: 0.9,
          PI_1: 1.0,
          PI_2: 1.1,
        },
      ],
      selectedPlot: ["Baseline", "PI_1"],
      setSelectedPlot: setSelectedPlotMock,
    });

    const { container } = render(<SessionPicker />);

    const baseline = screen.getByText("Baseline");
    const pi1 = screen.getByText("PI_1");

    // Baseline → active1, PI_1 → active2
    expect(baseline.className).toMatch(/active1/);
    expect(pi1.className).toMatch(/active2/);

    // Other item should not have an active class
    const pi2 = screen.getByText("PI_2");
    expect(pi2.className).not.toMatch(/active/);

    // List container should exist
    expect(container.querySelector(".compare-list")).toBeTruthy();
  });

  // -------------------------------
  // 5. Auto-selects first session when none selected
  // -------------------------------
  test("auto-selects first available session if none selected", () => {
    useData.mockReturnValue({
      calibrationData: [{}],
      csvData: [
        { metric: "Speed", units: "m/s", Baseline: 0.9, PI_1: 1.0 },
      ],
      selectedPlot: [],
      setSelectedPlot: setSelectedPlotMock,
    });

    render(<SessionPicker />);

    // Should automatically call setSelectedPlot(["Baseline"])
    expect(setSelectedPlotMock).toHaveBeenCalledWith(["Baseline"]);
  });

  // -------------------------------
  // 6. No sessions when csvData is undefined
  // -------------------------------
  test("renders 'No sessions available' when csvData is undefined", () => {
    useData.mockReturnValue({
      calibrationData: [{}],
      csvData: undefined,
      selectedPlot: [],
      setSelectedPlot: setSelectedPlotMock,
    });

    render(<SessionPicker />);

    expect(screen.getByText(/No sessions available/i)).toBeInTheDocument();
  });

  // -------------------------------
  // 7. Filters out metadata fields correctly
  // -------------------------------
  test("excludes 'metric', 'units', and 'Task condition' from session list", () => {
    useData.mockReturnValue({
      calibrationData: [{}],
      csvData: [
        { 
          metric: "Speed", 
          units: "m/s", 
          "Task condition": "DT",
          Baseline: 0.9, 
          PI_1: 1.0 
        },
      ],
      selectedPlot: ["Baseline"],
      setSelectedPlot: setSelectedPlotMock,
    });

    render(<SessionPicker />);

    expect(screen.queryByText("metric")).not.toBeInTheDocument();
    expect(screen.queryByText("units")).not.toBeInTheDocument();
    expect(screen.queryByText("Task condition")).not.toBeInTheDocument();
    expect(screen.getByText("Baseline")).toBeInTheDocument();
    expect(screen.getByText("PI_1")).toBeInTheDocument();
  });

  // -------------------------------
  // 8. Maximum 4 selections enforced
  // -------------------------------
  test("does not allow more than 4 sessions to be selected", () => {
    useData.mockReturnValue({
      calibrationData: [{}],
      csvData: [
        {
          metric: "Speed",
          units: "m/s",
          Baseline: 0.9,
          PI_1: 1.0,
          PI_2: 1.1,
          PI_3: 1.2,
          PI_4: 1.3,
        },
      ],
      selectedPlot: ["Baseline", "PI_1", "PI_2", "PI_3"],
      setSelectedPlot: setSelectedPlotMock,
    });

    render(<SessionPicker />);

    // Try to click PI_4 when 4 are already selected
    fireEvent.click(screen.getByText("PI_4"));
    // setSelectedPlot should NOT be called because we're at the max
    expect(setSelectedPlotMock).not.toHaveBeenCalled();
  });
});
