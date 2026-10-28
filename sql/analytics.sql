
-- 1. Revenue by product (excluding cancelled orders)
SELECT
    p.product_name,
    SUM(f.quantity) AS units_sold,
    SUM(f.revenue) AS total_revenue
FROM fact_orders f
JOIN dim_product p ON f.product_id = p.product_id
WHERE f.status != 'cancelled'
GROUP BY p.product_id, p.product_name
ORDER BY total_revenue DESC;

-- 2. Daily sales
SELECT
    order_date,
    COUNT(*) AS total_orders,
    ROUND(SUM(revenue), 2) AS total_revenue
FROM fact_orders
WHERE status != 'cancelled'
GROUP BY order_date
ORDER BY order_date;

-- 3. Top customers by delivered revenue
SELECT
    c.name,
    c.city,
    ROUND(SUM(f.revenue), 2) AS delivered_revenue
FROM fact_orders f
JOIN dim_customer c ON f.customer_id = c.customer_id
WHERE f.status = 'delivered'
GROUP BY c.customer_id, c.name, c.city
ORDER BY delivered_revenue DESC;

-- 4. Check for duplicate order IDs
SELECT order_id, COUNT(*) AS occurrences
FROM fact_orders
GROUP BY order_id
HAVING COUNT(*) > 1;

-- 5. Revenue by order status
SELECT
    status,
    COUNT(*) AS order_count,
    ROUND(SUM(revenue), 2) AS order_value
FROM fact_orders
GROUP BY status
ORDER BY order_count DESC;
