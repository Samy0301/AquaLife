USE AquaLife;


-- Tipo = 'Especie' si existe en Especie; si no, 'Equipo'.
-- @busqueda filtra por nombre (vacio = todos). En la app: LIKE %s con '%texto%'.
SET @busqueda = '';
SELECT
    p.IDProd,
    p.Nombre,
    IF(e.IDProd IS NULL, 'Equipo', 'Especie') AS Tipo,
    p.Precio
FROM Producto p
LEFT JOIN Especie e ON e.IDProd = p.IDProd
WHERE p.Nombre LIKE CONCAT('%', @busqueda, '%')
ORDER BY p.IDProd
LIMIT 200;

-- Prueba
-- SET @idprod = 1;
-- SET @nuevo_precio = 400;
-- UPDATE Producto SET Precio = @nuevo_precio WHERE IDProd = @idprod;


SET @idprod = 1;
SELECT
    h.IDHist,
    h.IDProd,
    p.Nombre,
    h.PrecioAnterior,
    h.PrecioNuevo,
    h.PorcentajeCambio,
    h.FechaCambio,
    h.HoraCambio,
    h.Usuario
FROM Historial_Precios h
JOIN Producto p ON p.IDProd = h.IDProd
WHERE h.IDProd = @idprod
ORDER BY h.IDHist DESC;