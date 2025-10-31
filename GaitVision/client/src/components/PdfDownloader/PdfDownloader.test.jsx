// src/components/PdfDownloader/PdfDownloader.test.jsx
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

// Prevent style-related noise in tests
jest.mock("./tableStyle", () => ({ tableStyles: {} }));
jest.mock("html2canvas", () => ({
  __esModule: true,
  default: jest.fn(),
}));
jest.mock("jspdf", () => ({
  __esModule: true,
  default: jest.fn(),
}));
jest.mock("jspdf-autotable", () => ({
  __esModule: true,
  default: jest.fn(),
}));

import PdfDownloader, { calculateZScore } from "./PdfDownloader";
import jsPDF from "jspdf";
import html2canvas from "html2canvas";
import autoTable from "jspdf-autotable";
import { useData } from "../DataContext/DataContext";

// mock DataContext
jest.mock("../DataContext/DataContext", () => ({
  useData: jest.fn(),
}));

describe("<PdfDownloader />", () => {
  const fakeCanvas = {
    width: 800,
    height: 400,
    toDataURL: jest.fn(() => "data:image/png;base64,FAKE"),
  };

  const pdfInstance = {
    internal: {
      pageSize: {
        getWidth: () => 595,
        getHeight: () => 842,
      },
    },
    setFont: jest.fn(),
    setFontSize: jest.fn(),
    text: jest.fn(),
    addImage: jest.fn(),
    save: jest.fn(),
    addPage: jest.fn(),
    line: jest.fn(),
    setDrawColor: jest.fn(),
    setLineWidth: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();

    html2canvas.mockResolvedValue(fakeCanvas);
    jsPDF.mockImplementation(() => pdfInstance);
    useData.mockReturnValue({
      calibrationData: [{ name: "speed", mean: 5, stdev: 1, condition: "ST", timepoint: "Baseline" }],
      csvData: [
        { metric: "speed", units: "m/s", Baseline: 6, "participant id": "P001", "Task condition": "ST" },
      ],
      selectedMetrics: new Set(["speed"]),
      selectedPlot: ["Baseline"],
      selectedTask: "ST",
    });
  });

  // PDF Download Button Testing

    // Normal Testcase – verifies expected UI behavior under typical conditions.
  test("renders the download button", () => {
    render(<PdfDownloader targetRef="report-root" data={[]} />);
    expect(screen.getByRole("button", { name: /download report/i })).toBeInTheDocument();
  });

    // Abnormal Testcase – handles missing input/data scenario.
  test("shows message if data is missing", async () => {
    render(<PdfDownloader targetRef="plot" data={[]} />);
    fireEvent.click(screen.getByRole("button", { name: /download report/i }));
    await waitFor(() => {
      expect(screen.getByText(/Please generate plot first!/i)).toBeInTheDocument();
    });
    expect(jsPDF).not.toHaveBeenCalled();
  });

    // Abnormal Testcase – handles missing DOM element scenario.
  test("logs error and aborts when target element is not found", async () => {
    const errSpy = jest.spyOn(console, "error").mockImplementation(() => {});
    render(<PdfDownloader targetRef="missing-class" data={[{ metric: "speed" }]} />);
    fireEvent.click(screen.getByRole("button", { name: /download report/i }));
    await waitFor(() => {
      expect(screen.getByText(/Please generate plot first!/i)).toBeInTheDocument();
    });
    expect(jsPDF).not.toHaveBeenCalled();
    errSpy.mockRestore();
  });

    // Normal Testcase – typical usage scenario where everything works correctly.
  test("happy path: generates and saves PDF", async () => {
    const targetClass = "report-root";
    const { container } = render(
      <div>
        <div className={targetClass}>chart mock</div>
        <PdfDownloader targetRef={targetClass} data={[{ value: 1 }]} />
      </div>
    );

    fireEvent.click(screen.getByRole("button", { name: /download report/i }));
    await waitFor(() => expect(pdfInstance.save).toHaveBeenCalledTimes(1));

    expect(html2canvas).toHaveBeenCalledWith(
      container.querySelector(`.${targetClass}`),
      { scale: 2 }
    );

    expect(jsPDF).toHaveBeenCalledWith({
      orientation: "portrait",
      unit: "pt",
      format: "a4",
    });

    expect(autoTable).toHaveBeenCalledTimes(1);
    expect(pdfInstance.addImage).toHaveBeenCalled();
    expect(pdfInstance.save).toHaveBeenCalled();
  });


// Z-score Calculation Testing
const calibrationData = [
  {
    name: "Average Speed",
    mean: 0.6,
    stdev: 0.3,
    timepoint: "Baseline",
    condition: "ST"
  },
  {
    name: "Average Athlete Load Asymmetry",
    mean: 0.5288,
    stdev: 0.2729,
    timepoint: "Baseline",
    condition: "ST"
  }
];

const csvData = [
  {
    metric: "Average Speed",
    units: "m/s",
    "Task condition": "ST",
    "participant id": 1,
    Baseline: 0.7,
    "PI-1": 0.9
  },
  {
    metric: "Average Athlete Load Asymmetry",
    units: "%",
    "Task condition": "ST",
    "participant id": 1,
    Baseline: 0.8,
    "PI-1": 0.85
  }
];

describe("Z-score Calculation with Baseline", () => {

    // Normal Testcase – typical calculation with valid inputs.
  test("returns correct Z-score for Average Speed", () => {
    const z = calculateZScore("Average Speed", 0.9, calibrationData, "ST");
    // (0.9 - 0.6) / 0.3 = 1.0
    expect(z).toBe("1.00");
  });

    // Normal Testcase – typical calculation with valid inputs.
  test("returns correct Z-score for Average Athlete Load Asymmetry", () => {
    const z = calculateZScore("Average Athlete Load Asymmetry", 0.8, calibrationData, "ST");
    // (0.8 - 0.5288)/0.2729 ≈ 0.99
    expect(z).toBe("0.99");
  });
    // Boundary/Abnormal Testcase – tests behavior when required data is null.
  test("returns null if calibrationData is null", () => {
    const z = calculateZScore("Average Speed", 0.7, null, null);
    expect(z).toBeNull();
  });

    // Boundary/Abnormal Testcase – tests behavior for invalid metric input.
  test("returns null if metric not in calibrationData", () => {
    const z = calculateZScore("Nonexistent Metric", 0.5, calibrationData, null);
    expect(z).toBeNull();
  });

    // Boundary Testcase – tests behavior when optional parameter is missing.
  test("ignores selectedTask if null", () => {
    const z = calculateZScore("Average Speed", 0.7, calibrationData, null);
    // (0.7 - 0.6)/0.3 = 0.33
    expect(z).toBe("0.33");
  });
    
    // Normal Testcase – ensures population average calculation matches expected.
  test("calculates population average for table rows", () => {
    const row = csvData[0];
    const metricName = row.metric;
    const popAvg =
      calibrationData.find((d) => d.name === metricName)?.mean.toFixed(2) ?? "N/A";
    expect(popAvg).toBe("0.60"); // matches Baseline mean
  });
});

describe("Population Average consistency with Z-score", () => {
  const calibrationData = [
    { name: "Average Speed", mean: 0.6, stdev: 0.3, timepoint: "Baseline", condition: "ST" },
    { name: "Average Athlete Load Asymmetry", mean: 0.5288, stdev: 0.2729, timepoint: "Baseline", condition: "ST" }
  ];

  const csvData = [
    { metric: "Average Speed", units: "m/s", "Task condition": "ST", "participant id": 1, Baseline: 0.7 },
    { metric: "Average Athlete Load Asymmetry", units: "%", "Task condition": "ST", "participant id": 1, Baseline: 0.8 }
  ];

  // Normal Testcase – verifies population average and Z-score consistency under standard inputs.
  test("Population Avg matches baseline mean used in Z-score calculation", () => {
    csvData.forEach(row => {
      const metricName = row.metric;
      const baselineValue = row.Baseline;

      // Population average calculation
      const popAvg =
        calibrationData.find(
          (d) =>
            d.name === metricName &&
            d.condition === row["Task condition"] &&
            d.timepoint === "Baseline"
        )?.mean.toFixed(2) ?? "N/A";

      // Z-score calculation
      const z = calculateZScore(metricName, baselineValue, calibrationData, row["Task condition"]);

      // Expected Z-score: (Baseline - PopAvg)/stdev
      const expectedZ = ((baselineValue - parseFloat(popAvg)) / calibrationData.find(
        (d) =>
          d.name === metricName &&
          d.condition === row["Task condition"] &&
          d.timepoint === "Baseline"
      ).stdev).toFixed(2);

      expect(popAvg).not.toBe("N/A");
      expect(z).toBe(expectedZ);
    });
  });
});


  
});
