# Guía de práctica
## Agente con LangGraph, MCP y Supabase PostgreSQL

**Caso de referencia:** inventario y reservas con confirmación humana.
**Dirigido a:** docente y equipos de estudiantes con fundamentos de programación web y SQL.
**Modalidad:** desarrollo con código, sin n8n, sin Docker y sin suscripción a una plataforma de flujos.
**Duración sugerida:** dos sesiones de tres horas y trabajo autónomo para adaptar el proyecto.
**Material incluido:** código Python, chat web, SQL, pruebas y esta guía.

Al terminar tendrás un chat que consulta productos mediante MCP, propone una reserva, se detiene para pedir aprobación y registra la operación en PostgreSQL. La misma conversación puede recuperarse después de reiniciar el backend.

El inventario es un ejemplo para aprender. En la entrega final cada grupo integra el agente a su propio producto: biblioteca, citas, ventas, soporte u otro sistema.

**Dos etapas de ejecución:** primero se comprueba la infraestructura con un planificador de demostración. Después se conecta un modelo de IA real. El modo demo es un simulador determinista y no constituye por sí solo la entrega de inteligencia artificial.

**Archivos principales:** `GUIA_PRACTICA.md`, `README.md`, `.env.example`, `app/`, `sql/`, `tests/` y `requirements-lock.txt`.

**Fecha de preparación:** 1 de noviembre de 2026.

---PAGE---
# 1. Objetivos y criterios de logro

Al completar la práctica, cada participante podrá:

1. Explicar percepción, decisión, acción y observación en un agente.
2. Ejecutar un grafo con LangGraph y conservar su estado en PostgreSQL.
3. Publicar y consumir herramientas por MCP, con un transporte local real.
4. Implementar un punto de control humano con `interrupt()` y `Command(resume=...)`.
5. Proteger las operaciones con identidad verificada, transacciones e idempotencia.
6. Documentar una instalación que otra persona pueda reproducir.

**Criterio verificable:** antes de confirmar no existe una reserva. Después de confirmar aparece una sola reserva y disminuye el stock. Cancelar no modifica existencias. Una cuenta no puede acceder a conversaciones o reservas ajenas.

**Resultado esperado del ejemplo:** con un stock inicial de 12 teclados, una reserva confirmada de dos deja 10 disponibles. Si ya hiciste pruebas, toma como referencia el stock actual y calcula su diferencia. No reinicies datos de otros grupos.

La calidad se evalúa por la ejecución y sus evidencias, además de la respuesta del chat. Mostrar solamente una conversación redactada por un modelo no demuestra una integración funcional.

---PAGE---
# 2. Arquitectura y responsabilidades

| Componente | Tecnología | Responsabilidad |
|---|---|---|
| Canal | HTML y JavaScript | Mensajes, acceso y botones de confirmación |
| API del agente | FastAPI | Validar identidad y propiedad de conversaciones |
| Orquestación | LangGraph | Planificar, usar herramientas, pausar y reanudar |
| Adaptador de herramientas | MCP Python SDK 1.x | Intercambiar llamadas mediante stdio |
| Servicio de negocio | Python y Psycopg | Consultar productos y registrar reservas |
| Persistencia | Supabase PostgreSQL | Datos, auditoría y checkpoints |
| Modelo | Adaptador ChatOpenAI | Interpretar lenguaje y seleccionar herramientas |

El navegador se comunica con FastAPI por HTTP. LangGraph decide el siguiente paso. El cliente MCP inicia un subproceso Python privado y habla con su servidor mediante entrada y salida estándar. El servidor utiliza el servicio de negocio para acceder a PostgreSQL.

**MCP por stdio es MCP real.** No requiere una URL pública ni otro puerto. Elegimos este transporte para una práctica local reproducible. Como simplificación didáctica se inicia un proceso por llamada, lo cual añade latencia. Un despliegue mayor puede mantener conexiones o utilizar Streamable HTTP con autenticación.

La práctica base no incluye webhooks. Un webhook notificaría un evento a otro sistema y puede añadirse como ampliación. La API, MCP y el webhook cumplen responsabilidades distintas.

---PAGE---
# 3. Flujo del agente y control humano

La ejecución sigue estas rutas:

