
# E-commerce Data Engineering Pipeline

## Project Overview
An end-to-end data engineering project that processes
e-commerce customers, products, and order data using
Python, SQL, and SQLite.

## Architecture
CSV Data Sources
       |
       v
Python ETL Pipeline
       |
       v
Data Cleaning and Validation
       |
       v
SQLite Data Warehouse
       |
       v
SQL Analytics

## Tech Stack
- Python
- Pandas
- SQL
- SQLite
- Pytest
- Git and GitHub

## Key Features
- Extracts data from CSV files
- Removes duplicate order records
- Transforms and joins customer and product data
- Loads data into a SQLite warehouse
- Calculates revenue for orders
- Performs data quality checks
- Logs pipeline execution
- Includes automated tests

## Project Structure
- data/: Input CSV datasets
- src/: Python ETL scripts
- sql/: SQL analytics queries
- tests/: Automated tests
- run_sql.py: Runs analytics queries
- pipeline.log: Runtime log (generated locally)
- ecommerce.db: SQLite database (generated locally)

## How to Run

### 1. Create a virtual environment
python -m venv .venv

### 2. Activate on Windows
.venv\Scripts\Activate.ps1

### 3. Install dependencies
python -m pip install pandas pytest

### 4. Generate sample data
python src/generate_data.py

### 5. Run the ETL pipeline
python src/pipeline.py

### 6. Run SQL analytics
python run_sql.py

### 7. Run automated tests
python -m pytest -q

## Future Improvements
- PostgreSQL integration
- Apache Airflow orchestration
- Incremental data ingestion
- Cloud deployment
- Data quality monitoring
