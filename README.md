# Laboratorio: LangGraph + MCP + Supabase PostgreSQL

Proyecto docente con chat web, consultas de inventario y reservas confirmadas.
Sin n8n. El servidor MCP usa stdio y lo inicia el backend automáticamente.

## Guía completa

Lee `GUIA_PRACTICA.md` en orden. Incluye Supabase, Windows, Linux/macOS,
modo demo, modo IA, autenticación real, pruebas, evaluación y adaptación.

## Inicio rápido (Windows PowerShell)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
Copy-Item .env.example .env
```

1. En Supabase SQL Editor ejecuta `sql/01_schema.sql`.
2. Copia la URI de **Session pooler** al archivo `.env`.
3. Genera el token demo y reemplaza el marcador de `.env`:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(32))"
.\.venv\Scripts\python.exe check_db.py
.\.venv\Scripts\python.exe check_mcp.py
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Abre http://127.0.0.1:8000, pega el token y pulsa Conectar.
Escribe `stock TEC-01` y `reserva 2 TEC-01`. Usa los botones para aprobar o cancelar.
El modo demo no consume ni representa un modelo de IA.

Para IA real: detén el proceso, configura `MODEL_MODE=real`, `LLM_API_KEY`
y `LLM_MODEL`, reinicia y abre una conversación nueva.
Para cuentas reales configura `AUTH_MODE=supabase` y sigue la guía.

## Linux y macOS

Usa `python3.12 -m venv .venv`, `.venv/bin/python` en lugar del ejecutable
Windows y `cp .env.example .env` para copiar el ejemplo.

## Verificación

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Las pruebas de integración requieren una base PostgreSQL de pruebas y
`RUN_DB_TESTS=1`. Consulta el capítulo 18 antes de habilitarlas.

## Modelo y versiones

El adaptador ChatOpenAI necesita un modelo con tool calling. El proveedor y
el identificador son configurables. La API de IA puede tener costo independiente.
MCP se fija a 1.x deliberadamente. No mezcles imports de 2.x con esta práctica.
El archivo lock reproduce el entorno de referencia Python 3.12.

## Alcance

Un proceso local. No publicar directamente. El bloqueo de ejecución vive en
ese proceso. El backend valida propietario y la base controla transacciones.
La credencial PostgreSQL de la práctica es de servidor y puede eludir RLS:
no debe aparecer en navegador ni repositorio.

`proponer_reserva` es una herramienta de aplicación para el modelo.
`registrar_reserva` es la herramienta MCP que solo ejecuta el nodo autorizado.
Los checkpoints persisten memoria por conversación, no preferencias entre hilos.

No se incluyen claves, cuentas ni una instancia Supabase preconfigurada.
Consulta `docs/VALIDACION.md` para el alcance exacto de las pruebas realizadas.