1. El usuario solicita una consulta o una reserva.
2. El nodo `planner` produce una respuesta o una llamada de herramienta.
3. El nodo `tools` consulta MCP. Si recibe una propuesta válida, crea una confirmación pendiente.
4. El nodo `approval` se detiene mediante `interrupt()`.
5. El usuario pulsa Confirmar o Cancelar en la interfaz.
6. FastAPI comprueba la identidad, la conversación y el identificador de la operación.
7. LangGraph reanuda mediante `Command`. Si la aprobación sigue vigente, el nodo `execute` llama a MCP para reservar.
8. El nodo `finish` comunica el resultado real y termina.

**La escritura no depende de una frase del prompt.** El modelo dispone de `proponer_reserva`, pero no tiene acceso directo a la herramienta de escritura `registrar_reserva`. El backend ejecuta esta última únicamente después del control de aprobación. El servidor comprueba nuevamente la confirmación.

La propuesta incluye producto, cantidad, usuario y vencimiento de diez minutos. Una nueva propuesta requiere otra confirmación. El identificador evita que una respuesta vieja autorice una operación diferente.

Los efectos de escritura se ubican después de `interrupt()`. LangGraph vuelve a ejecutar el nodo interrumpido al reanudar, por lo que los efectos previos podrían repetirse si se colocan allí.

---PAGE---
# 4. Requisitos y preparación

Instala Python 3.12 y un editor como Visual Studio Code. Necesitas un navegador, conexión a Internet y acceso a un proyecto de Supabase. Para la etapa real necesitas una clave de API y un modelo que admita llamadas de herramientas.

**No necesitas instalar PostgreSQL en tu computadora.** La base de datos se alojará en Supabase. Python y el backend sí se ejecutarán localmente.

En Windows abre PowerShell y verifica:

```powershell
py -3.12 --version
```

Si el comando no existe, instala Python desde su distribución oficial y vuelve a abrir la terminal. En la instalación de Windows habilita el acceso desde la línea de comandos.

Descomprime el paquete en una carpeta de trabajo, por ejemplo `C:\clases\practica_agentes`. Abre esa carpeta en el editor. Debes ver directamente `requirements-lock.txt`, `check_db.py` y la carpeta `app`.

**Organización recomendada:** cada equipo crea un proyecto de Supabase para sus pruebas y mantiene su propia copia del repositorio. No compartan contraseñas del administrador ni utilicen datos reales de estudiantes para el ejemplo.

**Punto de control 1:** Python responde con su versión y puedes localizar los archivos del proyecto.

---PAGE---
# 5. Crear y preparar Supabase

1. Ingresa a Supabase con tu cuenta y crea un proyecto para la práctica.
2. Elige una contraseña de base de datos y guárdala de forma privada.
3. Espera a que la base de datos esté disponible.
4. Abre **SQL Editor** y crea una consulta nueva.
5. Copia TODO el contenido de `sql/01_schema.sql`, ejecútalo y verifica que no existan errores.
6. Ejecuta la siguiente consulta:

```sql
select id, name, stock
from agentlab.products
order by id;
```

| Código | Producto | Stock inicial ficticio |
|---|---|---|
| CAM-01 | Cámara web | 3 |
| MOU-01 | Mouse óptico | 8 |
| TEC-01 | Teclado USB | 12 |

El script crea el esquema privado `agentlab`. No lo agregues a los esquemas expuestos en la Data API. Habilita RLS sin políticas para las tablas del ejemplo y retira accesos de `anon` y `authenticated` a ese esquema.

El backend se conecta por PostgreSQL con una credencial de servidor. Esa conexión puede eludir RLS por su rol, de modo que el código debe validar siempre al propietario. RLS no sustituye esas verificaciones en esta arquitectura.

El script no borra datos y no repone stock si vuelves a ejecutarlo.

**Punto de control 2:** la consulta devuelve los tres productos.

---PAGE---
# 6. Obtener la conexión PostgreSQL

En el panel de Supabase abre **Connect** y selecciona **Session pooler**. Copia la URI PostgreSQL exacta de tu proyecto. Se utiliza el pooler de sesión para mantener el esquema de conexión del checkpointer. El puerto habitual de esta opción es 5432: confirma el valor que muestra tu panel.

Ejemplo ilustrativo, no una credencial válida:

