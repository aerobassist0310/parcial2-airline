# Paquete de implementación — Salvatore Victorino y Maria Camila Alfonso

## Qué es y qué no es

Base de implementación y guía de integración para el Parcial 2. Incluye una API alternativa, frontend, trabajo PySpark, SQL, herramientas locales y los archivos del evaluador recibidos sin modificaciones. No hay despliegue AWS ejecutado ni garantía de aprobar R1–R12.

PRIMERO: leer ADVERTENCIAS_TECNICAS.md y VALIDACION_LOCAL.md.

Si ya existe backend del primer parcial: hacer copia/rama Git y comparar sus endpoints con contract/API.md. Conservar lo que funciona; backend/ puede servir como referencia de concurrencia y de integración Athena. No se tuvo acceso a ese código.

## Mapa de archivos

| Carpeta/archivo | Uso |
|---|---|
| backend/ | API, conexión transaccional y cliente Athena |
| frontend/ | Cliente y panel con los selectores oficiales |
| jobs/etl_occupancy.py | Trabajo a ejecutar REALMENTE en EMR |
| airline_data/ | Generador, parámetros y oráculo originales |
| sql/ | Catálogo y consultas de comprobación |
| scripts/ | Preparar JSON/SQL, inventario y validaciones |
| deploy/airline.service | Ejemplo de servicio persistente en EC2 |
| tests/, harness/, contract/ | Material entregado, reorganizado según sus imports |
| config.example.yaml | Ejemplo ORIGINAL del evaluador |
| .env.example | Variables de la aplicación; no confundir con config.yaml |
| aws-settings.example.json | Valores para generar SQL y solicitud EMR |
| cost_projection.template.yaml | Borrador con importes pendientes, no listo para entregar |

## 1. Preparación local

Los comandos siguientes son Bash (Linux, macOS o WSL), desde la raíz del paquete.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-app.txt
cp .env.example .env
# EDITAR .env, inicialmente DB_MODE=sqlite.
set -a; source .env; set +a
python -m backend.app
```

Abrir http://127.0.0.1:8000 y /manager. El frontend y la API usan EL MISMO puerto, no hace falta servidor Node ni puerto 3000. /manager necesita Athena configurado para obtener datos; no se simula una ocupación.

```bash
# En otra terminal, con la API iniciada:
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/admin/flights \
 -H 'Content-Type: application/json' \
 -d '{"flight_id":"DEMO-1","route":"BOG-MDE","flight_date":"2030-01-15","capacity":2,"price_cents":100000}'
curl 'http://127.0.0.1:8000/flights/search?origin=BOG&destination=MDE&date=2030-01-15'
```

DEMO es solo un ejemplo, no un dato del histórico ni un resultado del oráculo.

## 2. Probar el trabajo Spark antes de AWS

Requiere Java compatible con la versión instalada de Spark y recursos locales suficientes. Las dependencias Spark locales NO se instalan en EC2 si solo sirve la API; EMR ya incorpora Spark.

```bash
pip install -r requirements-data-local.txt
# Sustituir el valor por la asignación REAL del equipo.
export TEAM_SEED=VALOR_ASIGNADO
python -m airline_data.generate --seed "$TEAM_SEED" --rows 10000 --out raw-sample/
spark-submit jobs/etl_occupancy.py \
 --flights raw-sample/flights.csv --reservations raw-sample/reservations.csv \
 --detail-out local-output/detail --metrics-out local-output/metrics
python -m scripts.validate_parquet --seed "$TEAM_SEED" --rows 10000 \
 --detail local-output/detail --metrics local-output/metrics
