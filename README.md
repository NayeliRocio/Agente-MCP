# Práctica: agente con LangGraph, MCP y Supabase

**Objetivo:** consultar productos y reservar con confirmación humana.

**Necesitas:** Python 3.12, el proyecto corregido entregado por el docente, una cuenta de Supabase y una clave de Groq. Este README acompaña al código; no lo reemplaza.

## 1. Instalar

Descomprime el proyecto corregido y abre PowerShell dentro de `practica_agentes`, donde está `run.py`.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
Copy-Item .env.examp
```

Si ya existe `.env`, conserva tu configuración y omite el último comando.

## 2. Preparar Supabase

1. Crea un proyecto y ejecuta `sql/01_schema.sql` en **SQL Editor**.
2. En **Connect > Session pooler**, copia la URI PostgreSQL y coloca la contraseña.
3. Pega esa URI en `DATABASE_URL` de `.env`. Mantén `sslmode=require`.

## 3. Configurar `.env`

Obtén una clave en https://console.groq.com/keys y completa:

```dotenv
DATABASE_URL=URI_POSTGRESQL_DE_TU_SUPABASE
AUTH_MODE=demo
DEMO_TOKEN=REEMPLAZAR_POR_TOKEN_ALEATORIO
DEMO_USER_ID=11111111-1111-4111-8111-111111111111
MODEL_MODE=real
LLM_API_KEY=TU_CLAVE_GROQ
LLM_MODEL=openai/gpt-oss-20b
LLM_BASE_URL=https://api.groq.com/openai/v1
```

Genera el token y pega el resultado en `DEMO_TOKEN`:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 4. Ejecutar

```powershell
.\.venv\Scripts\python.exe run.py
```

Abre **http://127.0.0.1:8000**, introduce tu `DEMO_TOKEN` y pulsa **Conectar**. Mantén la terminal abierta.

## 5. Probar

1. Escribe: **Busca un teclado y dime su stock**.
2. Escribe: **Reserva dos teclados USB**.
3. Pulsa **Confirmar reserva** en el recuadro. No escribas la confirmación como mensaje.
4. Consulta el stock: debe disminuir en dos unidades.
5. Propón otra reserva y pulsa **Cancelar**: el stock no debe cambiar.

## Si falla

- **Modo demo:** verifica `MODEL_MODE=real` y reinicia el servidor.
- **409:** confirma o cancela con los botones. Si el hilo quedó fallido, pulsa **Nueva conversación**.
- **MCP o base de datos:** ejecuta `check_db.py` y `check_mcp.py` con el Python de `.venv`.
- **ProactorEventLoop en Windows:** utiliza los archivos corregidos del docente, incluido `run.py`.
- **503 del proveedor:** espera o prueba otro modelo disponible en tu cuenta.

## Entrega

Código sin `.env`, una captura de consulta, una reserva confirmada, una cancelación y una explicación breve de la herramienta MCP utilizada.

**Alcance:** práctica local con un usuario demo por instalación. No compartas claves. Groq tiene cuotas de uso; cada equipo verifica las disponibles en su cuenta.

uedes desplegarlo gratis en Render como Web Service. Admite Python y FastAPI; tu base de datos puede continuar en Supabase. Render Docs

Para tu proyecto:
1. Sube el código a GitHub, sin .env ni .venv.
2. En Render selecciona New → Web Service y conecta el repositorio.
3. Elige el plan Free.
4. Configura:
Build Command:
pip install -r requirements-lock.txt

Start Command:
uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1

Render requiere escuchar en 0.0.0.0 y en el puerto asignado. En Render utiliza ese comando, no el run.py local. Render Docs
5. Agrega las variables de .env en Environment de Render.