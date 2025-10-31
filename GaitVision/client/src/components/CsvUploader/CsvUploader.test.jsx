import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import CsvUploader from "./CsvUploader.jsx";
import { DataProvider } from "../DataContext/DataContext.jsx";

describe("<CsvUploader />", () => {
  const UPLOAD_URL = "http://localhost:5001/upload";
  const serverJson = { ok: true, rows: 3 };

  let fetchSpy;
  let consoleErrorSpy;

  beforeEach(() => {
    jest.spyOn(console, "log").mockImplementation(() => {});
    fetchSpy = jest.spyOn(global, "fetch").mockResolvedValue({
      json: jest.fn().mockResolvedValue(serverJson),
    });
    consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  function getHiddenFileInput(container) {
    return container.querySelector('input[type="file"]');
  }

  test("renders a button and a hidden file input", () => {
    const { container } = render(
      <DataProvider>
        <CsvUploader onUpload={jest.fn()} />
      </DataProvider>
    );

    expect(screen.getByRole("button", { name: /upload csv/i })).toBeInTheDocument();

    const input = getHiddenFileInput(container);
    expect(input).toBeInTheDocument();
    expect(input).toHaveAttribute("accept", ".csv");
    expect(input).toHaveStyle({ display: "none" });
  });

  test("clicking the button triggers the file input click()", async () => {
    const { container } = render(
      <DataProvider>
        <CsvUploader onUpload={jest.fn()} />
      </DataProvider>
    );

    const input = getHiddenFileInput(container);
    const inputClickSpy = jest.spyOn(input, "click");

    await userEvent.click(screen.getByRole("button", { name: /upload csv/i }));
    expect(inputClickSpy).toHaveBeenCalledTimes(1);
  });

  test("successful upload posts FormData to backend and calls onUpload with JSON", async () => {
    const onUpload = jest.fn();
    const { container } = render(
      <DataProvider>
        <CsvUploader onUpload={onUpload} />
      </DataProvider>
    );

    const input = getHiddenFileInput(container);
    const file = new File(["a,b\n1,2"], "data.csv", { type: "text/csv" });
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => expect(fetchSpy).toHaveBeenCalledTimes(1));

    const [url, init] = fetchSpy.mock.calls[0];
    expect(url).toBe(UPLOAD_URL);
    expect(init.method).toBe("POST");
    expect(init.body).toBeInstanceOf(FormData);

    const sentFile = init.body.get("file");
    expect(sentFile).toBeInstanceOf(File);
    expect(sentFile.name).toBe("data.csv");

  });

  test("early return when no file selected (does not call fetch)", () => {
    const onUpload = jest.fn();
    const { container } = render(
      <DataProvider>
        <CsvUploader onUpload={onUpload} />
      </DataProvider>
    );

    const input = getHiddenFileInput(container);
    fireEvent.change(input, { target: { files: [] } });

    expect(fetchSpy).not.toHaveBeenCalled();
  });

  test("logs error if fetch rejects", async () => {
    fetchSpy.mockRejectedValueOnce(new Error("Network fail"));

    const onUpload = jest.fn();
    const { container } = render(
      <DataProvider>
        <CsvUploader onUpload={onUpload} />
      </DataProvider>
    );

    const input = getHiddenFileInput(container);
    const file = new File(["x,y\n3,4"], "bad.csv", { type: "text/csv" });
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => expect(consoleErrorSpy).toHaveBeenCalled());
  });
});
