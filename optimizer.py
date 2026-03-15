
import sqlite3
import re
import os


def get_connection():
    """Connect to SQLite database."""
    conn = sqlite3.connect("sample.db")
    return conn

def setup_database(conn):
    """Create tables from queries.sql and add sample data."""
    with open("queries.sql", "r") as f:
        sql = f.read()
    create_part = sql.split("-- ============ SAMPLE QUERIES")[0]
    conn.executescript(create_part)
    conn.commit()

    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO users (id, name, email, created_at) VALUES (?, ?, ?, ?)",
            [(1, "Alice", "alice@example.com", "2024-01-01"), (2, "Bob", "bob@example.com", "2024-01-02"), (3, "Charlie", "charlie@example.com", "2024-01-03")]
        )
        cur.executemany(
            "INSERT INTO orders (id, user_id, total, order_date) VALUES (?, ?, ?, ?)",
            [(1, 1, 99.99, "2024-02-01"), (2, 1, 50.00, "2024-02-02"), (3, 2, 120.00, "2024-02-03")]
        )
        cur.executemany(
            "INSERT INTO products (id, name, price, category) VALUES (?, ?, ?, ?)",
            [(1, "Widget", 19.99, "A"), (2, "Gadget", 29.99, "B"), (3, "Gizmo", 9.99, "A")]
        )
        cur.executemany(
            "INSERT INTO order_items (order_id, product_id, quantity) VALUES (?, ?, ?)",
            [(1, 1, 2), (1, 2, 1), (2, 3, 5), (3, 1, 1)]
        )
        conn.commit()
    cur.close()

# -------- QUERIES TO ANALYZE --------

# Each item: (name, sql_query)
QUERIES = [
    ("Simple join", "SELECT u.name, o.total FROM users u JOIN orders o ON u.id = o.user_id"),
    ("Join with aggregation", "SELECT u.name, COUNT(o.id) as order_count FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id"),
    ("Three-table join", "SELECT u.name, p.name, oi.quantity FROM users u JOIN orders o ON u.id = o.user_id JOIN order_items oi ON o.id = oi.order_id JOIN products p ON oi.product_id = p.id"),
    ("Aggregation only", "SELECT category, COUNT(*) as count, AVG(price) as avg_price FROM products GROUP BY category"),
    ("Subquery (IN)", "SELECT * FROM orders WHERE user_id IN (SELECT id FROM users WHERE name LIKE 'A%')"),
    ("Same with JOIN", "SELECT o.* FROM orders o JOIN users u ON o.user_id = u.id WHERE u.name LIKE 'A%'"),
]

# -------- PARSE EXPLAIN QUERY PLAN --------

def run_explain(conn, sql):
    """Run EXPLAIN QUERY PLAN and return list of lines."""
    cur = conn.cursor()
    cur.execute("EXPLAIN QUERY PLAN " + sql)
    rows = cur.fetchall()
    cur.close()
    return rows

def parse_plan_rows(rows):
    """Turn EXPLAIN rows into a simple list of step descriptions."""
    steps = []
    for row in rows:
        # row is (selectid, order, from, detail)
        detail = row[3] if len(row) > 3 else str(row)
        steps.append(detail)
    return steps

# -------- COST ESTIMATION (SIMPLE) --------

def estimate_cost(steps):
    """
    Simple cost: SCAN table = expensive, SEARCH with index = cheaper.
    Returns a number (lower = better).
    """
    cost = 0
    for step in steps:
        step_upper = step.upper()
        if "SCAN" in step_upper and "INDEX" not in step_upper:
            cost += 10   # full table scan
        elif "SEARCH" in step_upper:
            cost += 2    # index search
        elif "LIST SUBQUERY" in step_upper or "CORRELATED" in step_upper:
            cost += 5
        else:
            cost += 1
    return cost


