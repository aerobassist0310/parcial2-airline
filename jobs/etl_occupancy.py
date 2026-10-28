"""Trabajo Spark para el generador entregado: CSV sin campos multilínea."""
import argparse
import csv
from pyspark.sql import SparkSession, functions as F, types as T, Window

def reservation_record(item):
    line, index = item
    values = next(csv.reader([line]))
    if len(values) != 6:
        raise ValueError(f"CSV inesperado en ordinal {index}; se esperan 6 columnas")
    return (int(index),) + tuple(values)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--flights', required=True)
    p.add_argument('--reservations', required=True)
    p.add_argument('--detail-out', required=True)
    p.add_argument('--metrics-out', required=True)
    a = p.parse_args()
    if any(c in a.reservations for c in ['*', '?', '[', ',']):
        raise ValueError('Se requiere un único reservations.csv sin comodines')
    spark = SparkSession.builder.appName('airline-parcial2').getOrCreate()
    spark.conf.set('spark.sql.shuffle.partitions', '24')
    spark.conf.set('spark.sql.ansi.enabled', 'false')
    flights = (spark.read.option('header', True).schema('flight_id string, route string, flight_date string, capacity long').csv(a.flights)
        .withColumn('route', F.upper(F.regexp_replace('route', r'\s+', '')))
        .withColumn('month', F.substring('flight_date', 1, 7)))
    if flights.groupBy('flight_id').count().filter('count > 1').limit(1).count():
        raise ValueError('flight_id duplicado: revisar archivo de vuelos')
    lines = spark.sparkContext.textFile(a.reservations)
    header = next(csv.reader([lines.first()]))
    expected = ['reservation_id', 'flight_id', 'fare_class', 'price_cents', 'status', 'days_before_departure']
    if header != expected:
        raise ValueError(f'Cabecera distinta: {header}')
    indexed = lines.zipWithIndex().filter(lambda x: x[1] > 0).map(reservation_record)
    schema = T.StructType([T.StructField('_ordinal', T.LongType(), False)] +
                          [T.StructField(c, T.StringType(), True) for c in expected])
    reservations = spark.createDataFrame(indexed, schema)
    reservations = (reservations.withColumn('status', F.upper(F.regexp_replace('status', r'^\s+|\s+$', '')))
        .withColumn('price_cents', F.col('price_cents').cast('long'))
        .filter(F.col('status').isin('CONFIRMED', 'CANCELLED'))
        .filter(F.col('price_cents').isNotNull() & (F.col('price_cents') > 0)))
    order = Window.partitionBy('reservation_id').orderBy('_ordinal')
    reservations = reservations.withColumn('_n', F.row_number().over(order)).filter('_n = 1').drop('_n', '_ordinal')
    detail = reservations.join(flights.select('flight_id', 'route', 'month'), 'flight_id', 'inner').select(
        'reservation_id', 'flight_id', 'route', 'fare_class', 'price_cents', 'status', 'month').cache()
    if detail.filter(F.col('month').isNull()).limit(1).count():
        raise ValueError('month nulo')
    detail_count = detail.count()
    months = detail.select('month').distinct().count()
    detail.repartition('month').write.mode('overwrite').option('compression','snappy').partitionBy('month').parquet(a.detail_out)
    cap = flights.groupBy('route', 'month').agg(F.sum('capacity').cast('long').alias('seats_capacity'))
    is_confirmed = F.col('status') == 'CONFIRMED'
    agg = detail.groupBy('route', 'month').agg(
        F.sum(F.when(is_confirmed, 1).otherwise(0)).cast('long').alias('seats_sold'),
        F.sum(F.when(is_confirmed, F.col('price_cents')).otherwise(0)).cast('long').alias('revenue_cents'),
        F.sum(F.when(is_confirmed, 1).otherwise(0)).cast('long').alias('bookings'),
        F.sum(F.when(F.col('status') == 'CANCELLED', 1).otherwise(0)).cast('long').alias('cancellations'))
    metrics = cap.join(agg, ['route', 'month'], 'left').fillna(0).withColumn('occupancy',
        F.when(F.col('seats_capacity') > 0, F.col('seats_sold').cast('double')/F.col('seats_capacity')).otherwise(F.lit(0.0)))
    metrics = metrics.select('route', 'month', 'seats_capacity', 'seats_sold', 'occupancy', 'revenue_cents', 'bookings', 'cancellations')
    # Sin particionar métricas: conserva month en la posición que verifica test_analytics.py.
    metrics.coalesce(1).write.mode('overwrite').option('compression','snappy').parquet(a.metrics_out)
    print({'curated_rows': detail_count, 'month_partitions': months, 'bookings_definition': 'CONFIRMED'})
    detail.unpersist()
    spark.stop()

if __name__ == '__main__':
    main()
