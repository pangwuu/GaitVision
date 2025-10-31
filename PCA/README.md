# How to Run the PCA Analysis Tool

This guide will help you get the PCA Analysis Tool up and running on your computer, even if you have no programming experience. Please follow these steps carefully.

## Step 1: Install Python

Python is the programming language this application is built with. You need to install it first.

1.  **Download Python:**
    *   Go to the official Python website: [https://www.python.org/downloads/](https://www.python.org/downloads/)
    *   Download the latest stable version of Python 3 (e.g., Python 3.10.x or newer).

2.  **Install Python:**
    *   **Windows:** Run the downloaded `.exe` file. **IMPORTANT:** Check the box that says "Add Python to PATH" during installation, and then click "Install Now".
    *   **macOS:** Run the downloaded `.pkg` file and follow the on-screen instructions.

3.  **Verify Installation:**
    *   Open your computer's "Terminal" (on macOS) or "Command Prompt" (on Windows).
    *   Type `python --version` and press Enter. You should see a version number like `Python 3.10.12`.

## Step 2: Open the Terminal and Navigate to the Project Folder

1.  **Open Terminal/Command Prompt:**
    *   **Windows:** Search for "Command Prompt" or "PowerShell" in your Start Menu.
    *   **macOS:** Search for "Terminal" in Spotlight (Cmd + Space).

2.  **Navigate to the `PCA` Folder:**
    *   Use the `cd` command to go to the `PCA` folder.
    *   Type `cd ` (with a space), then drag and drop the "PCA" folder into the Terminal window. This will paste the correct path. Press Enter.
    *   It should look something like this (your path will be different):
        ```bash
        cd "/path/to/your/COMP3888 public/PCA"
        ```

## Step 3: Create and Activate a Virtual Environment

This creates a self-contained environment for the application's dependencies.

1.  **Create the Virtual Environment:**
    *   In the Terminal, make sure you are in the "PCA" folder.
    *   Type the following command and press Enter:
        ```bash
        python -m venv venv
        ```

2.  **Activate the Virtual Environment:**
    *   **Windows:**
        ```bash
        .\venv\Scripts\activate
        ```
    *   **macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```
    *   You'll know it's activated when you see `(venv)` at the beginning of your Terminal prompt.

## Step 4: Install Project Dependencies

Now, install the specific libraries the application needs.

1.  **Install Dependencies:**
    *   With the virtual environment activated, type the following command and press Enter:
        ```bash
        pip install -r requirements.txt
        ```
    *   This may take a few moments.

## Step 5: Run the Application

1.  **Start the Application:**
    *   In the same Terminal window, type:
        ```bash
        python pca_pipeline.py
        ```
    *   Press Enter.

## Step 6: Use the Application

1.  **Select a File:**
    *   A file selection window will pop up. Use this to navigate to and select the CSV file you want to analyze.

2.  **Analysis and Report:**
    *   The application will run the analysis. This may take a few moments.
    *   Once complete, a PDF report with the analysis results will be automatically generated and opened for you to view.
    *   All results, including logs and plots, are saved in a folder named `PCA_Analysis` inside your computer's "Documents" folder.

## When You're Done

The application will close automatically after the report is generated. You can then close the Terminal window. To use it again, just follow Step 5 and Step 6.

---
[Back to root README](../README.md)