# PCA Analysis Pipeline Documentation

This document provides instructions on how to set up, run, test, and build the PCA Analysis Pipeline application.

## 1. Setup

First, install the required Python packages using pip. It is recommended to do this within a virtual environment.

```bash
# Create and activate a virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt
```

## 2. Running the Application

The application can be run in two modes: with a Graphical User Interface (GUI) for file selection, or in a headless mode for command-line use.

### GUI Mode

To run the application with the GUI, which will prompt you to select a CSV file for analysis:

```bash
python pca_pipeline.py
```

A file dialog will open, allowing you to choose the CSV file you wish to analyze. The results, including plots, logs and a pdf report, will be saved in a `results` directory inside `~/Documents/PCA_Analysis/`.

## 3. Testing the Pipeline

A test suite is provided to verify the functionality of the PCA pipeline using predefined datasets. To run the tests, execute the `pca_test.py` script:

```bash
python pca_test.py
```

The script will run several test cases and print a summary of the results. It will exit with status code 0 if all tests pass and 1 otherwise.

### Further tests
To test the functionality of the entire pipeline, including the output on known csv files, follow these instructions:

1. Create a new directory in the `PCA` directory called `test_data`
2. Add any number of CSV files into your newly created `test_data` directory.
3. Run the `pipeline_test_unix.sh` or `pipeline_test_windows.ps1` files using a command prompt below

```bash
# Assuming your current working directory is "PCA"
bash pipeline_test_unix.sh # Mac/Linux
.\pipeline_test_windows.ps1 # Windows
```

4. All results will be created in `Documents/PCA_Analysis/results`

**IMPORTANT NOTE**: This test script merely runs the pipeline on all files in the `test_data` directory. It does **NOT** check or guarantee the accuracy of the results, you should compare the results to known results of an **already known** dataset.

## 4. Building the Application

You can create a standalone executable from the script using `pyinstaller`. This packages the application and all its dependencies into a single file.

### Build Command

```bash
cd PCA # All platforms

pyinstaller pca_pipeline.py --windowed --name "PCA_Analysis_Tool" # MacOS

pyinstaller pca_pipeline.py --onefile --windowed --name "PCA_Analysis_Tool" # Windows

xvfb-run -a pyinstaller pca_pipeline.py --windowed --name "PCA_Analysis_Tool" # Linux

```

- `--onefile`: Creates a single executable file.
- `--windowed`: Prevents a console window from appearing when the application is run. This is important for a GUI application.
- `--name "PCA_Analysis"`: Sets the name of the output executable.

After running the command, the executable will be located in the `dist` directory. You can distribute this file to users who may not have Python or the required libraries installed.
