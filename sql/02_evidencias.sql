-- Ejecutar antes y después de las pruebas. No modifica información.
select * from agentlab.products order by id;
select id, product_id, quantity, confirmation_id, created_at
 from agentlab.reservations order by created_at desc;
select tool_name, status, duration_ms, result, created_at
 from agentlab.tool_executions order by id desc limit 30;
select id, product_id, quantity, status, expires_at
 from agentlab.confirmations order by expires_at desc;
-- Detectar reservas duplicadas por confirmación. Resultado esperado: cero filas.
select confirmation_id, count(*) from agentlab.reservations
 group by confirmation_id having count(*) > 1;
