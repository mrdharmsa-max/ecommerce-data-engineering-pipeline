# E-commerce Data Engineering Pipeline

An end-to-end data engineering project that processes e-commerce customer, product, and order data using Python, SQL, PostgreSQL, and Apache Airflow.

**Version 1:** SQLite-based ETL and SQL analytics
**Version 2:** PostgreSQL, incremental ETL, execution
logging, and Airflow orchestration

## Project Overview

This project demonstrates how to build and improve an e-commerce data pipeline, from raw CSV files to structured database tables and SQL analytics.

The first version uses SQLite for data storage and analytics. The second version introduces PostgreSQL, file fingerprint-based incremental processing, ETL run logging, and Apache Airflow for workflow orchestration.

## Architecture

### Version 1 — SQLite Pipeline

```text
CSV Data Sources
       |
       v
Python ETL Pipeline
       |
       v
Data Cleaning and Validation
       |
       v
SQLite Database
       |
       v
SQL Analytics
```

### Version 2 — PostgreSQL and Airflow

```text
Customers / Products / Orders CSV
                 |
                 v
        File Fingerprint Check
                 |
                 v
       Apache Airflow DAG
                 |
                 v
       Python Incremental ETL
                 |
                 v
      Data Validation and Upsert
                 |
                 v
          PostgreSQL
                 |
                 v
        ETL Run Logging
```

## Tech Stack

- **Language:** Python
- **Data Processing:** Pandas
- **Databases:** SQLite, PostgreSQL
- **Database Connectivity:** Psycopg
- **Query Language:** SQL
- **Orchestration:** Apache Airflow
- **Containerization:** Docker and Docker Compose
- **Testing:** Pytest
- **Version Control:** Git and GitHub
- **Dashboard:** Streamlit (Version 1)

## Key Features

### Version 1

- Extracts e-commerce data from CSV files.
- Cleans and validates incoming records.
- Loads data into a SQLite database.
- Performs SQL-based analytics and revenue calculations.
- Includes automated tests and execution logging.
- Provides a Streamlit application for exploring project analytics.

### Version 2

- Integrates PostgreSQL as the primary data warehouse.
- Detects changes to source CSV files using SHA-256 fingerprints.
- Skips database processing when source files have not changed.
- Uses insert-and-update logic to handle new and modified records.
- Tracks inserted, updated, and unchanged records.
- Records ETL execution status, timestamps, row counts, and errors.
- Uses Apache Airflow to schedule and execute the ETL pipeline.
- Runs PostgreSQL and Airflow services through Docker Compose.

## Project Structure

```text
ecommerce-data-engineering-pipeline/
├── data/
│   ├── customers.csv
│   ├── products.csv
│   └── orders.csv
├── src/
│   ├── generate_data.py
│   ├── pipeline.py
│   ├── postgres_pipeline.py
│   └── incremental_utils.py
├── sql/
│   ├── analytics.sql
│   ├── schema.sql
│   └── etl_run_log.sql
├── tests/
│   └── test_pipeline.py
├── airflow/
│   └── dags/
│       └── ecommerce_etl_dag.py
├── app.py
├── run_sql.py
├── docker-compose.yml
├── docker-compose.airflow.yml
├── requirements.txt
└── README.md
```

Generated databases, logs, virtual environments, and other local runtime files may be excluded from version control.

## Getting Started

### Prerequisites

- Python installed
- Git
- Docker Desktop
- Docker Compose

### 1. Clone the repository

```bash
git clone https://github.com/mrdharmsa-max/ecommerce-data-engineering-pipeline.git
cd ecommerce-data-engineering-pipeline
```

### 2. Select the Version 2 branch

```bash
git checkout version-2-postgres
```

### 3. Create and activate a Python virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv-win
.\.venv-win\Scripts\Activate.ps1
```

### 4. Install Python dependencies

```powershell
python -m pip install -r requirements.txt
```

### 5. Start PostgreSQL

```powershell
docker compose up -d postgres
```

The local PostgreSQL configuration uses:

- Database: `ecommerce`
- Username: `ecommerce_user`
- Port: `5432`

Initialize the schema if required:

```powershell
docker exec -i ecommerce-postgres psql -U ecommerce_user -d ecommerce < sql/schema.sql
docker exec -i ecommerce-postgres psql -U ecommerce_user -d ecommerce < sql/etl_run_log.sql
```

The `etl_file_state` table must also exist for fingerprint-based processing. Create it if it is not already present:

```sql
CREATE TABLE IF NOT EXISTS etl_file_state (
    file_name TEXT PRIMARY KEY,
    fingerprint TEXT NOT NULL,
    last_processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 6. Run the PostgreSQL ETL pipeline

Activate the Python environment and run:

```powershell
python src/postgres_pipeline.py
```

The pipeline reads CSV files, detects source-file changes, performs database upserts, and records each execution in `etl_run_log`.

### 7. Run automated tests

```powershell
python -m pytest -q
```

### 8. Start Apache Airflow

Ensure the PostgreSQL container is running and the Docker network `ecommerce-data-pipeline_default` exists.

Initialize Airflow's metadata database and administrator account:

```powershell
docker compose -f docker-compose.airflow.yml up airflow-init
```

Start the Airflow webserver and scheduler:

```powershell
docker compose -f docker-compose.airflow.yml up -d airflow-webserver airflow-scheduler
```

Open the local Airflow interface:

**http://localhost:8080**

Use the administrator credentials configured in your local Compose file.

The DAG is named `ecommerce_postgres_etl`. It is configured for daily scheduling at 08:00 UTC (13:30 India Standard Time).

**Note:** This is a local development setup. Keep development credentials private and do not expose the Airflow interface publicly.

## Version 1 Live Demo

Explore the existing Streamlit application:

https://ecommerce-data-engineering-pipeline.streamlit.app/

The live application represents Version 1. Version 2 is developed separately on the `version-2-postgres` branch.

## Future Improvements

- Add dedicated tests for PostgreSQL incremental processing.
- Improve transaction handling and recovery after ETL failures.
- Add stronger data-quality checks and monitoring.
- Secure credentials using environment variables or a secrets manager.
- Build a custom Airflow image with pinned dependencies.
- Deploy the pipeline to a cloud environment.
- Expand analytics and reporting capabilities.

## Author

Developed as an end-to-end data engineering portfolio project using Python, SQL, PostgreSQL, Docker, and Apache Airflow.
