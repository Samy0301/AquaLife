#!/bin/sh
# Se ejecuta como el ULTIMO script de /docker-entrypoint-initdb.d (ordenado
# alfabeticamente despues de init.sql), es decir, justo despues de que MySQL
# ya cargo los datos en la base de datos durante el primer arranque.
# Borra el init.sql (y este mismo script) para que no quede accesible dentro
# del contenedor en ningun lugar una vez cargados los datos.
set -e
rm -f /docker-entrypoint-initdb.d/init.sql
rm -f /docker-entrypoint-initdb.d/zzz-cleanup.sh