def build_plan_graph(steps, query_name):
    """Build a simple graph: each step is a node, order is edges."""
    try:
        import networkx as nx
        import matplotlib.pyplot as plt
    except ImportError:
        print("(Skipping graph for '" + query_name + "'. Install: py -m pip install networkx matplotlib)")
        return

    G = nx.DiGraph()
    for i, step in enumerate(steps):
        short = step[:40] + "..." if len(step) > 40 else step
        G.add_node(i, label=short)
        if i > 0:
            G.add_edge(i - 1, i)
    if len(steps) == 1:
        G.add_node(0, label=steps[0][:50])

    pos = nx.spring_layout(G, seed=42)
    plt.figure(figsize=(10, 6))
    nx.draw(G, pos, with_labels=True, labels={i: steps[i][:30] for i in range(len(steps))}, font_size=8, node_color="lightblue", arrows=True)
    plt.title("Execution plan: " + query_name)
    plt.axis("off")
    plt.tight_layout()
    safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in query_name)
    plt.savefig("plan_" + safe_name + ".png", dpi=100)
    plt.close()
    print("Saved plan_" + safe_name + ".png")

# -------- SUGGEST ALTERNATIVES --------

def suggest_alternatives(name, sql, cost, steps):
    """Suggest better query if we see expensive patterns."""
    suggestions = []
    steps_text = " ".join(steps).upper()
    if "SUBQUERY" in steps_text and "IN (" in sql.upper():
        suggestions.append("Using IN (subquery) can be slow. Try rewriting with JOIN.")
    if "SCAN " in steps_text and "INDEX" not in steps_text:
        suggestions.append("Full table SCAN detected. Consider adding an INDEX on filtered/joined columns.")
    if "CORRELATED" in steps_text:
        suggestions.append("Correlated subquery may run many times. A JOIN might be faster.")
    return suggestions

# -------- MAIN: RUN ALL AND WRITE REPORT --------

def main():
    print("Database Query Optimizer Simulator")
    print("-----------------------------------")

    if not os.path.exists("queries.sql"):
        print("Error: queries.sql not found. Run this script from the project folder.")
        return

    conn = get_connection()
    setup_database(conn)

    results = []

    for name, sql in QUERIES:
        rows = run_explain(conn, sql)
        steps = parse_plan_rows(rows)
        cost = estimate_cost(steps)
        results.append((name, sql, steps, cost))
        build_plan_graph(steps, name)

    conn.close()

    # Build report
    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("OPTIMIZATION REPORT")
    report_lines.append("=" * 60)
    report_lines.append("")

    for name, sql, steps, cost in results:
        report_lines.append("Query: " + name)
        report_lines.append("SQL: " + sql[:80] + ("..." if len(sql) > 80 else ""))
        report_lines.append("Estimated cost: " + str(cost) + " (lower is better)")
        report_lines.append("Plan steps:")
        for s in steps:
            report_lines.append("  - " + s)
        suggestions = suggest_alternatives(name, sql, cost, steps)
        if suggestions:
            report_lines.append("Suggestions:")
            for s in suggestions:
                report_lines.append("  * " + s)
        report_lines.append("")

    # Comparison: which query is best in each "pair"
    report_lines.append("--- Comparison (subquery vs JOIN) ---")
    subq = next((r for r in results if "Subquery" in r[0]), None)
    join = next((r for r in results if "Same with JOIN" in r[0]), None)
    if subq and join:
        c1, c2 = subq[3], join[3]
        report_lines.append("Subquery (IN) cost: " + str(c1))
        report_lines.append("JOIN version cost: " + str(c2))
        if c2 < c1:
            report_lines.append("Recommendation: Prefer the JOIN version for better performance.")
        else:
            report_lines.append("Both plans are similar; use whichever is clearer.")
    report_lines.append("")
    report_lines.append("=" * 60)

    report_text = "\n".join(report_lines)
    with open("optimization_report.txt", "w") as f:
        f.write(report_text)
    print("\nReport saved to optimization_report.txt")
    print(report_text)

if __name__ == "__main__":
    main()
