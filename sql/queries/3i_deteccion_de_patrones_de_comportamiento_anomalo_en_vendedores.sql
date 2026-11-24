Use AquaLife;

SELECT c.IDUV AS id_vendedor,u.Nombre AS vendedor,c.IDProd AS id_producto,pr.Nombre AS producto,
    MIN(c.Precio) AS precio_minimo,MAX(c.Precio) AS precio_maximo,
    ((MAX(c.Precio)-MIN(c.Precio))/ MIN(c.Precio))*100 AS variacion_porcentual,
    MIN(c.Fecha) AS primera_venta,MAX(c.Fecha) AS ultima_venta,
    DATEDIFF(MAX(c.Fecha),MIN(c.Fecha)) AS dias_entre_extremos,
COUNT(*) AS cantidad_ventas
FROM Compra c
JOIN Usuario u ON c.IDUV=u.IDU
JOIN Producto pr ON c.IDProd=pr.IDProd
GROUP BY c.IDUV,u.Nombre,c.IDProd,pr.Nombre
HAVING ((MAX(c.Precio)-MIN(c.Precio))/ MIN(c.Precio))>0.3 AND DATEDIFF(MAX(c.Fecha),MIN(c.Fecha))<=30
ORDER BY variacion_porcentual DESC;

SELECT c.IDUV AS id_vendedor,u.Nombre AS vendedor,
COUNT(c.Puntuacion) AS cantidad_de_calificaciones,
SUM(c.Puntuacion=1) AS cantidad_1,SUM(c.Puntuacion=5) AS cantidad_5,
SUM(c.Puntuacion IN (2,3,4)) AS cantidad_calificaciones_intermedias,
SUM(c.Puntuacion IN (2,3,4))/ COUNT(c.Puntuacion) AS proporcion_calificaciones_intermedias,
2*LEAST(SUM(c.Puntuacion=1),SUM(c.Puntuacion=5))/ COUNT(c.Puntuacion) AS indice_polarizacion
FROM Compra c
JOIN Usuario u ON c.IDUV=u.IDU
WHERE c.Puntuacion IS NOT NULL
GROUP BY c.IDUV,u.Nombre
HAVING COUNT(c.Puntuacion)>=5 AND SUM(c.Puntuacion IN (2,3,4))/ COUNT(c.Puntuacion)<0.3 AND SUM(c.Puntuacion=1)>0 AND SUM(c.Puntuacion=5)>0
ORDER BY indice_polarizacion DESC;

SELECT c.IDUV AS id_vendedor,u.Nombre AS vendedor,
COUNT(DISTINCT c.IDUC) AS cantidad_compradores,
COUNT(DISTINCT CASE WHEN vendedores_por_comprador.cantidad_vendedores=1
    THEN c.IDUC END) AS compradores_exclusivos,
COUNT(DISTINCT CASE WHEN vendedores_por_comprador.cantidad_vendedores=1
    THEN c.IDUC END)/ COUNT(DISTINCT c.IDUC) AS proporcion_exclusivos
FROM Compra c
JOIN Usuario u ON c.IDUV=u.IDU
JOIN (SELECT IDUC,COUNT(DISTINCT IDUV) AS cantidad_vendedores FROM Compra 
    GROUP BY IDUC) vendedores_por_comprador ON vendedores_por_comprador.IDUC=c.IDUC
GROUP BY c.IDUV,u.Nombre
HAVING COUNT(DISTINCT CASE WHEN vendedores_por_comprador.cantidad_vendedores=1
    THEN c.IDUC END)/ COUNT(DISTINCT c.IDUC)>=0.5
ORDER BY proporcion_exclusivos DESC;

SELECT c.IDUV AS id_vendedor,u.Nombre AS vendedor,c.IDProd AS id_producto,pr.Nombre AS producto,
    COUNT(*) AS cantidad_ventas,
    AVG(c.Precio) AS precio_medio_vendedor,
    mediana.mediana_precio AS mediana_precio_especie,
    ((AVG(c.Precio)-mediana.mediana_precio)/ mediana.mediana_precio)*100 AS desviacion_porcentual
FROM Compra c
JOIN Usuario u ON c.IDUV=u.IDU
JOIN Producto pr ON c.IDProd=pr.IDProd
JOIN(SELECT IDProd,AVG(Precio) AS mediana_precio FROM(SELECT IDProd,Precio,
    ROW_NUMBER() OVER(PARTITION BY IDProd ORDER BY Precio) AS fila,
    COUNT(*) OVER(PARTITION BY IDProd) AS total_precios
    FROM Compra) precios_ordenados
WHERE fila IN (FLOOR((total_precios+1)/2),FLOOR((total_precios+2)/2))
GROUP BY IDProd) mediana ON mediana.IDProd=c.IDProd
GROUP BY c.IDUV,u.Nombre,c.IDProd,pr.Nombre,mediana.mediana_precio
HAVING ABS((AVG(c.Precio)-mediana.mediana_precio)/ mediana.mediana_precio)>0.3
ORDER BY ABS((AVG(c.Precio)-mediana.mediana_precio)/ mediana.mediana_precio) DESC;

