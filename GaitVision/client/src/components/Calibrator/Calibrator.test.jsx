// src/components/Calibrator/Calibrator.test.jsx
import React from "react";
import { render, screen, fireEvent, waitFor, cleanup } from "@testing-library/react";
import Calibrator from "./Calibrator.jsx";

// Mock DataContext.useData to avoid wiring a real provider in tests
jest.mock("../DataContext/DataContext.jsx", () => {
  const actual = jest.requireActual("../DataContext/DataContext.jsx");
  return {
    ...actual,
    useData: jest.fn(),
  };
});
import { useData } from "../DataContext/DataContext.jsx";

// Mock global fetch once for the whole file
global.fetch = jest.fn();

describe("<Calibrator />", () => {
  let setCalibrationDataMock;

  beforeEach(() => {
    // Fresh mock for each test
    setCalibrationDataMock = jest.fn();
    useData.mockReturnValue({
      setCalibrationData: setCalibrationDataMock,
    });
  
    // Silence console noise from component debug logs/warns
    jest.spyOn(console, "log").mockImplementation(() => {});
    jest.spyOn(console, "warn").mockImplementation(() => {});
    jest.spyOn(console, "error").mockImplementation(() => {});
  
    fetch.mockReset();
  });

  afterEach(() => {
    cleanup();
    jest.restoreAllMocks();
  });

  test("renders a 'Normalise' button", () => {
    render(<Calibrator />);
    expect(screen.getByRole("button", { name: /Normalise/i })).toBeInTheDocument();
  });

  test("uploads a file and handles a successful response", async () => {
    // Arrange: successful backend response with valid 'variables' array
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        variables: [
          { name: "Stride Length", timepoint: "T1", condition: "A", mean: 1.23, stdev: 0.12 },
          { name: "Cadence", timepoint: "T1", condition: "A", mean: 0.98, stdev: 0.08 },
        ],
      }),
    });

    const { container } = render(<Calibrator />);

    // Prepare a fake CSV file and trigger the input change
    const file = new File(["metric,data"], "mock.csv", { type: "text/csv" });
    const input = container.querySelector('input[type="file"]');
    expect(input).toBeTruthy();

    fireEvent.change(input, { target: { files: [file] } });

    // Assert: fetch called once with FormData
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));

    // Assert: calibration data stored via context setter
    await waitFor(() => expect(setCalibrationDataMock).toHaveBeenCalledWith(expect.any(Array)));

    // Assert: success message is shown
    await waitFor(() =>
      expect(screen.getByText(/Normalisation successful!/i)).toBeInTheDocument()
    );
  });

  test("shows an error message when JSON format is invalid", async () => {
    // Arrange: backend returns an object without 'variables'
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ wrongKey: [] }),
    });

    const { container } = render(<Calibrator />);

    const file = new File(["metric,data"], "mock.csv", { type: "text/csv" });
    const input = container.querySelector('input[type="file"]');
    fireEvent.change(input, { target: { files: [file] } });

    // Assert: error message for invalid format
    await waitFor(() =>
      expect(
        screen.getByText(/Invalid data format received from API\./i)
      ).toBeInTheDocument()
    );

    // Assert: no calibration data set
    expect(setCalibrationDataMock).not.toHaveBeenCalled();
  });

  test("shows an error message when the upload fails (network error)", async () => {
    // Arrange: fetch rejects
    fetch.mockRejectedValueOnce(new Error("Network error"));

    const { container } = render(<Calibrator />);

    const file = new File(["metric,data"], "mock.csv", { type: "text/csv" });
    const input = container.querySelector('input[type="file"]');
    fireEvent.change(input, { target: { files: [file] } });

    // Assert: upload failure message
    await waitFor(() =>
      expect(screen.getByText(/Upload failed\./i)).toBeInTheDocument()
    );

    // Assert: no calibration data set on failure
    expect(setCalibrationDataMock).not.toHaveBeenCalled();
  });

  test("shows an error message when server responds with non-OK status", async () => {
    // Arrange: backend returns non-OK status (e.g., 500)
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({ message: "Server error" }),
    });

    const { container } = render(<Calibrator />);

    const file = new File(["metric,data"], "mock.csv", { type: "text/csv" });
    const input = container.querySelector('input[type="file"]');
    fireEvent.change(input, { target: { files: [file] } });

    // Assert: upload failure message due to non-OK response
    await waitFor(() =>
        expect(screen.getByText(/Invalid data format received from API\./i)).toBeInTheDocument()
    );

    // Assert: no calibration data set
    expect(setCalibrationDataMock).not.toHaveBeenCalled();
  });
});
