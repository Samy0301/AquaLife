USE AquaLife;

WITH RECURSIVE Conversacion AS (
 SELECT *, 0 Nivel FROM Comentar
 WHERE IDC=1 -- comentario inicial variable 

 UNION ALL
 
 SELECT c.*, conv.Nivel+1 FROM Comentar c 
 INNER JOIN Conversacion conv
 ON c.IDC_Padre= conv.IDC)
 
 SELECT * FROM Conversacion 
 ORDER BY Nivel , IDC 