# AGENT.md

## Project Overview

This project, "betza-visualizer," is a dual implementation of a parser and visualizer for fairy chess piece movements based on their Betza notation. The repository contains two separate, parallel implementations that must be kept in sync:

1.  A Python application that uses the **Textual TUI framework** to provide a visualization within a terminal.
2.  A TypeScript application that uses **HTML, CSS, and SVG** to provide a visualization in a web browser.

## Core Agent Mandate: Maintain Parity

**This is the most important rule.** The parsing logic, the suite of tests, and the visualization rules **must** remain consistent across both the Python and TypeScript versions. Any change to the core logic in one implementation must be replicated in the other.

## Agent Workflow Example: Adding a New Piece

This example demonstrates the required workflow for adding a new feature.

**Goal**: Add support for the "Ferz" piece (Betza notation "F"), which moves one square diagonally.

**Required Steps:**

1.  **Update Python Parser**:
    *   Modify `betza_parser.py` to correctly parse the "F" notation and generate its diagonal move vectors.
2.  **Add Python Test**:
    *   Add a new test case in the `tests/` directory to verify the Ferz's movement logic in Python.
3.  **Update TypeScript Parser**:
    *   Modify the corresponding parser file in `src/` to replicate the exact same parsing logic for "F".
4.  **Add TypeScript Test**:
    *   Add a new test case in the `tests/` directory for TypeScript to verify the Ferz's movement, ensuring the test case matches the Python one.
5.  **Add Web E2E Test**:
    *   If the change affects web app behavior, add a Python Playwright test to `tests/test_web_app.py` to verify the visual and interactive correctness of the change.
6.  **Verify All Implementations**:
    *   Run the full test suite for both Python (TUI) and the Web (Jest and Playwright) to ensure all tests pass.

## Implementation Details

### 1. Python (TUI Version)

This version is a command-line application that renders the visualization directly in the terminal.

*   **Framework:** [Textual](https://textual.textualize.io/)
*   **Core Files:**
    *   `main.py`: The entry point for the Textual TUI application.
    *   `betza_parser.py`: The Python implementation of the Betza notation parser.
    *   `tests/`: Contains the unit tests for the Python implementation.

#### Setup and Execution

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Run Tests:**
    ```bash
    python -m unittest discover -s tests
    ```
3.  **Run the Application:**
    ```bash
    python main.py
    ```
#### Development

This project uses `ruff` for linting and formatting.

*   **To check for linting errors, run:**
    ```bash
    ruff check .
    ```

*   **To automatically fix linting errors, run:**
    ```bash
    ruff check . --fix
    ```

*   **To format the code, run:**
    ```bash
    ruff format .
    ```

### 2. TypeScript (Web Version)

This version is a client-side web application that renders the visualization in a browser.

*   **Core Technologies:** TypeScript, HTML, CSS, SVG
*   **Development Tools:**
    *   **Testing:** Jest
    *   **Package Management:** Yarn
*   **Core Files:**
    *   `src/`: Contains the TypeScript source code for the parser and visualization logic.
    *   `tests/`: Contains the Jest test suite for the TypeScript implementation.
    *   `index.html`: The main HTML file for the web interface.
    *   `package.json`: Defines Node.js dependencies and scripts.
    *   `tsconfig.json`: TypeScript compiler configuration.
    *   `jest.config.js`: Jest testing framework configuration.

#### Setup and Execution

The recommended workflow is to install dependencies, run tests, build the project, and then start the application.

1.  **Install Dependencies:**
    ```bash
    yarn install
    ```

2.  **Run Tests:**
    ```bash
    yarn test
    ```

3.  **Build the Application:**
    ```bash
    yarn build
    ```

4.  **Run the Application:**
    ```bash
    yarn start
    ```

#### Development

For formatting and linting the TypeScript code, we use `prettier` and `eslint`.

- To format the code, run:
  ```bash
  yarn format
  ```

- To lint the code, run:
  ```bash
  yarn lint
  ```

#### End-to-End Testing (Python + Playwright)

In addition to the Jest unit tests, the web application has a suite of end-to-end (E2E) tests written in Python using the Playwright framework. These tests verify the application's behavior in a real browser environment.

1.  **Install Python Dependencies:**
    Ensure you have installed the Python dependencies, including `pytest-playwright`:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Build the Web App:**
    The E2E tests run against the built version of the application. Make sure you have a recent build in the `dist/` directory:
    ```bash
    yarn build
    ```

3.  **Run the Web Server:**
    Before running the tests, you must serve the built application. A simple Python web server can be used:
    ```bash
    python -m http.server 8080 --directory dist &
    ```

4.  **Run E2E Tests:**
    Execute the Playwright tests using `pytest`:
    ```bash
    python -m pytest tests/test_web_app.py
    ```
