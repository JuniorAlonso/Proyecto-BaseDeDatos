# Evidencias de Pruebas de Control de Acceso y Auditoría

Este documento contiene el resultado real de la ejecución de pruebas de permisos en la base de datos **marketDB** del Market "La Estancia".

Las pruebas verifican los accesos permitidos (éxitos) y los accesos denegados (errores de privilegios) para cada rol, además de verificar la bitácora de auditoría.

La base de datos corre sobre un contenedor Docker y se ejecutan las consultas usando la herramienta `psql` interna con credenciales específicas de cada usuario de base de datos.

---

## 1. Pruebas de Acceso: administrador (Rol: rol_administrador)

### A1. Lectura de tablas comerciales (productos)
**Usuario**: `administrador`

**Consulta SQL**:
```sql
SELECT * FROM productos LIMIT 2;
```

**Resultado de la ejecución**:
```text
id_producto |           nombre            | precio | stock | id_proveedor | categoria 
-------------+-----------------------------+--------+-------+--------------+-----------
           1 | Arroz Integral Costeao 1kg |   4.50 |   150 |            1 | Abarrotes
           2 | Aceite Vegetal Primor 1L    |   8.90 |    80 |            1 | Abarrotes
(2 rows)
```

---

### A2. Lectura de tabla de usuarios de aplicación
**Usuario**: `administrador`

**Consulta SQL**:
```sql
SELECT id_usuario, username, id_rol, activo FROM usuarios;
```

**Resultado de la ejecución**:
```text
id_usuario |   username    | id_rol | activo 
------------+---------------+--------+--------
          1 | administrador |      1 | t
          2 | supervisor    |      2 | t
          3 | cajero        |      3 | t
          4 | consultor     |      4 | t
          5 | auditor       |      5 | t
(5 rows)
```

---

### A3. Lectura de tabla de logs de auditoría
**Usuario**: `administrador`

**Consulta SQL**:
```sql
SELECT id_log, tabla_afectada, operacion, usuario_db FROM auditoria_logs LIMIT 3;
```

**Resultado de la ejecución**:
```text
id_log | tabla_afectada | operacion |  usuario_db   
--------+----------------+-----------+---------------
      1 | productos      | INSERT    | administrador
      2 | productos      | UPDATE    | administrador
      3 | productos      | DELETE    | administrador
(3 rows)
```

---

### A4. Inserción de un nuevo producto (Gestión comercial total)
**Usuario**: `administrador`

**Consulta SQL**:
```sql
INSERT INTO productos (nombre, precio, stock, id_proveedor) VALUES ('Chocolate Sublime 30g', 1.80, 100, 1) RETURNING *;
```

**Resultado de la ejecución**:
```text
id_producto |        nombre         | precio | stock | id_proveedor | categoria 
-------------+-----------------------+--------+-------+--------------+-----------
           4 | Chocolate Sublime 30g |   1.80 |   100 |            1 | General
(1 row)

INSERT 0 1
```

---

### A5. Modificación de precio del producto
**Usuario**: `administrador`

**Consulta SQL**:
```sql
UPDATE productos SET precio = 2.00 WHERE nombre = 'Chocolate Sublime 30g' RETURNING *;
```

**Resultado de la ejecución**:
```text
id_producto |        nombre         | precio | stock | id_proveedor | categoria 
-------------+-----------------------+--------+-------+--------------+-----------
           4 | Chocolate Sublime 30g |   2.00 |   100 |            1 | General
(1 row)

UPDATE 1
```

---

### A6. Eliminación del producto insertado
**Usuario**: `administrador`

**Consulta SQL**:
```sql
DELETE FROM productos WHERE nombre = 'Chocolate Sublime 30g' RETURNING *;
```

**Resultado de la ejecución**:
```text
id_producto |        nombre         | precio | stock | id_proveedor | categoria 
-------------+-----------------------+--------+-------+--------------+-----------
           4 | Chocolate Sublime 30g |   2.00 |   100 |            1 | General
(1 row)

DELETE 1
```

---

## 2. Pruebas de Acceso: supervisor (Rol: rol_supervisor)

