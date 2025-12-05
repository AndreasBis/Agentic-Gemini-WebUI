# Agentic Gemini Web UI

Agentic Gemini is an exploratory repository demonstrating multi-agent workflows using the `AG2` (autogen) framework and Google's Gemini models (via AI Studio).

This project wraps the powerful agentic backend in a modern **Flask-based Web UI**, enabling you to interact with various agent patterns—from simple code execution to complex human-in-the-loop workflows—directly from your browser. It features persistent chat history, syntax highlighting, and a responsive design.

## Table of Contents

- [Agentic Gemini Web UI](#agentic-gemini-web-ui)
- [Table of Contents](#table-of-contents)
- [Features](#features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Configuration](#configuration)
  - [Running the Application (Docker)](#running-the-application-docker)
  - [Local Development Setup (Optional)](#local-development-setup-optional)
- [Maintenance](#maintenance)
- [Acknowledgement](#acknowledgement)

## Features

-   **5 Distinct Agent Modes:**
    1.  **Basic Code Agent:** Simple User $\to$ Assistant flow.
    2.  **Coder vs. Reviewer:** Iterative code improvement.
    3.  **Orchestrated Group Chat:** Manager, Planner, and Reviewer working together.
    4.  **Human-in-the-Loop:** Expert and Planner with real-time human validation.
    5.  **Tool Use Chat:** Advanced filesystem operations (Find, Read, Edit, Run files) within a sandboxed environment.
-   **Modern Web Interface:**
    -   Champagne & Cognac aesthetic.
    -   Real-time streaming responses via WebSockets.
    -   Markdown rendering and Syntax Highlighting for code.
-   **Persistent History:**
    -   SQLite-backed chat history.
    -   Sidebar navigation with Rename, Delete, and Download capabilities.
-   **Secure Execution:**
    -   Dockerized environment ensures host system safety.
    -   Strict file access controls in Tool Mode.

## Getting Started

Follow these instructions to get the project up and running on your local machine.

### Prerequisites

You will need the following tools installed on your system:
-   Git
-   Docker Engine
-   (Optional) Python 3.12+ for local development

### Configuration

The application requires a Google Gemini API key. You must create two configuration files in the root directory:

1.  **`config.json`**:
    Create this file using `sample_config.json` as a template.

    ```json
    [
      {
        "model": "gemini-2.5-flash-lite",
        "api_key": "your-AI-Studio-API-key-goes-here",
        "api_type": "google"
      }
    ]
    ```

2.  **`config_path.json`**:
    Create this file using `sample_config_path.json` as a template.

    ```json
    {
      "config_path": "config.json"
    }
    ```

### Running the Application (Docker)

This is the **recommended** way to run the application. It ensures the environment is isolated and the file permissions are handled correctly.

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/Agentic-Gemini.git](https://github.com/your-username/Agentic-Gemini.git)
    cd Agentic-Gemini
    ```

2.  **Build the Docker image:**
    ```bash
    docker build -t agentic-gemini .
    ```

3.  **Run the application:**
    Run the following command.
    * `-p 5000:5000`: Exposes the Web UI port.
    * `-v ...docker.sock`: **Required** for the agent to spawn execution containers.
    * `-v ...:/my_files`: **Required for Mode 5**. Mounts your local working directory.

    ```bash
    docker run -it --rm -p 5000:5000 -v /var/run/docker.sock:/var/run/docker.sock -v "/your/local/directory":"/my_files" agentic-gemini
    ```

4.  **Access the UI:**
    Open your browser and navigate to: `http://localhost:5000`

### Local Development Setup (Optional)

If you wish to modify the web application code locally:

1.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    # Linux/macOS:
    source venv/bin/activate
    # Windows:
    .\venv\Scripts\Activate.ps1
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the server:**
    ```bash
    python web_app.py
    ```

## Maintenance

**Cleaning up Docker Resources**
If you need to stop all containers and clean up the environment (useful if the Docker daemon gets cluttered), use these commands:

1.  **Stop all containers:**
    ```bash
    docker stop $(docker ps -a -q)
    ```

2.  **Remove all containers:**
    ```bash
    docker rm $(docker ps -a -q)
    ```

3.  **Complete System Prune (Images & Volumes):**
    ```bash
    docker system prune -a --volumes
    ```

## Acknowledgement

This project is built upon the `AG2` (autogen) framework.

-   [ag2ai/ag2 Repository](https://github.com/ag2ai/ag2)