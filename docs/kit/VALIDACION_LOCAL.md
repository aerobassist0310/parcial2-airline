# Validación del paquete

Fecha de preparación: 26 de octubre de 2026.

## Ejecutado
- Análisis de sintaxis de todos los archivos Python.
- Inicio real del servidor HTTP y acceso a páginas, archivos estáticos y /health.
- Vuelo duplicado: 409; reserva/vuelo inexistente: 404; reserva creada consultable por ID.
- Cuatro carreras HTTP de 50 clientes sobre SQLite local: capacidades 1, 7, 1, 7.
- Resultados: [{"capacity": 1, "201": 1, "409": 49}, {"capacity": 7, "201": 7, "409": 43}, {"capacity": 1, "201": 1, "409": 49}, {"capacity": 7, "201": 7, "409": 43}].
- En cada carrera, se verificó que el vuelo agotado no se ofreciera en búsqueda.
- CLI original con semilla de PRUEBA 123 y --rows 10000: produjo 1008 vuelos y 130411 reservas crudas (el generador aproxima volumen y usa un mínimo de vuelos). No representa al equipo.
- Renderizado local de SQL y JSON EMR con identificadores ficticios, sin solicitudes AWS. La plantilla sin completar es rechazada, como se espera.
- Verificación de cierre al finalizar y ante fallo en el JSON EMR.
- Sintaxis JavaScript con Node: comprobada.
- Archivos del docente copiados sin alterar; hashes en ORIGINALES_SHA256.json (raíz del repositorio).

## No ejecutado
- PySpark/Java ni comparación de sus Parquet (Spark no está instalado en este entorno).
- PostgreSQL/RDS y su concurrencia: el ensayo usó SQLite, no PostgreSQL.
- EMR, Athena, Glue, S3, IAM, VPC o despliegue en EC2.
- Playwright en navegador, latencia R1 en AWS, plazo R7 y reporte R1–R12 completo.
- Tarifas AWS actuales ni proyección económica final.

Estos controles NO permiten declarar que se aprobó el parcial. Repetir validación en AWS.
Reproducir la prueba local con `python -m scripts.smoke_local` desde la raíz del paquete.
