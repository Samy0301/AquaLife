USE AquaLife;

SELECT u.IDU AS id_usuario,u.Nombre AS influencer,
    COALESCE(pubreac.reacciones,0) AS reacciones,COALESCE(pubreac.puntos_reacciones,0) AS puntos_reacciones,
    COALESCE(pubcom.comentarios,0) AS comentarios,COALESCE(pubcom.comentarios,0)*2 AS puntos_comentarios,
    COALESCE(pubreac.puntos_reacciones,0)+COALESCE(pubcom.comentarios,0)*2 AS puntaje_total
FROM Usuario u
LEFT JOIN (SELECT p.IDU,COUNT(*) AS reacciones,
    SUM(CASE r.Tipo
        WHEN 'Me gusta'   THEN 1
        WHEN 'Me encanta' THEN 2
        WHEN 'Me asombra' THEN 1.5
        ELSE 0
    END) AS puntos_reacciones
    FROM Publicacion p 
    JOIN Reaccionar r ON r.IDPub=p.IDPub 
    GROUP BY p.IDU) pubreac ON pubreac.IDU=u.IDU
LEFT JOIN (SELECT p.IDU,COUNT(*) AS comentarios FROM Publicacion p 
JOIN Comentar c ON c.IDPub=p.IDPub 
GROUP BY p.IDU) pubcom ON pubcom.IDU=u.IDU 
WHERE u.IDU IN (SELECT IDU FROM Publicacion)
ORDER BY puntaje_total DESC,u.IDU ASC
LIMIT 5;

SET @id_influencer=1031;

SELECT e.IDProd AS id_especie,e.NombreComun AS especie,
    COALESCE(G.n,0) AS gustar,
    COALESCE(C.n,0) AS contribuir,
    COALESCE(CO.n,0) AS comprar,
    COALESCE(G.n,0)+COALESCE(C.n,0)+COALESCE(CO.n,0) AS interacciones
FROM Especie e
LEFT JOIN (SELECT IDProd,COUNT(*) AS n FROM Gustar WHERE IDU=@id_influencer
    GROUP BY IDProd) G ON G.IDProd=e.IDProd
LEFT JOIN (SELECT IDProd,COUNT(*) AS n FROM Contribucion WHERE IDU=@id_influencer
    GROUP BY IDProd) C ON C.IDProd=e.IDProd
LEFT JOIN (SELECT IDProd,COUNT(*) AS n FROM Compra WHERE IDUC=@id_influencer
    GROUP BY IDProd) CO ON CO.IDProd=e.IDProd
WHERE COALESCE(G.n,0)+COALESCE(C.n,0)+COALESCE(CO.n,0) > 0
ORDER BY interacciones DESC, e.IDProd ASC
LIMIT 7;

SELECT fecha,tipo,id,ventas_antes,ventas_despues,
    CASE WHEN ventas_antes=0 AND ventas_despues>0 THEN 100
        WHEN ventas_antes=0 THEN 0
        ELSE ((ventas_despues-ventas_antes)/ ventas_antes)*100
    END AS incremento_porcentual
FROM (SELECT actividad.id_ref AS id,actividad.tipo AS tipo,actividad.fecha AS fecha,
    COALESCE(SUM(c.Fecha BETWEEN DATE_SUB(actividad.fecha,INTERVAL 14 DAY) AND DATE_SUB(actividad.fecha,INTERVAL 1 DAY)),0) AS ventas_antes,
    COALESCE(SUM(c.Fecha BETWEEN DATE_ADD(actividad.fecha,INTERVAL 1 DAY) AND DATE_ADD(actividad.fecha,INTERVAL 14 DAY)),0) AS ventas_despues
    FROM (SELECT p.IDPub AS id_ref, MIN(r.Fecha) AS fecha,'publicacion' AS tipo FROM Publicacion p 
    JOIN Reaccionar r ON r.IDPub=p.IDPub WHERE p.IDU=@id_influencer GROUP BY p.IDPub UNION ALL
    SELECT c.IDProd AS id_ref, c.Fecha AS fecha,'contribucion' AS tipo FROM Contribucion c WHERE c.IDU=@id_influencer) actividad
    LEFT JOIN Compra c ON c.IDProd IN (SELECT IDProd FROM (SELECT IDProd FROM (SELECT IDProd FROM Gustar WHERE IDU=@id_influencer UNION ALL
                                    SELECT IDProd FROM Contribucion WHERE IDU=@id_influencer UNION ALL
                                    SELECT IDProd FROM Compra WHERE IDUC=@id_influencer) interacciones
        GROUP BY IDProd
        ORDER BY COUNT(*) DESC, IDProd ASC
        LIMIT 7) top)
    AND c.Fecha BETWEEN DATE_SUB(actividad.fecha,INTERVAL 14 DAY) AND DATE_ADD(actividad.fecha,INTERVAL 14 DAY)
    GROUP BY actividad.id_ref,actividad.tipo,actividad.fecha) ventas
ORDER BY fecha ASC, tipo ASC;

SELECT COUNT(DISTINCT r.IDU) AS usuarios_que_reaccionaron,
    COUNT(DISTINCT CASE WHEN c.IDUC IS NOT NULL THEN r.IDU END) AS usuarios_que_compraron_despues,
    (COUNT(DISTINCT CASE WHEN c.IDUC IS NOT NULL THEN r.IDU END)/ COUNT(DISTINCT r.IDU))*100 AS tasa_conversion_porcentual
FROM Reaccionar r
JOIN Publicacion p ON r.IDPub=p.IDPub
LEFT JOIN Compra c ON c.IDUC=r.IDU AND c.Fecha>r.Fecha AND c.IDProd IN(SELECT IDProd FROM(SELECT IDProd FROM(SELECT IDProd FROM Gustar WHERE IDU=@id_influencer UNION ALL
    SELECT IDProd FROM Contribucion WHERE IDU=@id_influencer UNION ALL
    SELECT IDProd FROM Compra WHERE IDUC=@id_influencer) interacciones
    GROUP BY IDProd
    ORDER BY COUNT(*) DESC,IDProd ASC
    LIMIT 7) top)
WHERE p.IDU=@id_influencer;