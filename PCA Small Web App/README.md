# How to Run the PCA Small Web App Locally

This guide will help you get the PCA Small Web App up and running on your computer, even if you're new to programming. Just follow these steps carefully!

## Step 1: Install Python

Python is the programming language this app is built with. You need to install it first.

1.  **Download Python:**
    *   Go to the official Python website: [https://www.python.org/downloads/](https://www.python.org/downloads/)
    *   Look for the latest stable version of Python 3 (e.g., Python 3.10.x, 3.11.x, or 3.12.x). Click on the "Download" button for your operating system (Windows, macOS, or Linux).

2.  **Install Python:**
    *   **Windows:** Double-click the downloaded `.exe` file. **IMPORTANT:** Make sure to check the box that says "Add Python X.Y to PATH" during installation. Then, click "Install Now".
    *   **macOS:** Double-click the downloaded `.pkg` file and follow the on-screen instructions. Python is often pre-installed on macOS, but it's good to install the latest version.
    *   **Linux:** Python is usually pre-installed. If you need a newer version, you might use your system's package manager (e.g., `sudo apt-get install python3.x` for Ubuntu/Debian or `sudo dnf install python3.x` for Fedora).

3.  **Verify Installation:**
    *   Open your computer's "Terminal" (on macOS/Linux) or "Command Prompt" / "PowerShell" (on Windows).
    *   Type `python --version` and press Enter. You should see something like `Python 3.10.12` (the version number might be different). If you see an error, Python might not be installed correctly or added to your system's PATH.

## Step 2: Open the Terminal and Navigate to the Project Folder

The "Terminal" (or "Command Prompt" / "PowerShell") is where you'll type commands to run the app.

1.  **Open Terminal/Command Prompt:**
    *   **Windows:** Search for "Command Prompt" or "PowerShell" in your Start Menu and open it.
    *   **macOS:** Search for "Terminal" in Spotlight (Cmd + Space) and open it.
    *   **Linux:** Look for "Terminal" in your applications menu.

2.  **Navigate to the Project Folder:**
    *   You need to tell the Terminal where your "PCA Small Web app" folder is.
    *   First, find the exact location of your "PCA Small Web app" folder on your computer. For example, it might be in your "Downloads" folder, "Documents", or "Desktop".
    *   Once you know the path (e.g., `/Users/johnnywu/Desktop/Uni/Sem 2/COMP3888/COMP3888_M15_02_P23/PCA Small Web app`), use the `cd` command to go there.
    *   Type `cd ` (note the space after `cd`), then drag and drop your "PCA Small Web app" folder directly into the Terminal window. This will automatically fill in the path. Press Enter.
    *   It should look something like this (your path will be different):
        ```bash
        cd /Users/johnnywu/Desktop/Uni/Sem 2/COMP3888/COMP3888_M15_02_P23/PCA Small Web app
        ```

## Step 3: Create and Activate a Virtual Environment (Recommended)

A virtual environment keeps the app's dependencies separate from other Python projects on your computer. This is good practice.

1.  **Create the Virtual Environment:**
    *   In the Terminal, make sure you are in the "PCA Small Web app" folder (from Step 2).
    *   Type the following command and press Enter:
        ```bash
        python -m venv venv
        ```
    *   This will create a new folder named `venv` inside your project folder.

2.  **Activate the Virtual Environment:**
    *   **Windows (Command Prompt):**
        ```bash
        .\venv\Scripts\activate
        ```
    *   **Windows (PowerShell):**
        ```bash
        .\venv\Scripts\Activate.ps1
        ```
    *   **macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```
    *   You'll know it's activated because `(venv)` will appear at the beginning of your Terminal prompt.

## Step 4: Install Project Dependencies

Now you need to install all the specific libraries the app needs to run.

1.  **Install Dependencies:**
    *   With the virtual environment activated (you see `(venv)` in your prompt), type the following command and press Enter:
        ```bash
        pip install -r requirements.txt
        ```
    *   This might take a few moments as it downloads and installs several packages.

## Step 5: Run the Web Application

Almost there! Now you can start the app.

1.  **Start the Application:**
    *   In the same Terminal window (with `(venv)` activated), type:
        ```bash
        python app.py
        ```
    *   Press Enter.

2.  **Look for the Link:**
    *   After running the command, you will see some messages in the Terminal. Look for a line that says something like:
        ```
         * Running on http://127.0.0.1:5000
        ```
    *   This is the address where your app is running.

## Step 6: Access the App in Your Web Browser

1.  **Open Your Web Browser:** Open Chrome, Firefox, Edge, Safari, or any web browser you prefer.

2.  **Go to the Address:** In the address bar of your web browser, type or paste the address you saw in the Terminal (e.g., `http://127.0.0.1:5000`) and press Enter.

    *   You should now see the PCA Small Web App running in your browser!

## When You're Done

To stop the application, go back to the Terminal window where it's running and press `Ctrl + C` (hold down the Control key and press C). To exit the virtual environment, simply type `deactivate` and press Enter.