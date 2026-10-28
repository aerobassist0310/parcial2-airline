-- Ejecutar cada sentencia individualmente y guardar QueryExecutionId y bytes escaneados.
SELECT count(*) FROM reservations_curated;
SHOW PARTITIONS reservations_curated;
SELECT month, count(*) AS filas, sum(CASE WHEN status='CONFIRMED' THEN price_cents ELSE 0 END) AS ingresos
FROM reservations_curated GROUP BY month ORDER BY month;
SELECT route, CAST(sum(seats_sold) AS DOUBLE)/sum(seats_capacity) AS occupancy
FROM route_month_metrics GROUP BY route ORDER BY occupancy DESC LIMIT 10;
-- Cambiar el mes por uno REAL del conjunto completo.
SELECT count(*), sum(price_cents) FROM reservations_curated WHERE month='CAMBIAR';