### S1. Lectura de inventario (productos)
**Usuario**: `supervisor`

**Consulta SQL**:
```sql
SELECT * FROM productos LIMIT 2;
```

**Resultado de la ejecución**:
```text
id_producto |           nombre            | precio | stock | id_proveedor | categoria 
-------------+-----------------------------+--------+-------+--------------+-----------
           1 | Arroz Integral Costeao 1kg |   4.50 |   150 |            1 | Abarrotes
           2 | Aceite Vegetal Primor 1L    |   8.90 |    80 |            1 | Abarrotes
(2 rows)
```

---

### S2. Modificación de stock de un producto (Gestión de stock)
**Usuario**: `supervisor`

**Consulta SQL**:
```sql
UPDATE productos SET stock = 160 WHERE id_producto = 1 RETURNING *;
```

**Resultado de la ejecución**:
```text
id_producto |           nombre            | precio | stock | id_proveedor | categoria 
-------------+-----------------------------+--------+-------+--------------+-----------
           1 | Arroz Integral Costeao 1kg |   4.50 |   160 |            1 | Abarrotes
(1 row)

UPDATE 1
```

---

### S3. Agregar nuevos productos (Inventario permitido)
**Usuario**: `supervisor`

**Consulta SQL**:
```sql
INSERT INTO productos (nombre, precio, stock, id_proveedor) VALUES ('Fideos Don Vittorio 500g', 3.20, 90, 1) RETURNING *;
```

**Resultado de la ejecución**:
```text
id_producto |          nombre          | precio | stock | id_proveedor | categoria 
-------------+--------------------------+--------+-------+--------------+-----------
           5 | Fideos Don Vittorio 500g |   3.20 |    90 |            1 | General
(1 row)

INSERT 0 1
```

---

### S4. Intentar crear un nuevo usuario de aplicación (DENEGADO)
**Usuario**: `supervisor`

**Consulta SQL**:
```sql
INSERT INTO usuarios (username, password_hash, id_rol, activo) VALUES ('hack_user', '123', 3, TRUE);
```

**Resultado de la ejecución**:
```text
ERROR:  permission denied for table usuarios
```

---

### S5. Lectura de logs de auditoría (PERMITIDO)
**Usuario**: `supervisor`

**Consulta SQL**:
```sql
SELECT id_log, tabla_afectada, operacion, usuario_db, fecha_hora FROM auditoria_logs ORDER BY id_log DESC LIMIT 3;
```

**Resultado de la ejecución**:
```text
id_log | tabla_afectada | operacion |  usuario_db   |         fecha_hora         
--------+----------------+-----------+---------------+----------------------------
    101 | productos      | INSERT    | supervisor    | 2026-07-10 01:07:15.43893
    100 | productos      | UPDATE    | supervisor    | 2026-07-10 01:07:15.101553
     99 | productos      | DELETE    | administrador | 2026-07-10 01:07:14.161426
(3 rows)
```

---

### S6. Intentar eliminar los logs de auditoría (DENEGADO)
**Usuario**: `supervisor`

**Consulta SQL**:
```sql
DELETE FROM auditoria_logs;
```

**Resultado de la ejecución**:
```text
ERROR:  permission denied for table auditoria_logs
```

---

### S7. Intentar modificar la estructura de la tabla productos (DENEGADO)
**Usuario**: `supervisor`

**Consulta SQL**:
```sql
ALTER TABLE productos ADD COLUMN descripcion_adicional TEXT;
```

**Resultado de la ejecución**:
```text
ERROR:  must be owner of table productos
```

---

## 3. Pruebas de Acceso: cajero (Rol: rol_operador)

### C1. Consultar productos disponibles
**Usuario**: `cajero`

**Consulta SQL**:
```sql
SELECT id_producto, nombre, precio, stock FROM productos LIMIT 2;
```

**Resultado de la ejecución**:
```text
id_producto |           nombre            | precio | stock 
-------------+-----------------------------+--------+-------
           2 | Aceite Vegetal Primor 1L    |   8.90 |    80
           3 | Leche Evaporada Gloria 400g |   4.20 |   200
(2 rows)
```

