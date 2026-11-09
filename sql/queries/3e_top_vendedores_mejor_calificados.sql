USE AquaLife;

SELECT
    u.IDU,
    u.Nombre,
    u.Email,
    u.DireccionParticular,
    SUM(c.Cantidad)               AS TotalProductosVendidos,
    ROUND(AVG(c.Puntuacion), 2)   AS CalificacionPromedio
FROM Compra c
JOIN Usuario u ON u.IDU = c.IDUV
GROUP BY u.IDU, u.Nombre, u.Email, u.DireccionParticular
ORDER BY AVG(c.Puntuacion) DESC, SUM(c.Cantidad) DESC   
LIMIT 5;