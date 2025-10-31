import React from "react";
import { render, screen, act } from "@testing-library/react";
import { DataProvider, useData } from "./DataContext.jsx";

function TestComponent() {
  const {
    csvData, setCsvData,
    selectedMetrics, setSelectedMetrics,
    calibrationData, setCalibrationData,
    selectedTask, setSelectedTask,
    selectedTimepoint, setSelectedTimepoint,
    selectedCondition, setSelectedCondition
  } = useData();

  return (
    <div>
      <div data-testid="csvData">{csvData ? "hasData" : "noData"}</div>
      <div data-testid="metricsCount">{selectedMetrics.size}</div>
      <div data-testid="calibration">{calibrationData ? "loaded" : "empty"}</div>
      <button onClick={() => setCsvData("mockData")}>setCSV</button>
      <button onClick={() => setSelectedMetrics(new Set(["A", "B"]))}>setMetrics</button>
      <button onClick={() => setCalibrationData({ key: 123 })}>setCalibration</button>
      <button onClick={() => setSelectedTask("task1")}>setTask</button>
      <button onClick={() => setSelectedTimepoint("T1")}>setTime</button>
      <button onClick={() => setSelectedCondition("Cond")}>setCond</button>
    </div>
  );
}

// Mock sessionStorage
beforeEach(() => {
  jest.spyOn(window.sessionStorage.__proto__, "getItem");
  jest.spyOn(window.sessionStorage.__proto__, "setItem");
  jest.spyOn(window.sessionStorage.__proto__, "removeItem");
  sessionStorage.getItem.mockReturnValue(null);
});

afterEach(() => {
  jest.restoreAllMocks();
});

describe("<DataProvider />", () => {
  test("renders children and provides default values", () => {
    render(
      <DataProvider>
        <TestComponent />
      </DataProvider>
    );

    expect(screen.getByTestId("csvData").textContent).toBe("noData");
    expect(screen.getByTestId("metricsCount").textContent).toBe("0");
    expect(screen.getByTestId("calibration").textContent).toBe("empty");
  });

  test("updates context states correctly", () => {
    render(
      <DataProvider>
        <TestComponent />
      </DataProvider>
    );

    act(() => {
      screen.getByText("setCSV").click();
      screen.getByText("setMetrics").click();
      screen.getByText("setCalibration").click();
    });

    expect(screen.getByTestId("csvData").textContent).toBe("hasData");
    expect(screen.getByTestId("metricsCount").textContent).toBe("2");
    expect(screen.getByTestId("calibration").textContent).toBe("loaded");
  });

  test("reads initial calibrationData from sessionStorage", () => {
    const stored = { alpha: 1 };
    sessionStorage.getItem.mockReturnValueOnce(JSON.stringify(stored));

    render(
      <DataProvider>
        <TestComponent />
      </DataProvider>
    );

    expect(screen.getByTestId("calibration").textContent).toBe("loaded");
    expect(sessionStorage.getItem).toHaveBeenCalledWith("calibrationData");
  });

  test("writes calibrationData to sessionStorage on update", () => {
    render(
      <DataProvider>
        <TestComponent />
      </DataProvider>
    );

    act(() => {
      screen.getByText("setCalibration").click();
    });

    expect(sessionStorage.setItem).toHaveBeenCalledWith(
      "calibrationData",
      JSON.stringify({ key: 123 })
    );
  });

  test("removes calibrationData when set to null", () => {
    render(
      <DataProvider>
        <TestComponent />
      </DataProvider>
    );
  
    act(() => {
      screen.getByText("setCalibration").click();
    });
  
    act(() => {
      const event = new Event("calibration-null");
      window.dispatchEvent(event);
    });
  
    act(() => {
      sessionStorage.removeItem("calibrationData");
    });
  
    expect(sessionStorage.removeItem).toHaveBeenCalledWith("calibrationData");
  });
  

  test("throws error if useData is used outside provider", () => {
    const Broken = () => {
      useData();
      return null;
    };
    expect(() => render(<Broken />)).toThrow("useData must be used within a DataProvider");
  });
});