```text
postgresql://postgres.PROJECT_REF:CONTRASENA@HOST:5432/postgres?sslmode=require
```

Sustituye la contraseña en la cadena copiada. No inventes el host ni la región. La contraseña de PostgreSQL es diferente de una clave publicable o una clave de la Data API.

Si la contraseña tiene caracteres reservados como `@`, `:`, `/`, `#` o `%`, codifícala para usarla en una URI. Puedes hacerlo localmente, sin mostrarla en pantalla:

```powershell
py -3.12 encode_password.py
```

Mantén `sslmode=require`. Para un despliegue real verifica también el certificado según la documentación de Supabase.

**No uses Transaction pooler como sustitución directa en esta práctica:** el código fija `search_path` por sesión. Aunque desactivamos prepared statements, ese modo de agrupación necesita revisar la gestión de esquema y conexión.

---PAGE---
# 7. Crear el entorno Python en Windows

Abre PowerShell en la carpeta raíz del proyecto y ejecuta:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
```

Estos comandos usan el ejecutable del entorno directamente. No necesitas activar scripts de PowerShell ni cambiar la política de ejecución.

`requirements-lock.txt` fija las versiones del entorno de referencia. Incluye también dependencias de pruebas. `requirements.txt` contiene rangos para actualizar deliberadamente y `requirements-dev.txt` incorpora herramientas de desarrollo. No actualices paquetes durante la primera ejecución del laboratorio.

La práctica utiliza **MCP SDK 1.x**, fijado en el paquete para que coincidan los imports de `FastMCP` y `ClientSession`. No mezcles este código con ejemplos del SDK 2.x sin realizar una migración consciente.

En Linux o macOS:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
```

**Punto de control 3:** la instalación termina sin errores y el entorno contiene LangGraph, MCP, FastAPI y Psycopg.

---PAGE---
# 8. Configurar el archivo .env

Copia el ejemplo desde PowerShell:

```powershell
Copy-Item .env.example .env
```

Edita `.env` y configura primero:

```text
DATABASE_URL=URI_REAL_DE_TU_PROYECTO
AUTH_MODE=demo
MODEL_MODE=demo
DEMO_TOKEN=UN_TOKEN_ALEATORIO_DE_AL_MENOS_24_CARACTERES
DEMO_USER_ID=11111111-1111-4111-8111-111111111111
```

Genera un token local:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(32))"
```

Pega el resultado como `DEMO_TOKEN`. No dejes el texto de ejemplo. Este token identifica una sola cuenta de práctica local y no debe compartirse como autenticación de una aplicación publicada.

Mantén el identificador de demostración estable para recuperar tus conversaciones. En esta fase no necesitas rellenar una clave del modelo. Las variables de Supabase Auth se configuran más adelante.

`.env` está excluido mediante `.gitignore`. Antes de compartir el ZIP o un repositorio, revisa que no incluya ese archivo. El paquete original solo incluye `.env.example`.

**Punto de control 4:** la URI real está en `.env` y el token ya fue reemplazado.

---PAGE---
# 9. Probar PostgreSQL y MCP por separado

Primero verifica la conexión y los datos:

```powershell
.\.venv\Scripts\python.exe check_db.py
```

Debe aparecer `Conexión PostgreSQL correcta` y el listado de productos. Si falla, corrige la URI, el estado del proyecto o el script SQL antes de continuar.

Después verifica el protocolo y las herramientas:

```powershell
.\.venv\Scripts\python.exe check_mcp.py
```

La salida debe incluir las cuatro herramientas:

```text
buscar_producto
consultar_stock
registrar_reserva
consultar_reserva
```

También debe aparecer el producto `TEC-01` con su stock actual. El cliente descubre las herramientas mediante `list_tools()` y ejecuta `call_tool()`. Eso comprueba una comunicación MCP real, sin modelo de IA.

El servidor se inicia automáticamente como subproceso. No necesitas ejecutar `mcp_server.py` en otra terminal. En el transporte stdio no añadas instrucciones `print()` al servidor para depuración: utiliza logs enviados a stderr.

**Punto de control 5:** ambos comandos funcionan. Guarda una captura sin mostrar contraseñas ni el contenido de `.env`.

---PAGE---
# 10. Iniciar el backend y abrir el chat

Desde la carpeta raíz del proyecto ejecuta:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Mantén abierta esa terminal. No uses múltiples workers en esta versión didáctica: el servidor serializa ejecuciones con un bloqueo de proceso.

Abre en el navegador:

```text
http://127.0.0.1:8000
```

Debes ver el chat y el indicador de **modo demostración**. Pega tu `DEMO_TOKEN` y pulsa **Conectar**. Se crea una conversación con UUID.

Abre también `http://127.0.0.1:8000/health`. Una respuesta con `ok: true` confirma que el proceso puede consultar PostgreSQL. La documentación interactiva de la API está en `/docs`.