```

No sustituir el histórico completo por una muestra. No cargar Parquet creado localmente como evidencia R4. Para la ejecución final, generar con --rows 2000000 y la misma semilla; los Parquet finales deben ser escritos por EMR.

## 3. Recursos AWS que Camila debe preparar

1. Iniciar Learner Lab y comprobar saldo, región y permisos. Ejecutar `aws sts get-caller-identity` en la terminal donde se usará CLI. Si usa credenciales temporales del laboratorio necesita también AWS_SESSION_TOKEN; NO guardarlas en Git.
2. Identificar roles y perfiles de instancia YA PERMITIDOS para EC2 y EMR. No asumir nombres ni crear IAM automáticamente. Verificar que el perfil EC2 puede consultar Athena, Glue y los prefijos S3 necesarios.
3. Crear un bucket S3 privado, en la región del proyecto, con bloqueo de acceso público. Usar prefijos distintos sample/ y full/ para no mezclar muestras con datos finales.
4. Crear RDS PostgreSQL permitido, Single-AZ, sin acceso público. Misma VPC que EC2. Permitir 5432 en el grupo RDS SOLO desde el grupo de EC2. Crear base airline y usuario para la aplicación según el método elegido.
5. Crear EC2 t3.small con perfil de instancia permitido, almacenamiento pequeño y conectividad saliente. Para evitar NAT, la instancia pública requiere la configuración de subred, ruta y dirección pública que el laboratorio permita. Restringir SSH a su IP; habilitar 8000 solo a los orígenes de desarrollo/evaluación necesarios. No abrir RDS a Internet.
6. Identificar una subred y grupos de seguridad aptos para EMR, con la conectividad exigida por el laboratorio. No asumir que toda subred EC2 sirve para EMR ni abrir SSH globalmente. Seleccionar una versión EMR disponible que soporte m4.large; si no existe o se deniega, consultar al docente antes de cambiar el tipo permitido.

Los scripts incluidos no crean VPC, IAM, RDS ni grupos de seguridad. Estos dependen del laboratorio y deben revisarse manualmente.

## 4. Desplegar aplicación en EC2

Transferir el paquete sin .env local ni credenciales. Instalar Python y crear un entorno virtual según el sistema operativo de la AMI. En /opt/airline instalar requirements-app.txt. Crear usuario de sistema airline y dar permisos sobre la carpeta de aplicación.

Crear /etc/airline.env usando .env.example, con DB_MODE=postgres y DATABASE_URL del RDS. No usar credenciales SQLite ni incluir claves AWS; preferir el perfil de la instancia. Si se exige validar certificado RDS, instalar su CA y cambiar sslmode=require por verify-full con sslrootcert; comprobar la conexión. El ejemplo require cifra, pero no valida identidad del servidor.

Configurar APP_HOST=0.0.0.0 y APP_PORT=8000, Athena y región. Restringir lectura de /etc/airline.env a root (systemd lo carga antes de cambiar usuario). Usar una contraseña/conninfo válida, sin publicar secretos en logs.

```bash
sudo chown root:root /etc/airline.env
sudo chmod 600 /etc/airline.env
sudo cp deploy/airline.service /etc/systemd/system/airline.service
sudo systemctl daemon-reload
sudo systemctl enable --now airline
sudo systemctl status airline
sudo journalctl -u airline -n 80 --no-pager
```

Estos comandos suponen que /opt/airline, el entorno virtual y el usuario YA existen. El esquema se crea al arrancar la aplicación; el usuario de DB necesita permisos de creación inicial. Revisar posibles conflictos si se integra una base del primer parcial; NO apuntar a una base existente sin respaldo y revisión.

Verificar /health, búsqueda y reserva. Confirmar reinicio del servicio y no depender de una terminal SSH abierta. La base académica usa HTTP; no tratarla como portal público de producción.

## 5. Preparar S3 y ejecutar EMR

```bash
cp aws-settings.example.json aws-settings.json
# EDITAR con bucket, subred, roles, grupos y versión reales.
python -m scripts.check_aws --settings aws-settings.json
```

Ejecutar las cargas SOLO después de verificar bucket y región. Sustituir BUCKET_REAL en cada comando.

```bash
aws s3 cp jobs/etl_occupancy.py s3://BUCKET_REAL/code/etl_occupancy.py
aws s3 cp raw-sample/flights.csv s3://BUCKET_REAL/sample/raw/flights.csv
aws s3 cp raw-sample/reservations.csv s3://BUCKET_REAL/sample/raw/reservations.csv
```

Poner data_prefix=sample para el primer ensayo, generar JSON y REVISARLO:

```bash
python -m scripts.build_emr_request
# Solo este comando crea recursos facturables; revisar request antes.
aws emr create-cluster --region REGION_REAL --cli-input-json file://emr-request.json
```

Guardar ClusterId. Consultar estado y pasos, sin relanzar por impaciencia:

```bash
aws emr describe-cluster --cluster-id ID_REAL --region REGION_REAL
aws emr list-steps --cluster-id ID_REAL --region REGION_REAL
```

La solicitud usa tres m4.large, termina al acabar y termina ante fallo del paso. Si permanece activo o falla el cierre, investigar y terminar explícitamente el clúster desde la consola/CLI, comprobando el ID. Un error de arranque también consume presupuesto.

Después del ensayo: generar el dataset completo, cargarlo en full/raw/, cambiar data_prefix=full, volver a generar el JSON y ejecutar una sola vez revisada. No mover Parquet de sample a full ni generar la evidencia final fuera de EMR.

## 6. Catálogo y Athena

Poner data_prefix=full para catalogar el conjunto completo. Las tablas apuntan exclusivamente a los prefijos finales, no a sample/ ni raw/.

```bash
python -m scripts.render_catalog --out catalog.sql
```

En Athena, seleccionar el workgroup y la ubicación de resultados s3://BUCKET_REAL/athena-results/. Revisar catalog.sql y ejecutar CADA sentencia por separado: crear base, tabla de detalle, MSCK REPAIR TABLE y tabla de métricas. Crear tablas no ejecuta el lote ni corrige archivos equivocados.

Si las tablas ya existían, IF NOT EXISTS no cambia sus ubicaciones ni tipos. Revisar `SHOW CREATE TABLE` y Glue; corregir metadatos explícitamente con cuidado. No borrar datos para resolver un error de metadatos.

Comprobar con sql/checks.sql: 24 meses, conteos, ingresos y top-10. Registrar QueryExecutionId y DataScannedInBytes para la consulta mensual. La tabla de métricas queda sin partición por el contrato concreto del evaluador; leer advertencia técnica antes de cambiarla.

## 7. Configurar y ejecutar el evaluador ORIGINAL

```bash
pip install -r requirements-harness.txt
playwright install chromium
cp config.example.yaml config.yaml
```

Editar config.yaml con semilla REAL, team_id real, URLs actuales, región, database, tablas, workgroup y resultados Athena. Como ambos se sirven en el mismo puerto, backend.base_url y frontend.base_url serán http://IP_EC2:8000. La estructura aws.tables está anidada; no usar la plantilla inventada en respuestas anteriores.

Completar cost_projection.yaml partiendo del template con importes verificados, no null. Validar:

```bash
python -m scripts.check_cost cost_projection.yaml
pytest
```

Revisar report.md y report.json: no basta con que el proceso termine. Los casos omitidos, no verificados o fallidos no prueban cumplimiento. No modificar thresholds.yaml, pricing.yaml, tests/, harness/, generador ni oráculo para obtener un aprobado. El docente usa su propia copia.

## 8. Entregar a Salvatore y cerrar

- URLs finales y ventana de evaluación; actualizar si cambia IP.
- Inventario y recursos permitidos; costos y supuestos reales.
- IDs y horarios EMR; estado COMPLETED del paso y clúster terminado.
- Tablas Glue, particiones, métricas Athena y bytes escaneados.
- Reporte completo, commit de código y registro de cambios.
- Confirmación de que ambos pueden explicar y modificar API, transacciones, C1–C5 y agregaciones.
- Detener recursos fuera de la ventana acordada, pero mantener el sistema accesible cuando evalúe el docente.

No hay promesa de aprobación: faltan pruebas Spark y AWS, integración con el primer parcial y evaluación real de latencia, permisos y costos.
