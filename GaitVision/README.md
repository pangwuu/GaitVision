# How to Run the GaitVision Web Application

This guide will help you get the GaitVision web application running on your local computer. This is a two-part application, meaning it has a **backend** (the server) and a **frontend** (the user interface). Both must be running at the same time.

Please follow these instructions carefully.

## Prerequisites: Install Required Software

Before you begin, you need to install Python and Node.js.

### 1. Install Python

Python is required for the backend server. If you think python may be already installed, skip ahead to step 3 and try to verify the installation.

> The docs here use `python` for Python related commands. On MacOS/Linux devices you'd typically use `python3` instead of `python` for all python related commands

1.  **Download Python:**
    *   Go to the official Python website: [https://www.python.org/downloads/](https://www.python.org/downloads/)
    *   Download the latest stable version of Python 3 (e.g., Python 3.10.x or newer).

2.  **Install Python:**
    *   **Windows:** Run the downloaded `.exe` file. **IMPORTANT:** Check the box that says "Add Python to PATH" during installation, and then click "Install Now".
    *   **macOS:** Run the downloaded `.pkg` file and follow the on-screen instructions.

3.  **Verify Installation:**
    *   Open "Terminal" (macOS) or "Command Prompt" (Windows) and type `python --version`. You should see a version number.

### 2. Install Node.js and npm

Node.js and npm are required for the frontend user interface.

1.  **Download Node.js:**
    *   Go to the official Node.js website: [https://nodejs.org/](https://nodejs.org/)
    *   Download the **LTS (Long Term Support)** version – click “Windows Installer (.msi)” or the `.pkg` file (MacOS).

2.  **Install Node.js:**
    *   Run the downloaded installer and follow the on-screen instructions. npm (Node Package Manager) is included with the installation.

3.  **Verify Installation:**
    *   In a new Terminal or Command Prompt window, type `node --version` and press Enter. You should see a version number.

---

## Part 1: Running the Backend (API Server)

This server handles data processing.

1.  **Open a Terminal:**
    *   **Windows:** Search for "Command Prompt" or "PowerShell" in your Start Menu.
    *   **macOS:** Search for "Terminal" in Spotlight (Cmd + Space).

2.  **Navigate to the `flask-server` Folder:**
    *   **This is a crucial step.** All of the following commands must be run from inside the correct project folder.
        ```bash
        cd "/path/to/your/GaitVision-main/GaitVision/flask-server"
        ```

        > **Note for Windows users:** Your path will look different, e.g., `cd "C:\Users\YourUser\Desktop\GaitVision-main\GaitVision\flask-server"`.

> **💡 Pro Tip: How to Copy a File Path**
> 
> *   **On macOS:** Right-click on a file or folder, hold down the `Option` key, and select "Copy [item name] as Pathname".
> *   **On Windows:** Hold down the `Shift` key and right-click on a file or folder, then select "Copy as path".
> 
> You can then paste this path directly into the terminal after typing `cd `.

3.  **Create and Activate a Virtual Environment:**
    *   Create the environment:
        ```bash
        python -m venv venv
        ```
    *   Activate it:

        Now, activate the environment based on your operating system.

        #### On macOS / Linux
        In your terminal, run:
        ```bash
        source venv/bin/activate
        ```

        #### On Windows
        For simplicity, we recommend using **Command Prompt** for the following steps.

        *   **In Command Prompt:**
            ```bash
            .\venv\Scripts\activate
            ```
        *   **In PowerShell:**
            ```bash
            .\venv\Scripts\Activate.ps1
            ```
            > **Note:** If you get an error using PowerShell, you may need to run it as an Administrator and execute the command `Set-ExecutionPolicy RemoteSigned`. Using Command Prompt is often easier.
    *   You should see `(venv)` at the beginning of your prompt.

4.  **Install Dependencies:**
    *   With the virtual environment activated, run:
        ```bash
        pip install -r requirements.txt
        ```

5.  **Start the Backend Server:**
    *   Run the following command:
        ```bash
        python server.py
        ```

6.  **Leave it Running:**
    *   The backend server is now running. You will see some output in the terminal. **You must leave this terminal window open.**

---

## Part 2: Running the Frontend (User Interface)

This is the visual part of the application that you will interact with.

1.  **Open a NEW Terminal:**
    *   This is very important. You need a **second** terminal window. Do not close the first one.

2.  **Navigate to the `client` Folder:**
    *   In your new terminal, use the `cd` command to go to the **`client`** folder (located inside the `GaitVision` folder).
        ```bash
        cd "/path/to/your/GaitVision-main/GaitVision/client"
        ```

        > **Note for Windows users:** Your path will look different, e.g., `cd "C:\Users\YourUser\Desktop\GaitVision-main\GaitVision\client"`.

3.  **Install Dependencies:**
    *   Run the following command. This might take a few minutes.
        ```bash
        npm install
        ```
        > **Note:** Don't worry if you see many `WARN` messages during the installation. This is normal for `npm`, and the command should still succeed.

4.  **Start the Frontend:**
    *   After the installation is complete, run:
        ```bash
        npm start
        ```

---

## Part 3: Access the Application

*   After running `npm start`, your default web browser should automatically open a new tab to `http://localhost:3000`.
*   If it doesn't, you can manually open your browser and go to that address.
*   You should now see the GaitVision application!

## When You're Done

To stop the application, you need to close both the frontend and backend servers.

1.  Go to each of your two terminal windows.
2.  Press `Ctrl + C` in each window.
3.  You can then safely close the terminals.

---

## Having Trouble?

*   **`command not found` (e.g., `python`, `npm`):** This usually means the program was not added to your system's PATH.
    *   **For Python:** When installing, make sure to check the box that says "Add Python to PATH".
    *   **For Node.js/npm:** The installer should do this automatically. If not, re-installing the LTS version is the easiest fix.

*   **`pip install` or `npm install` fails:**
    *   This can be a network issue. Make sure you are connected to the internet.
    *   If `pip install` fails on Windows with an error mentioning "C++" or "Microsoft Visual C++", you may need to install Microsoft's C++ Build Tools. This is an advanced step, but you can find the tools by searching for "Visual Studio Build Tools".

*   **Server doesn't start or crashes:**
    *   Look for an **"Address already in use"** error in the terminal. This means another application is using the required port (e.g., 3000 or 5000). You will need to close that other application or restart your computer.
    *   For any other errors, try to read the message in the terminal carefully. It will often give you a clue as to what went wrong.

---
[Back to root README](../README.md)
