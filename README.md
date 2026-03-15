# Database Query Optimizer Simulator (SQL + Python)

Simulates how SQL optimizers choose query plans using SQLite's EXPLAIN QUERY PLAN.

## What it does

1. Creates sample tables in SQLite (users, orders, products, order_items).
2. Runs several SQL queries (joins, aggregations, subquery vs JOIN).
3. Parses and compares EXPLAIN QUERY PLAN output.
4. Estimates cost (simple rules: SCAN = expensive, SEARCH = cheaper).
5. Visualizes execution plans as graphs (saved as PNG).
6. Suggests better alternatives and writes an optimization report.

## Setup

1. Install Python dependencies (for graphs):

   ```bash
   py -m pip install -r requirements.txt
   ```

2. Run the optimizer (from this folder):

   ```bash
   py optimizer.py
   ```

## Deliverables

- **optimizer.py** – main script (parsing, cost estimation, visualization, report).
- **queries.sql** – table definitions and comment references to the queries used.
- **optimization_report.txt** – generated report with costs and suggestions.
- **plan_*.png** – execution plan visualizations.

## Submitting for points

Upload your project to a GitHub repository or record a short demo video, then share the link on the required platform to complete the mission.
