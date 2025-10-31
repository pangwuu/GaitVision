# COMP3888 Project: Data Analysis and Visualization Tools

This project contains three primary applications developed for data analysis and visualization: a standalone PCA Analysis Tool, a simple PCA web app, and the full-stack GaitVision Web Application.

Each application is contained within its own directory and includes a detailed `README.md` file with specific setup instructions.

---

## Applications Overview

### 1. PCA Analysis Tool (`/PCA`)

This is a standalone desktop application for performing Principal Component Analysis (PCA) on CSV datasets. It is intended for users who need to run a quick, in-depth statistical analysis locally.

*   **Purpose:** To provide a powerful, GUI-driven tool for comprehensive PCA.
*   **Features:** Automated data preprocessing, PCA execution, and the generation of detailed PDF reports including plots, loading matrices, and variable rankings.
*   **How to Run:** For detailed instructions, please see the [`PCA/README.md`](./PCA/README.md) file.

### 2. PCA Small Web App (`/PCA Small Web App`)

This is a lightweight, local web application that performs a simplified PCA on an uploaded CSV file and displays the results in the browser.

*   **Purpose:** To offer a simple, web-based interface for quick PCA tasks without the need for a complex setup.
*   **Features:** A straightforward web page to upload a file, which then runs the analysis and presents the key results.
*   **How to Run:** For detailed instructions, please see the [`PCA Small Web App/README.md`](./PCA%20Small%20Web%20App/README.md) file.

### 3. GaitVision Web Application (`/GaitVision`)

GaitVision is a comprehensive, full-stack web application that provides a rich, interactive interface for analyzing and visualizing gait analysis data. It is designed to help clinicians and researchers compare a patient's metrics against a normalized baseline population.

*   **Purpose:** To provide an advanced, interactive tool for clinical gait analysis.
*   **Features:**
    *   A **backend API** (`/GaitVision/flask-server`) for data processing, normalization, and PCA-based variable suggestions.
    *   An **interactive frontend** (`/GaitVision/client`) for uploading calibration and patient data.
    *   Dynamic **radar chart visualizations** that use Z-scores to show patient deviation from a population average.
    *   The ability to filter by variables, walk tasks, and timepoints.
    *   Downloadable PDF summaries of the analysis.
*   **How to Run:** This is a two-part application requiring both a backend and frontend server. Detailed setup instructions can be found in the [`GaitVision/README.md`](./GaitVision/README.md) file.