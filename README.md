# 📦 Warehouse Management System (WMS) - MVP

This is a complete MVP implementation of the **WMS Assignment** from CSTE, focused on automating SKU-to-MSKU mapping, sales data processing, dashboards, and AI-powered querying.

## 🧩 Project Overview

The Warehouse Management System (WMS) MVP provides a comprehensive solution for:
- Mapping platform-specific SKUs to Master SKUs (MSKUs)
- Processing and visualizing sales data
- Creating interactive dashboards
- Enabling natural language queries over the data

| Part | Module                              | Tech Stack                           | Status |
|------|-------------------------------------|--------------------------------------|--------|
| 1    | SKU to MSKU Mapping                 | Python, Pandas, Tkinter              | ✅ Done |
| 2    | Data Dashboard                      | Airtable/Local Dashboard             | ✅ Done |
| 3    | Web App Integration                 | Flask, HTML, CSS, JavaScript         | ✅ Done |
| 4    | AI Query Layer + Visualization      | DuckDB, Gemini AI, Chart.js          | ✅ Done |

## ✅ Part 1: SKU to MSKU Mapping

- **Functionality**: Maps platform-specific SKUs to MSKUs using a master mapping file
- **Features**:
  - Handles combo SKUs (e.g., `A+B+C`)
  - Validates SKU formats
  - Generates detailed error logs
  - Supports multiple input formats (Excel, CSV)
- **Implementation**:
  - `MappingLoader` class for loading and managing mapping data
  - `SalesProcessor` class for processing sales data and applying mappings
  - Tkinter GUI for easy file selection and processing

## ✅ Part 2: Data Dashboard

- **Implementation Options**:
  - **Airtable**: Set up a relational database with visual dashboards
  - **Local Dashboard**: Built-in web dashboard as a fallback
- **Features**:
  - Visualize sales data by product, region, platform
  - Filter and sort data
  - Download processed data in various formats
  - Interactive charts and graphs

## ✅ Part 3: Web Application

- **Technology**: Flask web framework with responsive frontend
- **Features**:
  - Upload sales and mapping files
  - Process data with a single click
  - View and download processed outputs
  - Interactive data tables and visualizations
  - Embedded dashboard for data analysis

## ✅ Part 4: AI-Powered Query Layer

- **Technology**: DuckDB with Gemini AI integration
- **Features**:
  - Ask questions in natural language (e.g., "Show me top 5 products by sales")
  - AI converts questions to SQL queries
  - Results displayed as tables and interactive charts
  - Support for various query types (top products, trends, distributions)

## 🖥️ Demo Screenshots

![Home Page](static/screenshots/home.png)
![AI Dashboard](static/screenshots/ai-dashboard.png)

## 🎥 Loom Demo Video

Check out the full walkthrough of the WMS MVP in this Loom video:
https://www.loom.com/share/bdb9255db8a24cd29a98a3b805c3ae57?sid=6b6ef988-5848-4817-979f-df8062df59f0

## 📁 Project Structure

WMS-Assignment/
├── part1_sku_mapping/
│   ├── sku_mapper.py         # Core mapping logic
│   ├── gui.py                # Tkinter GUI interface
│   └── data/                 # Sample data files
│
├── part2_database/
│   └── Airtables.txt         # Setup instructions for Airtable
│
├── part3_webapp/
│   ├── app.py                # Flask web application
│   ├── templates/            # HTML templates
│   ├── static/               # CSS, JS, and assets
│   │   ├── js/               # JavaScript files for dashboard
│   │   ├── css/              # Styling
│   │   ├── outputs/          # Processed data outputs
│   │   └── screenshots/      # Application screenshots
│
├── .env                      # Environment variables (API keys)
└── README.md                 # Project documentation


## 🛠 Technologies Used

- **Backend**: Python, Flask, Pandas, DuckDB
- **Frontend**: HTML, CSS, JavaScript, Chart.js
- **Data Processing**: Pandas, NumPy
- **AI Integration**: Gemini AI via OpenRouter API
- **Database**: Airtable API, DuckDB (in-memory)
- **Visualization**: Chart.js, Bootstrap

## 🚀 How to Run

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables in `.env` file
4. Run the web application: `python part3_webapp/app.py`
5. Access the application at `http://localhost:5000`

## 👨‍💻 Created By

Rohan Moura
For CSTE WMS Automation Assignment  
May 2024