En el inicio, `AsyncPostgresSaver.setup()` crea sus tablas en `agentlab`. Además de las tablas del negocio, verás `checkpoints`, `checkpoint_blobs`, `checkpoint_writes` y `checkpoint_migrations`.

**Punto de control 6:** se muestra la conversación y el indicador de conexión lista. Si no inicia, lee el primer error de la terminal, no solo el último mensaje.

---PAGE---
# 11. Primera ejecución sin consumir IA

El simulador admite instrucciones específicas. Úsalas exactamente en la primera comprobación:

```text
buscar teclado
stock TEC-01
reserva 2 TEC-01
```

**Consulta:** ejecuta `stock TEC-01` y anota la cantidad disponible.

**Reserva pendiente:** escribe `reserva 2 TEC-01`. Se ejecutan consultas y aparece una propuesta con producto, cantidad y vigencia. Todavía no se creó la reserva.

**Comprobación previa:** ejecuta en SQL Editor:

```sql
select * from agentlab.reservations
order by created_at desc;
```

**Confirmación:** pulsa **Confirmar reserva**. Debe mostrarse un UUID generado por la aplicación. Consulta otra vez el stock y verifica la reducción de dos unidades.

**Cancelación:** crea una propuesta nueva y pulsa **Cancelar**. Comprueba que el stock permanece igual.

El simulador responde con JSON a consultas. Es intencional: permite verificar resultados sin atribuirlos a un modelo. Su analizador no interpreta todas las frases de español. Las expresiones libres se prueban en la etapa real.

**Punto de control 7:** confirmar cambia los datos y cancelar no los cambia.

---PAGE---
# 12. Activar un modelo de IA real

Detén el backend con `Ctrl+C`. En `.env` cambia:

```text
MODEL_MODE=real
LLM_API_KEY=TU_CLAVE_PRIVADA
LLM_MODEL=IDENTIFICADOR_EXACTO_DEL_MODELO
LLM_BASE_URL=
```

El adaptador es `ChatOpenAI`. Con `LLM_BASE_URL` vacío utiliza su endpoint predeterminado. También puedes indicar un proveedor compatible con ese formato, siempre que admita tool calling y los parámetros utilizados. No todos los proveedores son intercambiables sin ajustes.

Selecciona el identificador disponible en tu proveedor. No confundas una suscripción al chat de un proveedor con acceso y saldo de su API. La clave se configura en el servidor y nunca se entrega a los estudiantes dentro del código compartido.

Reinicia el backend y abre una conversación nueva. Debe verse el indicador de modo IA. Prueba:

```text
¿Tienen teclados disponibles?
Quiero reservar dos teclados USB.
```

El modelo debe consultar las herramientas y proponer la operación. La reserva sigue requiriendo los botones. Después de reservar, pide que consulte el código de reserva recibido.

Si el proveedor rechaza `parallel_tool_calls`, revisa su compatibilidad antes de retirar ese parámetro. El flujo de referencia solicita una herramienta por respuesta.

**Punto de control 8:** la conversación libre produce llamadas reales y su resultado coincide con PostgreSQL.

---PAGE---
# 13. Identidad con Supabase Auth

La demostración local usa un usuario fijo. Para trabajar con cuentas separadas, utiliza Supabase Auth.

1. En el proyecto de Supabase habilita el proveedor de correo y contraseña.
2. Crea dos usuarios de prueba desde la sección de administración de usuarios. Comprueba que sus correos estén confirmados antes de iniciar sesión.
3. Obtén la URL del proyecto y su clave **publicable**. La clave publicable no es la contraseña PostgreSQL ni una clave privada de servidor.
4. Configura `.env`:

```text
AUTH_MODE=supabase
SUPABASE_URL=https://TU_PROYECTO.supabase.co
SUPABASE_PUBLISHABLE_KEY=TU_CLAVE_PUBLICABLE
```

Reinicia el backend. El chat mostrará correo y contraseña. FastAPI solicita una sesión a Supabase y conserva el token únicamente en memoria del navegador. Cada petición verifica al usuario con `/auth/v1/user`.

El token puede vencer. Vuelve a conectar si aparece un error 401. Para simplificar, esta práctica no implementa renovación automática ni registro de cuentas desde el chat.

Una cuenta solo puede acceder a sus conversaciones y reservas. Las credenciales del administrador de la base permanecen en el backend. No se utiliza una clave `service_role` en el frontend.

**Punto de control 9:** dos usuarios obtienen conversaciones distintas y no acceden a datos del otro.

---PAGE---
# 14. Comprender los archivos del proyecto

| Archivo | Qué debes revisar |
|---|---|
| `app/main.py` | Rutas HTTP, autorización, checkpoints y bloqueo de ejecución |
| `app/agent.py` | Estado, instrucciones, herramientas del modelo y nodos |
| `app/mcp_client.py` | Inicio del subproceso, llamada MCP y auditoría |
| `app/mcp_server.py` | Cuatro herramientas expuestas mediante MCP |
| `app/service.py` | Consultas SQL y transacción de reserva |
| `app/auth.py` | Identidad demo o verificación con Supabase |
| `app/db.py` | Conexión asíncrona a PostgreSQL |
| `app/index.html` | Chat y botones de confirmación |
| `sql/01_schema.sql` | Tablas, restricciones y datos iniciales |
| `sql/02_evidencias.sql` | Consultas para demostrar resultados |
| `tests/` | Pruebas del planificador y del flujo |

El catálogo MCP tiene cuatro herramientas. El catálogo del modelo utiliza tres de consulta y una operación de aplicación llamada `proponer_reserva`. Esta diferencia es deliberada: la herramienta MCP de escritura se conserva detrás de la aprobación.

Los esquemas del modelo están declarados de manera explícita en `SCHEMAS`. `check_mcp.py` demuestra el descubrimiento MCP. Como ampliación puedes obtener los contratos del servidor automáticamente, conservando una lista de herramientas permitidas.

**Ejercicio:** identifica en el código la línea donde la reserva se propone, donde el grafo se pausa y donde se ejecuta la escritura.

---PAGE---
# 15. Transacción e idempotencia

La herramienta `registrar_reserva` recibe una confirmación, no una cantidad elegida nuevamente por el modelo. El servicio lee producto y cantidad desde la propuesta aprobada.

La operación ocurre en una transacción:

1. Bloquea la confirmación con `SELECT ... FOR UPDATE` y verifica el usuario.
2. Si ya existe una reserva para esa confirmación, devuelve la misma reserva.
3. Valida el estado aprobado y el vencimiento.
4. Descuenta stock solo si aún hay unidades suficientes.
5. Inserta la reserva y marca la confirmación como utilizada.
6. Confirma todos los cambios juntos.

Fragmento central:

```sql
update agentlab.products
set stock = stock - %s
where id = %s and stock >= %s
returning stock;
```

Los valores se envían mediante parámetros de Psycopg. No se concatenan entradas del usuario dentro de SQL.

La restricción `UNIQUE(confirmation_id)` y la comprobación transaccional evitan crear dos reservas para una misma aprobación. Dos usuarios pueden consultar el mismo stock antes de reservar, pero la actualización condicional decide quién obtiene realmente las unidades.

**No se garantiza entrega exactamente una vez de extremo a extremo.** Se protege el efecto de reserva ante reintentos de la misma confirmación. Ante una caída durante el flujo, revisa el estado persistido y las reservas antes de iniciar otra operación.

---PAGE---
# 16. Memoria, reinicio y recuperación

LangGraph usa `thread_id` como identificador de conversación. El checkpointer conserva el estado en PostgreSQL, incluidos mensajes y una interrupción pendiente.

**Prueba de recuperación:**