---

### C2. Registrar un nuevo cliente
**Usuario**: `cajero`

**Consulta SQL**:
```sql
INSERT INTO clientes (nombre_completo, dni, email) VALUES ('Patricia Morales Vega', '76543210', 'patricia.morales@email.com') RETURNING *;
```

**Resultado de la ejecución**:
```text
id_cliente |    nombre_completo    |   dni    |           email            | telefono | puntos 
------------+-----------------------+----------+----------------------------+----------+--------
          3 | Patricia Morales Vega | 76543210 | patricia.morales@email.com |          |      0
(1 row)

INSERT 0 1
```

---

### C3. Registrar una venta
**Usuario**: `cajero`

**Consulta SQL**:
```sql
INSERT INTO ventas (id_usuario, id_cliente, total) VALUES (3, 2, 35.50) RETURNING *;
```

**Resultado de la ejecución**:
```text
id_venta | id_usuario | id_cliente |        fecha_venta         | total | voucher |   status   | payment_method | items 
----------+------------+------------+----------------------------+-------+---------+------------+----------------+-------
        1 |          3 |          2 | 2026-07-10 01:07:18.727591 | 35.50 |         | Completado | Efectivo       | 
(1 row)

INSERT 0 1
```

---

### C4. Intentar modificar el precio de un producto (DENEGADO)
**Usuario**: `cajero`

**Consulta SQL**:
```sql
UPDATE productos SET precio = 1.00 WHERE id_producto = 1;
```

**Resultado de la ejecución**:
```text
ERROR:  permission denied for table productos
```

---

### C5. Intentar eliminar una venta realizada (DENEGADO - Control de Integridad)
**Usuario**: `cajero`

**Consulta SQL**:
```sql
DELETE FROM ventas WHERE id_venta = 1;
```

**Resultado de la ejecución**:
```text
ERROR:  permission denied for table ventas
```

---

### C6. Intentar consultar la bitácora de auditoría (DENEGADO)
**Usuario**: `cajero`

**Consulta SQL**:
```sql
SELECT * FROM auditoria_logs;
```

**Resultado de la ejecución**:
```text
ERROR:  permission denied for table auditoria_logs
```

---

### C7. Intentar consultar los usuarios del sistema (DENEGADO)
**Usuario**: `cajero`

**Consulta SQL**:
```sql
SELECT * FROM usuarios;
```

**Resultado de la ejecución**:
```text
ERROR:  permission denied for table usuarios
```

---

## 4. Pruebas de Acceso: consultor (Rol: rol_consultor)

### CO1. Consultar inventario para reportes
**Usuario**: `consultor`

**Consulta SQL**:
```sql
SELECT * FROM productos LIMIT 2;
```

**Resultado de la ejecución**:
```text
id_producto |           nombre            | precio | stock | id_proveedor | categoria 
-------------+-----------------------------+--------+-------+--------------+-----------
           2 | Aceite Vegetal Primor 1L    |   8.90 |    80 |            1 | Abarrotes
           3 | Leche Evaporada Gloria 400g |   4.20 |   200 |            2 | Lacteos
(2 rows)
```

---

### CO2. Consultar ventas para reportes
**Usuario**: `consultor`

**Consulta SQL**:
```sql
SELECT * FROM ventas LIMIT 2;
```

**Resultado de la ejecución**:
```text
id_venta | id_usuario | id_cliente |        fecha_venta         | total | voucher |   status   | payment_method | items 
----------+------------+------------+----------------------------+-------+---------+------------+----------------+-------
        1 |          3 |          2 | 2026-07-10 01:07:18.727591 | 35.50 |         | Completado | Efectivo       | 
(1 row)
```

---

### CO3. Intentar registrar un nuevo cliente (DENEGADO)
**Usuario**: `consultor`

**Consulta SQL**:
```sql
INSERT INTO clientes (nombre_completo, dni, email) VALUES ('Juan Pérez', '99999999', 'juan@email.com');
```

**Resultado de la ejecución**:
```text
ERROR:  permission denied for table clientes
```

---

### CO4. Intentar ver la tabla de auditoría (DENEGADO)
**Usuario**: `consultor`

