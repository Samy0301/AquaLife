#!/bin/sh
# Se ejecuta como el PRIMER script de /docker-entrypoint-initdb.d (ordenado
# alfabeticamente antes de init.sql), es decir, justo antes de que MySQL
# cargue los datos en la base de datos durante el primer arranque.
# Calcula el SHA-256 de init.sql y lo imprime en los logs del contenedor,
# para dejar registro y poder comparar ese hash entre distintas
# generaciones/builds (deben coincidir siempre, dado que la generacion es
# reproducible por defecto: ver DEFAULT_SEED / DEFAULT_REFERENCE_DATE en
# generate_init_sql.py).
set -e
HASH=$(sha256sum /docker-entrypoint-initdb.d/init.sql | awk '{print $1}')
echo "[hash-init] SHA-256 de init.sql: $HASH"
