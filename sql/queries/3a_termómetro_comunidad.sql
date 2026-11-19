USE AquaLife;

SELECT
    p.*,
    u.Nombre AS autor,            
    COUNT(r.IDU) AS total_reacciones
FROM Publicacion p
JOIN Usuario u ON u.IDU = p.IDU
LEFT JOIN Reaccionar r ON r.IDpub = p.IDpub
GROUP BY p.IDpub
ORDER BY total_reacciones DESC