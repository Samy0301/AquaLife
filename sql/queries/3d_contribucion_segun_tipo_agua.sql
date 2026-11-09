USE AquaLife;

WITH contrib AS (
    SELECT ta.IDTA, ta.Tipo AS TipoAgua, e.IDProd, e.NombreComun, e.Categoria
    FROM Contribucion c
    JOIN Especie  e  ON e.IDProd = c.IDProd
    JOIN TipoAgua ta ON ta.IDTA  = e.IDTA
),
total_tipo AS (
    SELECT IDTA, TipoAgua, COUNT(*) AS TotalContribuciones
    FROM contrib
    GROUP BY IDTA, TipoAgua
),
por_especie AS (
    SELECT IDTA, IDProd, NombreComun, COUNT(*) AS n,
           RANK() OVER (PARTITION BY IDTA ORDER BY COUNT(*) DESC) AS rk
    FROM contrib
    GROUP BY IDTA, IDProd, NombreComun
),
por_categoria AS (
    SELECT IDTA, Categoria, COUNT(*) AS n,
           RANK() OVER (PARTITION BY IDTA ORDER BY COUNT(*) DESC) AS rk
    FROM contrib
    GROUP BY IDTA, Categoria
),
top_especie AS (
    SELECT IDTA,
           GROUP_CONCAT(NombreComun ORDER BY NombreComun SEPARATOR ', ') AS Especies,
           MAX(n) AS Contribuciones
    FROM por_especie WHERE rk = 1
    GROUP BY IDTA
),
top_categoria AS (
    SELECT IDTA,
           GROUP_CONCAT(Categoria ORDER BY Categoria SEPARATOR ', ') AS Categorias,
           MAX(n) AS Contribuciones
    FROM por_categoria WHERE rk = 1
    GROUP BY IDTA
)
SELECT
    t.TipoAgua,
    t.TotalContribuciones,
    te.Especies        AS EspecieMasPopular,
    te.Contribuciones  AS ContribucionesEspecie,
    tc.Categorias      AS CategoriaMasPopular,
    tc.Contribuciones  AS ContribucionesCategoria
FROM total_tipo t
JOIN top_especie   te ON te.IDTA = t.IDTA
JOIN top_categoria tc ON tc.IDTA = t.IDTA
ORDER BY t.TotalContribuciones DESC;