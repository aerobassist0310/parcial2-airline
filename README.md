# Sistema de reservas aéreas y panel de analítica gerencial

Segundo parcial de Big Data e Ingeniería de Datos. Salvatore Victorino y Maria Camila Alfonso.

Sistema de reservas de vuelos con un frontend web, un backend transaccional y un camino de procesamiento
histórico en AWS (EMR → S3/Parquet → Glue Data Catalog → Athena) que alimenta un panel gerencial de
ocupación por ruta y mes.

**Resultado del evaluador del docente: 70/70** ([report.md](report.md)), ejecutado el 28 de octubre de 2026.

## Arquitectura

| Componente | Servicio | Detalle |
|---|---|---|
| API y frontend | EC2 t3.small (Ubuntu 24.04) | `backend/` sirve la API y las páginas de `frontend/` en el puerto 8000, como servicio systemd |
| Base transaccional | RDS PostgreSQL db.t3.micro, Single-AZ | Sin acceso público; solo la EC2 llega al puerto 5432 |
| Datos | S3 (`p2-airline-salvatore-20261027`) | `full/raw/` (CSV), `full/curated/` y `full/metrics/` (Parquet), `athena-results/`, `emr-logs/` |
| Lote histórico | EMR emr-spark-8.0.0, 1 primary + 1 core m4.large | `jobs/etl_occupancy.py` aplica C1–C5 y escribe Parquet particionado por mes |
| Catálogo y consultas | Glue Data Catalog + Athena | Base `airline_analytics`, tablas `reservations_curated` y `route_month_metrics` |

Las reservas solo tocan RDS; el panel solo consulta Athena. Así la analítica nunca compite con las reservas.

## Estructura

```text
backend/         API (servidor HTTP de la biblioteca estándar; SQLite o PostgreSQL)
frontend/        Tienda (/) y panel gerencial (/manager) con los data-testid del contrato
jobs/            Trabajo PySpark para EMR
sql/             DDL de Glue/Athena y consultas de comprobación
deploy/          Unidad systemd y archivos de entorno (Athena, RDS) tal como se desplegaron
scripts/         Utilidades: solicitud EMR, verificación con Athena, prueba de concurrencia
airline_data/    Generador y oráculo del docente (sin modificar)
harness/, tests/ Evaluador del docente (sin modificar; hashes en ORIGINALES_SHA256.json)
contract/        Contratos del docente (API, datos, frontend, costos)
docs/kit/        Guías y validación local del paquete inicial
config.yaml      Configuración del evaluador (sin credenciales)
cost_projection.yaml  Proyección mensual de costos (34,48 USD)
report.md, report.json  Resultado del evaluador
PROMPT_LOG.md    Registro de uso de IA
```

## Datos y lote EMR

El histórico se generó con el generador original, con semilla **12345** (el docente no asignó una):

```bash
python -m airline_data.generate --seed 12345 --rows 2000000 --out raw-full/
```

Resultado: 12.480 vuelos y 2.087.701 reservas sin limpiar, que quedan en 2.017.079 reservas limpias.

El lote se ejecuta como un paso **Custom JAR** (`command-runner.jar`) con estos argumentos:

```text
spark-submit --deploy-mode client --driver-memory 1g --executor-memory 2g --executor-cores 1 --num-executors 1 --conf spark.dynamicAllocation.enabled=false s3://p2-airline-salvatore-20261027/code/etl_occupancy.py --flights s3://p2-airline-salvatore-20261027/full/raw/flights.csv --reservations s3://p2-airline-salvatore-20261027/full/raw/reservations.csv --detail-out s3://p2-airline-salvatore-20261027/full/curated/reservations_curated/ --metrics-out s3://p2-airline-salvatore-20261027/full/metrics/route_month_metrics/
```

- **Modo client y memoria explícita:** con un solo nodo core, en modo cluster el driver deja sin memoria
  YARN al ejecutor y el trabajo queda en RUNNING sin avanzar.
- **Custom JAR en lugar del formulario "Spark application":** al clonar un clúster, ese formulario perdió
  la ruta del script.
- **Terminación:** el clúster debe tener *Automatically terminate cluster after last step ends*. Revisarlo
  en cada clon y confirmar al final que el estado sea TERMINATED (R10).

`scripts/build_emr_request.py` genera la misma configuración como solicitud para la CLI de AWS.

## Glue y Athena

Las tablas se crean con el DDL de `sql/catalog.sql.template`, o con:

```bash
python -m scripts.verificar_athena --prefix full --rows 2000000 --recrear-tablas
```

Ese script también compara R4–R7 con el oráculo. `DROP TABLE` solo borra la definición en el catálogo,
nunca los Parquet de S3.

## Despliegue de la aplicación (EC2)

1. Copiar el código al servidor, crear `.venv` e instalar `requirements-app.txt`.
2. Copiar `deploy/airline.service` a `/etc/systemd/system/`.
3. Copiar `deploy/airline.service.d/athena.conf` y crear `rds.conf` a partir de `rds.conf.example`
   (con `sudo chmod 600`, porque contiene la contraseña).
4. `sudo systemctl daemon-reload && sudo systemctl enable --now airline`.

La aplicación crea sus tablas en PostgreSQL al arrancar. El perfil de instancia `LabInstanceProfile` le da
acceso a Athena y S3 sin claves en el código.

## Ejecutar el evaluador

```bash
python -m venv .venv-harness
.venv-harness/Scripts/python -m pip install -r requirements-harness.txt
.venv-harness/Scripts/python -m playwright install chromium
.venv-harness/Scripts/python -m pytest
```

Requiere las credenciales temporales del Learner Lab en `~/.aws/credentials` (AWS Details → AWS CLI),
que nunca se suben al repositorio. Antes de cada ejecución hay que actualizar la IP pública de la EC2 en
`config.yaml`, porque cambia cuando el laboratorio se reinicia. Para la evaluación del docente, el puerto
8000 debe estar abierto a todos durante la ventana acordada.

## Costos

Proyección mensual de 34,48 USD (ver `cost_projection.yaml`): EC2 19,47; RDS 14,71; S3, Athena y EMR
0,10 cada uno; Glue 0. Fuera de las sesiones de trabajo se detienen EC2 y RDS.
