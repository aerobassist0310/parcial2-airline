# Registro de apoyo de IA

Se usaron asistentes de inteligencia artificial durante todo el proyecto: para estructurar la documentación, generar una primera versión del código (API, frontend y trabajo PySpark) a partir de los contratos del docente, guiar el despliegue en AWS paso a paso y diagnosticar los fallos de EMR a partir de sus registros. El equipo ejecutó o autorizó cada acción en su cuenta de AWS y validó los resultados con el oráculo y el evaluador. Las conversaciones completas se entregan como anexos del informe.

## Entrada 1: planificación e informe de avance, 26 de octubre de 2026
- Solicitud: «Con lo que sabes de mi parcial. Necesito que me des los pasos y me ayudes con toda la parte de planificacion para lo que es el parcial 2».
- Material: plan, borrador del informe de avance, diagrama de arquitectura y tabla de servicios.
- Herramienta utilizada: Perplexity (conversación original).
- Revisión humana: Salvatore Victorino (ajustes de formato, contenido y redacción del informe).

## Entrada 2: paquete de implementación, 26 de octubre de 2026
- Solicitud: «Ahora, generame o pasame los otros archivos o codigo que necesite Camila para hacer la implementacion, que ella es la que va a trabajar con AWS».
- Material: base de API e interfaz; trabajo PySpark; SQL; scripts locales y guía de despliegue (docs/kit/).
- Herramienta utilizada: Perplexity (conversación original).
- Revisión humana: Salvatore Victorino durante el despliegue del 27 y 28 de octubre.
- Validación: consultar docs/kit/VALIDACION_LOCAL.md (pruebas locales, previas a AWS).

## Entrada 3: despliegue guiado en AWS, 27 de octubre de 2026
- Solicitud: «Camila no puede hacer su parte. Explicame a detalle cada paso desde abrir el learner lab a como se configura TODO».
- Material: guía paso a paso para EC2 (servicio systemd), bucket S3, perfil IAM de la instancia, muestra de datos y formulario de EMR.
- Herramienta utilizada: Perplexity (conversación original).
- Ejecución AWS: Salvatore Victorino, en su cuenta del Learner Lab.

## Entrada 4: lote EMR, Glue, Athena y RDS, 28 de octubre de 2026
- Solicitudes: «Usando el thread, me podrias ayudar a continuar?»; «Ahora dime como se crea lo de glue y athena como si yo supiera nada»; «Sí, usar 12345 y necesito crear RDS».
- Material: diagnóstico de los fallos de EMR a partir de los registros de S3 (modo cluster sin memoria para el ejecutor; paso de consola sin la ruta del script; clon sin terminación automática); paso Custom JAR en modo client; DDL de Glue/Athena; conexión del endpoint y del panel; migración de SQLite a RDS PostgreSQL; scripts/verificar_athena.py y scripts/prueba_concurrencia.py.
- Herramienta utilizada: Claude (Claude Code).
- Ejecución AWS: Salvatore Victorino, comando por comando, revisando cada salida.
- Validación: muestra comparada fila a fila con oracle.py; conjunto completo con 12/12 comprobaciones de R4–R7.

## Entrada 5: evaluador, informe y repositorio, 28 de octubre de 2026
- Solicitudes: «Sí, prepáralo» (evaluador en el equipo local); «Sí, actualízalo» (informe); «Sí, prepáralo» (repositorio).
- Material: config.yaml, cost_projection.yaml, entorno local del evaluador, informe final y este repositorio.
- Herramienta utilizada: Claude (Claude Code).
- Validación: evaluador del docente sin modificaciones, 70/70 (report.md).