1. Crea una propuesta y no la confirmes.
2. Copia el UUID de la conversación que muestra el chat.
3. Detén el backend con `Ctrl+C`.
4. Inícialo de nuevo con la misma base de datos y configuración.
5. Recarga el navegador en la misma pestaña y vuelve a conectar.
6. La aplicación recuperará el identificador guardado en `sessionStorage` y consultará el estado.
7. Confirma dentro de los diez minutos de vigencia. Si venció, crea una propuesta nueva.

La interfaz recupera el último resultado y la operación pendiente, no dibuja de nuevo todo el historial. Los mensajes y las trazas continúan en la base de datos.

**Distinción:** un checkpoint persistido sigue siendo memoria del hilo. No implica automáticamente una memoria semántica entre conversaciones. En esta práctica, las reservas son datos de negocio consultables y el historial es persistencia del sistema.

**Ampliación de memoria entre conversaciones:** crea una tabla de preferencias por usuario y define qué se guarda con autorización. Lee esa preferencia al iniciar un hilo nuevo. Documenta retención y eliminación. No conviertas toda conversación en una preferencia permanente.

---PAGE---
# 17. Pruebas funcionales y evidencias

| Caso | Procedimiento | Evidencia esperada |
|---|---|---|
| Consulta | Pedir stock existente | Coincide con SQL |
| Propuesta | Solicitar dos unidades | No hay reserva antes de aprobar |
| Confirmación | Pulsar Confirmar | Una reserva y descuento correcto |
| Cancelación | Pulsar Cancelar | Stock sin cambio |
| Cantidad inválida | Intentar cero o negativo | No se registra |
| Sin stock | Pedir más unidades | Error o aclaración, sin descuento |
| Vencimiento | Esperar más de diez minutos | No se ejecuta la propuesta |
| Reintento | Reenviar confirmación terminada | No aparece una segunda reserva |
| Propiedad | Usar otro usuario y UUID ajeno | Respuesta 404 o no encontrado |
| Reinicio | Recuperar conversación pendiente | Estado conservado |

Para cada prueba anota: fecha, estado inicial, entrada, herramientas, resultado del chat, resultado SQL y conclusión. Usa `sql/02_evidencias.sql`.

En modo demo utiliza el formato de comandos indicado. Para pruebas de lenguaje natural, errores del modelo y ambigüedad, activa el modo real.

Captura las herramientas y las tablas sin exponer credenciales ni mensajes privados. La demostración de un error controlado también cuenta como evidencia de calidad.

---PAGE---
# 18. Pruebas automatizadas

Ejecuta las pruebas locales:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Incluyen planificación demo, rechazo de stock insuficiente y comprobación de que el modelo no dispone de la herramienta de escritura. El grafo se prueba con dobles de la base de datos y de MCP para comprobar pausa, aprobación y cancelación.

Las pruebas con PostgreSQL real se omiten por defecto. Para ejecutarlas, configura una **base de pruebas independiente**, aplica `01_schema.sql` y ejecuta:

```powershell
$env:RUN_DB_TESTS="1"
$env:MODEL_MODE="demo"
.\.venv\Scripts\python.exe -m pytest tests/test_integration.py -q
Remove-Item Env:RUN_DB_TESTS
Remove-Item Env:MODEL_MODE
```

La prueba de integración crea productos y conversaciones propios con UUID, utiliza MCP y verifica propiedad, reintentos, cancelación, recuperación y dos reservas que compiten por una unidad. Intenta limpiar los datos que creó. No la ejecutes contra datos de producción.

**Validación realizada durante la preparación:** seis pruebas locales aprobadas, incluido descubrimiento MCP real por stdio. La prueba de integración PostgreSQL se dejó disponible pero no se ejecutó contra una cuenta de Supabase. Tampoco se consumió una API de IA ni se probaron credenciales reales de Supabase Auth. Estas verificaciones deben completarse con tu configuración.

El modo real puede variar por proveedor. Guarda las versiones y los resultados que realmente funcionaron en tu entorno.

---PAGE---
# 19. Errores frecuentes y solución

