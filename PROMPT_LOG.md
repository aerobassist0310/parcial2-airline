# Registro de uso de inteligencia artificial

Durante el proyecto se usaron asistentes de inteligencia artificial como apoyo en la planificación, la documentación, el código base y la resolución de problemas del despliegue. El equipo ejecutó o autorizó cada acción en AWS, revisó el código antes de usarlo y validó los resultados con el oráculo y el evaluador entregados por el docente. Las conversaciones completas se adjuntan al informe.

| Fecha | Herramienta | Uso | Verificación del equipo |
|---|---|---|---|
| 26 oct | Perplexity | Planificación del parcial: arquitectura, servicios y criterios de costo. | Revisión contra el enunciado y los contratos. |
| 26 oct | Perplexity | Borrador del informe de avance y diagrama de arquitectura. | Ajustes de contenido, formato y redacción. |
| 26 oct | Perplexity | Código base a partir de los contratos: API, frontend, trabajo PySpark y SQL. | Pruebas locales con SQLite antes del despliegue. |
| 27 oct | Perplexity | Guía de despliegue: EC2, bucket S3, perfil IAM y muestra de datos. | Ejecución en el Learner Lab y comprobación de cada paso. |
| 27–28 oct | Perplexity y Claude | Configuración del clúster EMR y diagnóstico de sus fallos a partir de los registros. | Nueva ejecución de la muestra, comparada fila a fila con oracle.py. |
| 28 oct | Claude | Tablas en Glue y Athena, conexión del endpoint y del panel, y migración a RDS PostgreSQL. | Comprobaciones de R2 y R4–R7 contra el oráculo. |
| 28 oct | Claude | Ejecución del evaluador y actualización del informe y del repositorio. | Evaluador del docente sin modificaciones: 70/70. |

## Criterios de uso

- El código generado se revisó y se probó antes de desplegarlo; las pruebas y los archivos del docente no se modificaron.
- Las credenciales y contraseñas no se guardaron en el código ni en el repositorio.
- Las decisiones finales (semilla, uso de RDS, proyección de costos) las tomó el equipo.
