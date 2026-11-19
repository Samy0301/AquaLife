USE AquaLife;

SELECT
    p.*,
    SUM(r.Tipo IN ('Me gusta', 'Me encanta', 'Me asombra','Me divierte')) AS reacciones_positivas,
    SUM(r.Tipo IN ('Me entristece', 'Me enoja'))    AS reacciones_negativas,
    COUNT(r.IDU) AS total_reacciones
FROM Publicacion p
JOIN Reaccionar r ON r.IDpub = p.IDpub
GROUP BY p.IDpub
HAVING reacciones_positivas > reacciones_negativas
ORDER BY reacciones_positivas DESC;