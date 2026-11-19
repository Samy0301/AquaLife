USE AquaLife;

SELECT
    CONCAT(rango * 10 + 1, '-', rango * 10 + 10) AS rango_edad,
    COUNT(*) AS cantidad_usuarios,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM Usuario), 2) AS porcentaje
FROM (
    SELECT FLOOR((TIMESTAMPDIFF(YEAR, FechaDeNacimiento, CURDATE()) - 1) / 10) AS rango
    FROM Usuario
) AS t
GROUP BY rango
ORDER BY rango