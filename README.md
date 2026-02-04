# InvestCLI - Financial Data Terminal

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-supported-blue?logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Typer](https://img.shields.io/badge/CLI-Typer-white?logo=typer)](https://typer.tiangolo.com/)

**InvestCLI** is a powerful Python-based Command Line Interface (CLI) tool designed to provide real-time financial data directly in your terminal. It leverages the `Typer` library for CLI management and `Rich` for beautiful, formatted output.

With InvestCLI, you can track stock prices, visualize charts, monitor cryptocurrency trends, check forex rates, read global financial news, and manage your own personal watchlist.

---

## Table of Contents

*   [Contributors](#contributors)
*   [Features](#features)
*   [Prerequisites & Setup](#prerequisites--setup)
*   [How to Run (Local Environment)](#how-to-run-local-environment)
    *   [1. Create & Activate Virtual Environment](#1-create--activate-virtual-environment-recommended)
    *   [2. Install Dependencies](#2-install-dependencies)
    *   [3. Run the Application](#3-run-the-application)
*   [How to Run (Docker Environment)](#how-to-run-docker-environment)
*   [Command Reference](#command-reference)
*   [Project Structure](#project-structure)
*   [Troubleshooting & API Limits](#troubleshooting--api-limits)

---

## Contributors

#### **Course:** CN330 Computer Application Development
#### **Institution:** Department of Computer Engineering, Faculty of Engineering, Thammasat University.

### Development Team
| Name | Student ID |
| :--- | :--- |
| **Chonchanan Jitrawang** | 6610685056 |
| **Kittidet Wichaidit** | 6610685098 |
| **Nonthapat Boonprasith** | 6610685205 |
| **Supakjira Songsawang** | 6610625052 |

---

## Features

*   **Market Overview:** View real-time prices of the **Top 20 Global Companies** by Market Cap (e.g., Apple, Nvidia, Microsoft).
*   **Stocks:** Real-time price data, fundamental overview (PE, Sector), and 30-day ASCII history charts.
*   **₿ Crypto:** Live cryptocurrency prices, market caps, and "Trending Top-15" coins from CoinGecko.
*   **Forex:** Real-time currency exchange rates with daily percentage changes.
*   **News & Search:** Top headlines by category and keyword search with direct **X (Twitter)** search integration.
*   **Watchlist:** Save your favorite assets locally (`watchlist.json`) to track them easily.

---

## Prerequisites & Setup

Before running the application (Local or Docker), you must configure your API keys.

1.  **Get Free API Keys:**
    *   [Alpha Vantage](https://www.alphavantage.co/support/#api-key) (For Stocks & Forex)
    *   [NewsAPI](https://newsapi.org/register) (For News)

2.  **Create a `.env` file:**
    Create a file named `.env` in the root directory and paste your keys:

    ```env
    ALPHA_VANTAGE_KEY=your_alpha_vantage_key_here
    NEWS_API_KEY=your_news_api_key_here
    ```

---

## How to Run (Local Environment)

Use this method for development. It is recommended to use a virtual environment.

### 1. Create & Activate Virtual Environment (Recommended)

**For Windows:**
```powershell
# Create venv
python -m venv venv

# Activate venv
.\venv\Scripts\activate
```

**For macOS / Linux:**
```bash
# Create venv
python3 -m venv venv

# Activate venv
source venv/bin/activate
```

### 2. Install Dependencies
Once the virtual environment is activated, install the required libraries:

```bash
pip install -r requirements.txt
```

### 3. Run the Application
You can now use the `python app.py` command followed by the feature you want to use.

**Examples:**

*   **Market Overview (Top 20 Market Cap):**
    ```bash
    python app.py list
    ```
*   **Check Stock Price:**
    ```bash
    python app.py stock AAPL
    ```
*   **View Stock Chart (30 Days):**
    ```bash
    python app.py stock TSLA --plot
    ```
*   **Company Overview:**
    ```bash
    python app.py overview MSFT
    ```
*   **Check Crypto Price:**
    ```bash
    python app.py crypto bitcoin
    ```
*   **Read Tech News:**
    ```bash
    python app.py news --category technology
    ```
*   **Manage Watchlist:**
    ```bash
    python app.py watchlist add NVDA
    python app.py watchlist show
    ```

---

## How to Run (Docker Environment)

Use this method to run the application in an isolated container without installing Python libraries locally.

### Method A: Using Docker Compose (Recommended)

1.  **Build the Image:**
    ```bash
    docker compose build
    ```

2.  **Run Commands:**
    Use `docker compose run` to execute commands. The `.env` file is loaded automatically.

    ```bash
    # Market Overview
    docker compose run --rm app list

    # Check Stock
    docker compose run --rm app stock AAPL

    # Check Forex
    docker compose run --rm app forex USD THB

    # Show Watchlist
    docker compose run --rm app watchlist show
    ```

### Method B: Using Dockerfile manually

1.  **Build the Image:**
    ```bash
    docker build -t invest-cli .
    ```

2.  **Run Container:**
    You must pass the `.env` file explicitly.

    ```bash
    docker run --rm --env-file .env invest-cli stock MSFT --plot
    ```

---

## Command Reference

| Command | Arguments | Description | Example |
| :--- | :--- | :--- | :--- |
| `list` | - | Show Top 20 Companies by Market Cap. | `python app.py list` |
| `stock` | `<SYMBOL>` `[--plot]` | Get stock price or history chart. | `python app.py stock AAPL --plot` |
| `overview` | `<SYMBOL>` | Get company fundamentals (PE, Sector). | `python app.py overview GOOGL` |
| `crypto` | `<COIN_ID>` or `trending` | Get coin price or top 15 trending. | `python app.py crypto ethereum` |
| `forex` | `<FROM>` `<TO>` | Check exchange rate. | `python app.py forex USD EUR` |
| `news` | `--category <CAT>` | Get top headlines (business, tech, etc.). | `python app.py news --category sports` |
| `search` | `<KEYWORD>` | Search news & generate Twitter link. | `python app.py search "AI"` |
| `watchlist` | `add <SYMBOL>` | Add stock to watchlist. | `python app.py watchlist add AAPL` |
| `watchlist` | `remove <SYMBOL>` | Remove stock from watchlist. | `python app.py watchlist remove AAPL` |
| `watchlist` | `show` | Show all saved stocks with live prices. | `python app.py watchlist show` |

---

## Project Structure

```text
.
├── .env                  # [Config] API Keys (User must create this)
├── .gitattributes        # [Git] Git configuration
├── .gitignore            # [Git] Files to ignore
├── app.py                # [Source] Main application code (Typer CLI)
├── compose.yml           # [Docker] Docker Compose configuration
├── Dockerfile            # [Docker] Instructions to build the Docker image
├── README.md             # [Doc] Project documentation
└── requirements.txt      # [Config] List of Python dependencies
```

---

## Troubleshooting & API Limits

**Alpha Vantage (Free Tier) Limitations:**
*   **Limit:** 5 API calls per minute / 500 calls per day.
*   **Impact:**
    *   When running `python app.py list` (Market Overview), the app attempts to fetch data for 20 companies.
    *   You will likely see data for the first 5 companies, and the rest will show **"API Limit Hit"**.
    *   This is normal behavior for the free key. The app handles this gracefully without crashing.
    *   **Solution:** Wait 1 minute before running another command.

**CoinGecko & NewsAPI:**
*   These APIs have generous free tiers and usually work without issues for standard usage.

---

### Technologies Used
*   **Python 3.10+**
*   **Typer:** For building the CLI interface.
*   **Rich:** For beautiful terminal formatting (Tables, Colors).
*   **Requests:** For handling API calls.
*   **AsciiChartPy:** For drawing price charts in the terminal.
*   **Docker:** For containerization.



