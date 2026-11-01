# Validación del paquete

Preparado el 1 de noviembre de 2026 en Python 3.12.

## Ejecutado

- Instalación de las dependencias en un entorno virtual aislado.
- Compilación sintáctica de todos los módulos Python.
- Seis pruebas locales aprobadas con pytest.
- Comprobación de planificación de consulta y propuesta.
- Comprobación de rechazo de stock insuficiente en planificador demo.
- Comprobación de ausencia de escritura directa en herramientas del modelo.
- Ejecución real de LangGraph con pausa, reanudación y cancelación usando dobles de servicios.
- Inicio de un subproceso MCP real por stdio y descubrimiento de las cuatro herramientas.
- Validación sintáctica de los dos scripts SQL mediante un parser PostgreSQL.
- Comprobación sintáctica del JavaScript del chat.

## Pendiente con la configuración del participante

- La prueba de integración PostgreSQL está incluida y se omite por defecto.
- No se conectó a una cuenta de Supabase ni se ejecutaron las transacciones SQL en ese servicio.
- No se realizaron peticiones a un modelo de IA de pago ni se validó un proveedor concreto.
- No se verificó Supabase Auth con cuentas reales.
- No se abrió el chat en el navegador contra Supabase. Las pruebas visuales de negocio son parte de la guía.

La validación sintáctica no sustituye la ejecución de las migraciones ni las pruebas concurrentes.
Utiliza una base de pruebas para tests/test_integration.py y registra sus resultados antes de la clase.

## Alcance

El servidor funciona en un proceso local. La versión MCP se mantiene en 1.x.
El modo demo no representa IA y no basta para la entrega final del curso.