| Mensaje o síntoma | Revisión concreta |
|---|---|
| Python no existe | Verifica `py -3.12 --version` e instalación |
| No encuentra `app` | Ejecuta desde la raíz del proyecto |
| `ModuleNotFoundError` | Usa el Python de `.venv` e instala el lock |
| `password authentication failed` | URI, contraseña DB y caracteres codificados |
| Host no resuelve | Copia host real desde Connect y revisa Internet |
| IPv6 no disponible | Usa Session pooler accesible en tu red |
| `schema agentlab does not exist` | Ejecuta `01_schema.sql` en ese proyecto |
| Permiso denegado al iniciar | Revisa usuario PostgreSQL y permisos de esquema |
| Puerto 8000 ocupado | Usa `--port 8001` y abre esa dirección |
| Error 401 | Token demo incorrecto o sesión de Auth vencida |
| Error 409 | Resuelve la confirmación pendiente o revisa el identificador |
| Error 503 | Revisa terminal, conexión DB, MCP y modelo |
| Modelo no encontrado | Usa el identificador exacto de tu proveedor |
| Saldo o cuota de IA | Revisa facturación de API o utiliza modo demo |
| MCP se cierra | Prueba `check_mcp.py` y verifica la versión `<2` |

Si una reserva falló, consulta primero las tablas antes de repetir. No cambies permisos para permitir acceso anónimo como solución a errores de conexión. La práctica utiliza un backend autenticado.

Para pedir ayuda, comparte el texto del error y el comando ejecutado, ocultando claves, URI con contraseña y tokens.

---PAGE---
# 20. Adaptación al producto de cada equipo

El grupo conserva su dominio y su backend existente. Sustituye las funciones de inventario por operaciones reales de su aplicación.

| Proyecto | Consultas | Acción con aprobación |
|---|---|---|
| Biblioteca | Buscar libro y disponibilidad | Solicitar préstamo |
| Citas | Servicios y horarios | Reservar cita |
| Ventas | Productos y condiciones | Registrar pedido |
| Soporte | Incidencias y estado | Crear ticket |
| Gestión académica | Requisitos y trámites | Registrar una solicitud |

**Secuencia de adaptación:** define el caso, identifica sus permisos, diseña contratos, prueba operaciones sin IA y luego intégralas al grafo. Conserva una clave idempotente y una confirmación ligada a los parámetros exactos.

Si el producto ya tiene backend en NestJS u otro lenguaje, modifica `service.py` para llamar a su API mediante HTTP. En ese caso, el backend original mantiene la lógica de negocio y PostgreSQL. No dupliques reglas en dos lugares sin necesidad.

Si el proyecto utiliza otro frontend, integra las rutas de FastAPI en su chat o adapta el canal. El HTML incluido es una referencia funcional para empezar.

**Requisitos mínimos del grupo:** tres herramientas útiles, al menos una acción, control humano, persistencia, identidad verificada y evidencia del efecto en su aplicación. La entrega final incluye modo IA real.

---PAGE---
# 21. Organización de las sesiones

**Antes de la clase:** el docente instala dependencias, ejecuta SQL, prueba conexión, verifica su proveedor de IA y realiza una reserva completa. Entrega a los estudiantes el ZIP original, sin `.env`.

**Sesión 1, 180 minutos:**

1. Arquitectura y contratos: 25 minutos.
2. Supabase y entorno Python: 45 minutos.
3. Pruebas de PostgreSQL y MCP: 30 minutos.
4. Chat y ejecución demo: 45 minutos.
5. Confirmación, cancelación y evidencias: 35 minutos.

**Sesión 2, 180 minutos:**

1. Conexión de IA real: 35 minutos.
2. Supabase Auth y aislamiento de usuarios: 35 minutos.
3. Pruebas, reinicio y análisis de fallos: 45 minutos.
4. Adaptación al dominio de cada grupo: 45 minutos.
5. Revisión de documentación y acuerdos de entrega: 20 minutos.

Los tiempos son sugerencias y presuponen fundamentos de Python y SQL. Si no los tienen, añade una sesión de preparación. La adaptación completa al producto integrador puede requerir trabajo autónomo.

Distribuye responsabilidades entre integración, datos, interfaz y pruebas, pero exige que todos puedan explicar el flujo. Durante la exposición, cada estudiante debe identificar una decisión del agente y un control que el modelo no puede omitir.

---PAGE---
# 22. Entrega final y rúbrica

Cada grupo entrega un repositorio o ZIP con código, instalación reproducible, `.env.example`, SQL o migraciones y pruebas. Excluye `.env`, entornos virtuales y datos privados.

