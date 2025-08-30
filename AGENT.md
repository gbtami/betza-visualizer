Of course. I've updated the `AGENT.md` to include the `yarn build` step and reordered the sequence to reflect the correct workflow.

# AGENT.md

## Project Overview

This project, "betza-visualizer," is a dual implementation of a parser and visualizer for fairy chess piece movements based on their Betza notation. The repository contains two separate, parallel implementations that must be kept in sync:

1.  A Python application that uses the **Textual TUI framework** to provide a visualization within a terminal.
2.  A TypeScript application that uses **HTML, CSS, and SVG** to provide a visualization in a web browser.

A core requirement of this project is that the parsing logic, the suite of tests, and the visualization rules remain consistent across both the Python and TypeScript versions.

## Implementations

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
## Development

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