**Consulta SQL**:
```sql
SELECT * FROM auditoria_logs;
```

**Resultado de la ejecución**:
```text
ERROR:  permission denied for table auditoria_logs
```

---

## 5. Pruebas de Acceso: auditor (Rol: rol_auditor)

### AU1. Consultar logs de auditoría (PERMITIDO)
**Usuario**: `auditor`

**Consulta SQL**:
```sql
SELECT id_log, tabla_afectada, operacion, usuario_db, fecha_hora FROM auditoria_logs ORDER BY id_log DESC LIMIT 5;
```

**Resultado de la ejecución**:
```text
id_log | tabla_afectada | operacion |  usuario_db   |         fecha_hora         
--------+----------------+-----------+---------------+----------------------------
    103 | ventas         | INSERT    | cajero        | 2026-07-10 01:07:18.727591
    102 | clientes       | INSERT    | cajero        | 2026-07-10 01:07:18.322589
    101 | productos      | INSERT    | supervisor    | 2026-07-10 01:07:15.43893
    100 | productos      | UPDATE    | supervisor    | 2026-07-10 01:07:15.101553
     99 | productos      | DELETE    | administrador | 2026-07-10 01:07:14.161426
(5 rows)
```

---

### AU2. Consultar configuración de usuarios del sistema (PERMITIDO)
**Usuario**: `auditor`

**Consulta SQL**:
```sql
SELECT id_usuario, username, id_rol, activo FROM usuarios;
```

**Resultado de la ejecución**:
```text
id_usuario |   username    | id_rol | activo 
------------+---------------+--------+--------
          1 | administrador |      1 | t
          2 | supervisor    |      2 | t
          3 | cajero        |      3 | t
          4 | consultor     |      4 | t
          5 | auditor       |      5 | t
(5 rows)
```

---

### AU3. Intentar registrar un producto comercial (DENEGADO)
**Usuario**: `auditor`

**Consulta SQL**:
```sql
INSERT INTO productos (nombre, precio, stock) VALUES ('Intruso', 10.00, 5);
```

**Resultado de la ejecución**:
```text
ERROR:  permission denied for table productos
```

---

### AU4. Intentar eliminar o alterar la bitácora de auditoría (DENEGADO)
**Usuario**: `auditor`

**Consulta SQL**:
```sql
DELETE FROM auditoria_logs;
```

**Resultado de la ejecución**:
```text
ERROR:  permission denied for table auditoria_logs
```

---

## 6. Verificación de la Auditoría Generada por las Pruebas

### Verificar las últimas operaciones registradas en la auditoría
**Usuario**: `administrador`

**Consulta SQL**:
```sql
SELECT id_log, tabla_afectada, operacion, usuario_db, valor_nuevo FROM auditoria_logs ORDER BY id_log DESC LIMIT 5;
```

**Resultado de la ejecución**:
```text
id_log | tabla_afectada | operacion |  usuario_db   |                                                                                             valor_nuevo                                                                                              
--------+----------------+-----------+---------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    103 | ventas         | INSERT    | cajero        | {"items": null, "total": 35.50, "status": "Completado", "voucher": null, "id_venta": 1, "id_cliente": 2, "id_usuario": 3, "fecha_venta": "2026-07-10T01:07:18.727591", "payment_method": "Efectivo"}
    102 | clientes       | INSERT    | cajero        | {"dni": "76543210", "email": "patricia.morales@email.com", "puntos": 0, "telefono": null, "id_cliente": 3, "nombre_completo": "Patricia Morales Vega"}
    101 | productos      | INSERT    | supervisor    | {"stock": 90, "nombre": "Fideos Don Vittorio 500g", "precio": 3.20, "categoria": "General", "id_producto": 5, "id_proveedor": 1}
    100 | productos      | UPDATE    | supervisor    | {"stock": 160, "nombre": "Arroz Integral Costeao 1kg", "precio": 4.50, "categoria": "Abarrotes", "id_producto": 1, "id_proveedor": 1}
     99 | productos      | DELETE    | administrador | 
(5 rows)
```

---

