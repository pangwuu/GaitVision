// src/components/TaskPicker/TaskPicker.test.jsx
import React from "react";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";

// --- Mock useData from DataContext ---
jest.mock("../DataContext/DataContext.jsx", () => ({
  useData: jest.fn(),
}));
import { useData } from "../DataContext/DataContext.jsx";

// --- Import component under test ---
import TaskPicker from "./TaskPicker.jsx";

describe("<TaskPicker />", () => {
  let setSelectedTaskMock;

  beforeEach(() => {
    setSelectedTaskMock = jest.fn();

    // Default mock values
    useData.mockReturnValue({
      calibrationData: [{}],
      csvData: [
        { "Task condition": "Walk_10m", Timepoint: "T1", Condition: "Pre" },
        { "Task condition": "Walk_20m", Timepoint: "T1", Condition: "Pre" },
        { "Task condition": "Walk_10m", Timepoint: "T2", Condition: "Post" },
      ],
      selectedTask: "Walk_10m",
      setSelectedTask: setSelectedTaskMock,
      selectedTimepoint: null,
      selectedCondition: null,
    });
  });

  afterEach(() => {
    cleanup();
    jest.clearAllMocks();
  });

  test("renders tasks and highlights the selected one", () => {
    render(<TaskPicker />);

    // Title
    expect(screen.getByText(/Walk Task Condition/i)).toBeInTheDocument();

    // Tasks should appear as buttons
    const button1 = screen.getByText("Walk_10m");
    const button2 = screen.getByText("Walk_20m");
    expect(button1).toBeInTheDocument();
    expect(button2).toBeInTheDocument();

    // "Walk_10m" is selected -> has 'active' class
    expect(button1.className).toMatch(/active/);
    expect(button2.className).not.toMatch(/active/);
  });

  test("renders empty state when csvData is empty", () => {
    useData.mockReturnValue({
      calibrationData: [{}],
      csvData: [],
      selectedTask: null,
      setSelectedTask: setSelectedTaskMock,
      selectedTimepoint: null,
      selectedCondition: null,
    });

    render(<TaskPicker />);

    expect(screen.getByText(/No tasks available/i)).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  test("filters tasks correctly based on selected timepoint and condition", () => {
    useData.mockReturnValue({
      calibrationData: [{}],
      csvData: [
        { "Task condition": "Walk_10m", Timepoint: "T1", Condition: "Pre" },
        { "Task condition": "Walk_20m", Timepoint: "T2", Condition: "Post" },
      ],
      selectedTask: "Walk_10m",
      setSelectedTask: setSelectedTaskMock,
      selectedTimepoint: "T2",
      selectedCondition: "Post",
    });

    render(<TaskPicker />);

    // Only "Walk_20m" fits both filters
    expect(screen.getByText("Walk_20m")).toBeInTheDocument();
    expect(screen.queryByText("Walk_10m")).not.toBeInTheDocument();
  });

  test("auto-selects the first available task if none selected", () => {
    useData.mockReturnValue({
      calibrationData: [{}],
      csvData: [
        { "Task condition": "Walk_10m", Timepoint: "T1", Condition: "Pre" },
        { "Task condition": "Walk_20m", Timepoint: "T1", Condition: "Pre" },
      ],
      selectedTask: null,
      setSelectedTask: setSelectedTaskMock,
      selectedTimepoint: null,
      selectedCondition: null,
    });

    render(<TaskPicker />);

    // Automatically selects the first unique task
    expect(setSelectedTaskMock).toHaveBeenCalledWith("Walk_10m");
  });

  test("clicking a task calls setSelectedTask with that task", () => {
    render(<TaskPicker />);

    fireEvent.click(screen.getByText("Walk_20m"));
    expect(setSelectedTaskMock).toHaveBeenCalledWith("Walk_20m");

    fireEvent.click(screen.getByText("Walk_10m"));
    expect(setSelectedTaskMock).toHaveBeenCalledWith("Walk_10m");
  });

  test("clears tasks and resets selection when calibrationData is null", () => {
    useData.mockReturnValue({
      calibrationData: null,
      csvData: [
        { "Task condition": "Walk_10m", Timepoint: "T1", Condition: "Pre" },
      ],
      selectedTask: "Walk_10m",
      setSelectedTask: setSelectedTaskMock,
      selectedTimepoint: null,
      selectedCondition: null,
    });

    render(<TaskPicker />);

    expect(setSelectedTaskMock).toHaveBeenCalledWith(null);
    expect(screen.getByText(/No tasks available/i)).toBeInTheDocument();
  });
});
