CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT,
    email TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    total REAL,
    order_date TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name TEXT,
    price REAL,
    category TEXT
);

CREATE TABLE IF NOT EXISTS order_items (
    order_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    PRIMARY KEY (order_id, product_id),
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Create indexes to show optimizer differences
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);

-- ============ SAMPLE QUERIES TO COMPARE ============

-- Query 1: Simple join (users + orders)
-- EXPLAIN QUERY PLAN SELECT u.name, o.total FROM users u JOIN orders o ON u.id = o.user_id;

-- Query 2: Join with aggregation
-- EXPLAIN QUERY PLAN SELECT u.name, COUNT(o.id) as order_count FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id;

-- Query 3: Three-table join
-- EXPLAIN QUERY PLAN SELECT u.name, p.name as product_name, oi.quantity FROM users u JOIN orders o ON u.id = o.user_id JOIN order_items oi ON o.id = oi.order_id JOIN products p ON oi.product_id = p.id;

-- Query 4: Aggregation only
-- EXPLAIN QUERY PLAN SELECT category, COUNT(*) as count, AVG(price) as avg_price FROM products GROUP BY category;

-- Query 5: Subquery (often less optimal)
-- EXPLAIN QUERY PLAN SELECT * FROM orders WHERE user_id IN (SELECT id FROM users WHERE name LIKE 'A%');

-- Query 6: Same result with JOIN (often more optimal)
-- EXPLAIN QUERY PLAN SELECT o.* FROM orders o JOIN users u ON o.user_id = u.id WHERE u.name LIKE 'A%';
