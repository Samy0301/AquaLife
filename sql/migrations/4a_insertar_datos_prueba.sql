USE AquaLife;

SET @pub = 59;
SET @u1 = 1, @u2 = 2, @u3 = 3, @u4 = 4, @u5 = 5;

INSERT INTO Comentar (IDC_Padre, IDU, IDPub, comentario) VALUES (NULL, @u1, @pub, 'Mis barbos tigre tienen puntitos blancos y se rascan contra la decoración. ¿Qué puede ser?');
SET @c1 = LAST_INSERT_ID();

INSERT INTO Comentar (IDC_Padre, IDU, IDPub, comentario) VALUES (@c1, @u2, @pub, '¿Los puntos son como granos de sal? Suena a ich (Ichthyophthirius).');
SET @c2 = LAST_INSERT_ID();

INSERT INTO Comentar (IDC_Padre, IDU, IDPub, comentario) VALUES (@c1, @u3, @pub, 'Antes de diagnosticar: ¿qué temperatura y parámetros de agua tienes?');
SET @c3 = LAST_INSERT_ID();

INSERT INTO Comentar (IDC_Padre, IDU, IDPub, comentario) VALUES (@c3, @u1, @pub, '24 °C, amoníaco 0, nitritos 0.25, nitratos 20.');
SET @c4 = LAST_INSERT_ID();

INSERT INTO Comentar (IDC_Padre, IDU, IDPub, comentario) VALUES (@c4, @u3, @pub, 'Esos nitritos son altos y estresan a los peces, lo que facilita la enfermedad.');
SET @c5 = LAST_INSERT_ID();

INSERT INTO Comentar (IDC_Padre, IDU, IDPub, comentario) VALUES (@c2, @u1, @pub, 'Sí, los veo en aletas y cuerpo, parecen granos de sal.');
SET @c6 = LAST_INSERT_ID();

INSERT INTO Comentar (IDC_Padre, IDU, IDPub, comentario) VALUES (@c6, @u2, @pub, 'Es ich clásico. Sube la temperatura poco a poco hasta 28 °C y considera sal.');
SET @c7 = LAST_INSERT_ID();

INSERT INTO Comentar (IDC_Padre, IDU, IDPub, comentario) VALUES (@c7, @u4, @pub, 'Ojo con la sal si tienes corydoras o plantas delicadas.');
SET @c8 = LAST_INSERT_ID();

INSERT INTO Comentar (IDC_Padre, IDU, IDPub, comentario) VALUES (@c8, @u1, @pub, 'Sí, tengo corydoras y varias plantas.');
SET @c9 = LAST_INSERT_ID();

INSERT INTO Comentar (IDC_Padre, IDU, IDPub, comentario) VALUES (@c9, @u4, @pub, 'Entonces mejor un medicamento específico para ich, a media dosis por los corydoras.');
SET @c10 = LAST_INSERT_ID();

INSERT INTO Comentar (IDC_Padre, IDU, IDPub, comentario) VALUES (@c5, @u5, @pub, 'Haz un cambio de agua del 30% para bajar los nitritos.');
SET @c11 = LAST_INSERT_ID();

INSERT INTO Comentar (IDC_Padre, IDU, IDPub, comentario) VALUES (@c11, @u1, @pub, 'Hecho. Los nitritos bajaron a 0.1.');
SET @c12 = LAST_INSERT_ID();

INSERT INTO Comentar (IDC_Padre, IDU, IDPub, comentario) VALUES (@c12, @u3, @pub, 'Perfecto. Repite el cambio a diario mientras dure el tratamiento.');
SET @c13 = LAST_INSERT_ID();

INSERT INTO Comentar (IDC_Padre, IDU, IDPub, comentario) VALUES (@c10, @u2, @pub, 'Importante: retira el carbón activo del filtro, anula el medicamento.');
SET @c14 = LAST_INSERT_ID();

INSERT INTO Comentar (IDC_Padre, IDU, IDPub, comentario) VALUES (@c14, @u1, @pub, 'Carbón retirado y medicamento puesto.');
SET @c15 = LAST_INSERT_ID();

INSERT INTO Comentar (IDC_Padre, IDU, IDPub, comentario) VALUES (@c1, @u5, @pub, '¿Pusiste peces nuevos hace poco? Podría ser el origen del brote.');
SET @c16 = LAST_INSERT_ID();

INSERT INTO Comentar (IDC_Padre, IDU, IDPub, comentario) VALUES (@c16, @u1, @pub, 'Sí, compré dos barbos hace 10 días y no hice cuarentena.');
SET @c17 = LAST_INSERT_ID();

INSERT INTO Comentar (IDC_Padre, IDU, IDPub, comentario) VALUES (@c17, @u5, @pub, 'Probable origen. Trata todo el acuario, no solo a los afectados.');
SET @c18 = LAST_INSERT_ID();

INSERT INTO Comentar (IDC_Padre, IDU, IDPub, comentario) VALUES (@c15, @u4, @pub, 'Mantén el tratamiento 7-10 días y 3 más tras desaparecer los puntos.');
SET @c19 = LAST_INSERT_ID();

INSERT INTO Comentar (IDC_Padre, IDU, IDPub, comentario) VALUES (@c19, @u1, @pub, 'Día 5: los puntos van desapareciendo y comen con normalidad.');
SET @c20 = LAST_INSERT_ID();

INSERT INTO Comentar (IDC_Padre, IDU, IDPub, comentario) VALUES (@c20, @u2, @pub, 'Genial. Cuando acabes, monta un tanque de cuarentena para futuros peces.');
SET @c21 = LAST_INSERT_ID();

INSERT INTO Comentar (IDC_Padre, IDU, IDPub, comentario) VALUES (@c21, @u1, @pub, 'Resuelto, gracias a todos por el diagnóstico colaborativo.');
SET @c22 = LAST_INSERT_ID();