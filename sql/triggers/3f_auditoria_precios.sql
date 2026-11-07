USE AquaLife;

-- 1) Tabla de auditoria ------------------------------------------------------
CREATE TABLE IF NOT EXISTS Historial_Precios (
    IDHist          INT AUTO_INCREMENT PRIMARY KEY,
    IDProd          INT           NOT NULL,
    PrecioAnterior  DECIMAL(10,2) NOT NULL,
    PrecioNuevo     DECIMAL(10,2) NOT NULL,
    PorcentajeCambio DECIMAL(10,2) NULL,        -- NULL si el precio anterior era 0
    FechaCambio     DATE          NOT NULL,
    HoraCambio      TIME          NOT NULL,
    Usuario         VARCHAR(100)  NOT NULL,     -- usuario de MySQL que hizo el UPDATE
    CONSTRAINT fk_hist_producto FOREIGN KEY (IDProd) REFERENCES Producto(IDProd),
    INDEX idx_hist_producto (IDProd, FechaCambio, HoraCambio)
);

-- 2) Trigger -----------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_auditoria_precio;

DELIMITER $$
CREATE TRIGGER trg_auditoria_precio
AFTER UPDATE ON Producto
FOR EACH ROW
BEGIN
    -- Solo si el precio realmente cambio (<=> compara tambien NULL de forma segura)
    IF NOT (OLD.Precio <=> NEW.Precio) THEN
        INSERT INTO Historial_Precios
            (IDProd, PrecioAnterior, PrecioNuevo, PorcentajeCambio,
            FechaCambio, HoraCambio, Usuario)
        VALUES
            (NEW.IDProd,
            OLD.Precio,
            NEW.Precio,
             -- (nuevo - anterior) / anterior * 100; si el anterior era 0 no hay % definido
             IF(OLD.Precio = 0, NULL, ROUND((NEW.Precio - OLD.Precio) / OLD.Precio * 100, 2)),
            CURDATE(),
            CURTIME(),
            USER());
    END IF;
END$$
DELIMITER ;

-- 3) Prueba ------------------------------------------------------------------
-- SELECT IDProd, Nombre, Precio FROM Producto WHERE IDProd = 2;

-- START TRANSACTION;
-- UPDATE Producto SET Precio = 400 WHERE IDProd = 2;
-- SELECT * FROM Historial_Precios WHERE IDProd = 2 ORDER BY IDHist DESC;

