import asyncio
import selectors
import sys

from mcp.server.fastmcp import FastMCP

from .config import setting
from . import service


mcp = FastMCP("Inventario docente")


def ejecutar_en_windows(funcion, argumentos):
    return asyncio.run(
        funcion(*argumentos),
        loop_factory=lambda: asyncio.SelectorEventLoop(
            selectors.SelectSelector()
        ),
    )


async def ejecutar_db(funcion, *argumentos):
    if sys.platform == "win32":
        return await asyncio.to_thread(
            ejecutar_en_windows,
            funcion,
            argumentos,
        )

    return await funcion(*argumentos)


@mcp.tool()
async def buscar_producto(texto: str) -> dict:
    """Busca productos por nombre o código."""
    return await ejecutar_db(
        service.search_product, texto
    )


@mcp.tool()
async def consultar_stock(producto_id: str) -> dict:
    """Consulta el stock actual de un producto."""
    return await ejecutar_db(
        service.stock, producto_id
    )


@mcp.tool()
async def registrar_reserva(confirmacion_id: str) -> dict:
    """Ejecuta una confirmación previamente aprobada."""
    return await ejecutar_db(
        service.reserve,
        confirmacion_id,
        setting("MCP_ACTOR_ID"),
    )


@mcp.tool()
async def consultar_reserva(reserva_id: str) -> dict:
    """Consulta una reserva del usuario autenticado."""
    return await ejecutar_db(
        service.get_reservation,
        reserva_id,
        setting("MCP_ACTOR_ID"),
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")