**Informe sugerido:** problema, objetivo, arquitectura, contratos MCP, flujo LangGraph, identidad, memoria, control humano, pruebas, resultados, limitaciones y conclusiones. Incluye versiones, instrucciones de ejecución y un video corto como evidencia complementaria.

| Criterio | Puntaje |
|---|---|
| Agente con modelo real y herramientas funcionales | 25 |
| Integración MCP verificable | 20 |
| PostgreSQL y reglas de negocio | 15 |
| Confirmación, identidad e idempotencia | 20 |
| Pruebas y evidencia de resultados | 10 |
| Documentación reproducible y exposición | 10 |
| Total | 100 |

**Demostración de cinco minutos:** iniciar sesión, consultar, proponer, mostrar que no existe escritura previa, confirmar, verificar el resultado SQL, ejecutar una cancelación y explicar un error controlado.

Para evaluar reproducibilidad, otro grupo debe instalar el proyecto con sus propias variables y ejecutar una consulta siguiendo el README. El acceso a una cuenta personal del autor no es un requisito aceptable de la entrega.

El modo demo facilita diagnóstico y exposición sin consumo de IA, pero no reemplaza la prueba del modelo real en la evaluación final.

---PAGE---
# 23. Alcance, límites y ampliaciones

Esta implementación está pensada para aprendizaje local. Escucha únicamente en `127.0.0.1` y usa un proceso. Para publicar un servicio añade HTTPS, gestión de secretos, límites de peticiones, revisión de CORS y un rol PostgreSQL de mínimo privilegio. El bloqueo local debe sustituirse por coordinación distribuida si ejecutas múltiples procesos.

La instalación utiliza una credencial administrativa de PostgreSQL para crear el esquema del checkpointer. En un despliegue, separa migraciones administrativas del rol de ejecución. No publiques este ejemplo cambiando solamente la dirección de escucha.

Los checkpoints no eliminan por sí solos el crecimiento del contexto ni implementan retención. Define limpieza, resúmenes y límites de conversación al ampliar el proyecto.

No se ha construido un editor visual ni un clon de n8n. El producto es una aplicación programada con un grafo explícito que cada equipo puede versionar, ejecutar y explicar.

**Ampliaciones opcionales:** memoria de preferencias entre conversaciones, herramientas obtenidas del catálogo MCP con lista permitida, notificaciones por webhook, eventos de ejecución en tiempo real, recuperación administrada de fallos y pruebas con distintos modelos.

Cualquier ampliación debe conservar la autorización de cada escritura. Un webhook o una llamada del modelo no equivale a la aprobación del usuario.

---PAGE---
# 24. Referencias y cierre de la práctica

Las instrucciones consultan fuentes oficiales. El código fija versiones para evitar mezclar interfaces de distintas generaciones del SDK.

- LangGraph, interrupciones y reanudación: https://docs.langchain.com/oss/python/langgraph/interrupts
- LangGraph, persistencia y alcance de memoria: https://docs.langchain.com/oss/python/langgraph/persistence
- MCP Python SDK, documentación 1.x: https://py.sdk.modelcontextprotocol.io/v1/
- Supabase, conexión PostgreSQL: https://supabase.com/docs/guides/database/connecting-to-postgres
- Supabase, autenticación: https://supabase.com/docs/guides/auth
- Psycopg, prepared statements: https://www.psycopg.org/psycopg3/docs/advanced/prepare.html
- FastAPI, documentación: https://fastapi.tiangolo.com/

**Preguntas para el informe:** ¿quién elige la herramienta?, ¿quién valida el permiso?, ¿qué guarda el checkpoint?, ¿por qué una consulta de stock no garantiza la reserva?, ¿cómo evita el sistema un duplicado?, ¿qué sucede si se reinicia antes de confirmar?

**Lista de cierre:** consulta correcta, reserva confirmada, cancelación sin cambios, reintento sin duplicados, acceso restringido por usuario, recuperación de estado, modelo real probado y documentación ejecutable por otra persona.

**Entrega docente:** comparte el PDF para la lectura y el ZIP para realizar la práctica. El Markdown de esta guía está dentro del paquete para que puedas modificar el contenido y adaptarlo a tu curso.
