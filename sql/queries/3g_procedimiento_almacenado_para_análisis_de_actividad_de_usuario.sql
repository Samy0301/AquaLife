USE AquaLife;
DELIMITER //
DROP PROCEDURE IF EXISTS sp_analisis_usuario //
CREATE PROCEDURE sp_analisis_usuario(IN id_usuario INT,IN fecha_inicio DATE,IN fecha_fin DATE)
BEGIN
SELECT
(SELECT Nombre FROM Usuario WHERE IDU=id_usuario) AS nombre,

(SELECT COUNT(*) FROM Publicacion p WHERE p.IDU=id_usuario AND (SELECT MIN(r.Fecha) FROM Reaccionar r WHERE r.IDPub=p.IDPub) BETWEEN fecha_inicio AND fecha_fin) AS publicaciones,

(SELECT COUNT(*) FROM Reaccionar r WHERE r.IDU=id_usuario AND r.Fecha BETWEEN fecha_inicio AND fecha_fin) AS reacciones_dadas,

(SELECT COUNT(*) FROM Reaccionar r 
JOIN Publicacion p ON r.IDPub=p.IDPub WHERE p.IDU=id_usuario AND r.Fecha BETWEEN fecha_inicio AND fecha_fin) AS reacciones_recibidas,

(SELECT COUNT(*) FROM Comentar c 
JOIN Publicacion p ON c.IDPub=p.IDPub WHERE c.IDU=id_usuario AND (SELECT MIN(r.Fecha) FROM Reaccionar r WHERE r.IDPub=p.IDPub) BETWEEN fecha_inicio AND fecha_fin) AS comentarios,

(SELECT COUNT(*) FROM Compra co WHERE co.IDUC=id_usuario AND co.Fecha BETWEEN fecha_inicio AND fecha_fin) AS compras,

COALESCE(
    (SELECT SUM(co.Precio*co.Cantidad) FROM Compra co WHERE co.IDUC=id_usuario AND co.Fecha BETWEEN fecha_inicio AND fecha_fin),0) AS monto_gastado,

(SELECT COUNT(*) FROM Contribucion con WHERE con.IDU=id_usuario AND con.Fecha BETWEEN fecha_inicio AND fecha_fin) AS contribuciones,

(SELECT e.NombreComun FROM Compra co 
JOIN Especie e ON co.IDProd=e.IDProd WHERE co.IDUC=id_usuario AND co.Fecha BETWEEN fecha_inicio AND fecha_fin 
GROUP BY co.IDProd,e.NombreComun 
ORDER BY COUNT(*) DESC,SUM(co.Cantidad) DESC,co.IDProd ASC 
LIMIT 1) AS especie_mas_comprada,

(SELECT e.NombreComun FROM Contribucion con
JOIN Especie e ON con.IDProd=e.IDProd WHERE con.IDU=id_usuario AND con.Fecha BETWEEN fecha_inicio AND fecha_fin
GROUP BY con.IDProd,e.NombreComun
ORDER BY COUNT(*) DESC,con.IDProd ASC
LIMIT 1) AS especie_mas_contribuida;

END //
DELIMITER ;