SELECT u.IDU AS id_vendedor,u.Nombre AS vendedor,
    ROUND(COALESCE(var.variacion_maxima,0)*100,1) AS variacion_maxima_porcentual,
    ROUND(COALESCE(pol.polarizacion,0),3) AS polarizacion,
    ROUND(COALESCE(exc.proporcion_exclusivos,0),3) AS proporcion_exclusivos,
    ROUND(COALESCE(desv.desviacion_maxima,0)*100,1) AS desviacion_maxima_porcentual,
    ROUND(0.3*LEAST(COALESCE(var.variacion_maxima,0),1)+0.25*COALESCE(pol.polarizacion,0)+0.25*COALESCE(exc.proporcion_exclusivos,0)+0.2*LEAST(COALESCE(desv.desviacion_maxima,0),1),3) 
        AS indice_sospecha,
    CASE WHEN 0.3*LEAST(COALESCE(var.variacion_maxima,0),1)+0.25*COALESCE(pol.polarizacion,0)+0.25*COALESCE(exc.proporcion_exclusivos,0)+0.2*LEAST(COALESCE(desv.desviacion_maxima,0),1)>=0.5 
            THEN 'sospechoso'
        ELSE 'normal'
    END AS clasificacion,
    CONCAT_WS('; ',var.evid_var,pol.evid_pol,exc.evid_exc,desv.evid_desv) AS evidencias
FROM Usuario u
JOIN(SELECT DISTINCT IDUV AS IDU FROM Compra) vendedores ON vendedores.IDU=u.IDU
LEFT JOIN(SELECT IDUV,
    MAX(variacion) AS variacion_maxima,
    CONCAT('Variación de precio ',
        ROUND(MAX(CASE WHEN variacion>0.3 THEN variacion END)*100,0),'% en ',
        GROUP_CONCAT(DISTINCT CASE WHEN variacion>0.3 THEN CONCAT(producto,' (',ROUND(variacion*100,0),'%, ',dias_entre_extremos,' días)') END
            ORDER BY variacion DESC SEPARATOR ', ')) AS evid_var
    FROM(SELECT c.IDUV,c.IDProd,pr.Nombre AS producto,
        (MAX(c.Precio)-MIN(c.Precio))/ MIN(c.Precio) AS variacion,
        DATEDIFF(MAX(c.Fecha),MIN(c.Fecha)) AS dias_entre_extremos
        FROM Compra c
        JOIN Producto pr ON c.IDProd=pr.IDProd
        GROUP BY c.IDUV,c.IDProd,pr.Nombre
        HAVING DATEDIFF(MAX(c.Fecha),MIN(c.Fecha))<=30) variaciones
    GROUP BY IDUV) var ON var.IDUV=u.IDU
LEFT JOIN(SELECT IDUV,polarizacion,
            CASE WHEN polarizacion>0.3 THEN CONCAT('Calificaciones polarizadas (índice ',ROUND(polarizacion,2),')') END AS evid_pol
    FROM(SELECT c.IDUV,
        2*LEAST(SUM(c.Puntuacion=1),SUM(c.Puntuacion=5))/ COUNT(c.Puntuacion) AS polarizacion
        FROM Compra c
        WHERE c.Puntuacion IS NOT NULL
        GROUP BY c.IDUV
        HAVING COUNT(c.Puntuacion)>=5) polarizaciones) pol ON pol.IDUV=u.IDU
LEFT JOIN(SELECT IDUV,proporcion_exclusivos,
            CASE WHEN proporcion_exclusivos>=0.5 THEN CONCAT('Compradores exclusivos: ',ROUND(proporcion_exclusivos*100,0),'%') END AS evid_exc
    FROM(SELECT c.IDUV,
        COUNT(DISTINCT CASE WHEN vendedores_por_comprador.cantidad_vendedores=1 THEN c.IDUC END)/ COUNT(DISTINCT c.IDUC) AS proporcion_exclusivos
        FROM Compra c
        JOIN (SELECT IDUC,COUNT(DISTINCT IDUV) AS cantidad_vendedores FROM Compra
            GROUP BY IDUC) vendedores_por_comprador ON vendedores_por_comprador.IDUC=c.IDUC
        GROUP BY c.IDUV) exclusivos) exc ON exc.IDUV=u.IDU
LEFT JOIN(SELECT IDUV,
        MAX(ABS(desviacion)) AS desviacion_maxima,
        CONCAT('Precio medio con una desviación del ',ROUND(MAX(CASE WHEN ABS(desviacion)>0.3 THEN ABS(desviacion) END)*100,0),'% respecto a la mediana de la especie') AS evid_desv
    FROM(SELECT c.IDUV,c.IDProd,pr.Nombre AS producto,
        (AVG(c.Precio)-mediana.mediana_precio)/ mediana.mediana_precio AS desviacion
        FROM Compra c
        JOIN Producto pr ON c.IDProd=pr.IDProd
        JOIN(SELECT IDProd,AVG(Precio) AS mediana_precio FROM(SELECT IDProd,Precio,
            ROW_NUMBER() OVER (PARTITION BY IDProd ORDER BY Precio) AS fila,
            COUNT(*) OVER (PARTITION BY IDProd) AS total_precios
            FROM Compra) precios_ordenados
            WHERE fila IN (FLOOR((total_precios+1)/2),FLOOR((total_precios+2)/2))
            GROUP BY IDProd) mediana ON mediana.IDProd=c.IDProd
        GROUP BY c.IDUV,c.IDProd,pr.Nombre,mediana.mediana_precio) desviaciones
    GROUP BY IDUV) desv ON desv.IDUV=u.IDU
ORDER BY indice_sospecha DESC;