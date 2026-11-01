"""Subproceso privado MCP. No abrir un puerto adicional ni imprimir en stdout."""
from mcp.server.fastmcp import FastMCP
from .config import setting
from . import service
mcp = FastMCP('Inventario docente')

@mcp.tool()
async def buscar_producto(texto: str) -> dict:
    """Busca productos del catálogo por nombre o código."""
    return await service.search_product(texto)

@mcp.tool()
async def consultar_stock(producto_id: str) -> dict:
    """Consulta el nombre y stock actual de un código de producto."""
    return await service.stock(producto_id)

@mcp.tool()
async def registrar_reserva(confirmacion_id: str) -> dict:
    """Ejecuta una confirmación previamente aprobada en el backend."""
    return await service.reserve(confirmacion_id, setting('MCP_ACTOR_ID'))

@mcp.tool()
async def consultar_reserva(reserva_id: str) -> dict:
    """Consulta una reserva perteneciente al usuario autenticado."""
    return await service.get_reservation(reserva_id, setting('MCP_ACTOR_ID'))

if __name__ == '__main__':
    mcp.run(transport='stdio')
