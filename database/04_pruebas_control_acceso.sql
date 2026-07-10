-- =====================================================================
-- SCRIPT 04: PRUEBAS DE CONTROL DE ACCESO (PERMITIDOS Y DENEGADOS)
-- Proyecto: Market "La Estancia"
-- Compatibilidad: PostgreSQL 15+
-- =====================================================================

-- NOTA: Este script no debe ejecutarse de golpe, sino bloque por bloque
-- utilizando las conexiones de los diferentes usuarios creados:
-- 1. administrador (rol_administrador)
-- 2. supervisor (rol_supervisor)
-- 3. cajero (rol_operador)
-- 4. consultor (rol_consultor)
-- 5. auditor (rol_auditor)

-- =====================================================================
-- CASO 1: PRUEBAS PARA administrador (Administrador - Acceso Total)
-- Conectar como: administrador / admin
-- =====================================================================

-- A1. Lectura de tablas comerciales y de seguridad (PERMITIDO)
SELECT * FROM productos;
SELECT * FROM usuarios;
SELECT * FROM auditoria_logs;

-- A2. Insercion de un nuevo producto (PERMITIDO)
INSERT INTO productos (nombre, precio, stock, id_proveedor) 
VALUES ('Chocolate Sublime 30g', 1.80, 100, 1);

-- A3. Modificacion de datos sensibles (PERMITIDO)
UPDATE productos SET precio = 2.00 WHERE nombre = 'Chocolate Sublime 30g';

-- A4. Eliminacion de datos (PERMITIDO)
DELETE FROM productos WHERE nombre = 'Chocolate Sublime 30g';


-- =====================================================================
-- CASO 2: PRUEBAS PARA supervisor (Supervisor - Gestion Comercial)
-- Conectar como: supervisor / super
-- =====================================================================

-- S1. Lectura de inventario y logs de auditoria (PERMITIDO)
SELECT * FROM productos;
SELECT id_log, tabla_afectada, operacion, usuario_db, fecha_hora FROM auditoria_logs;

-- S2. Modificacion de stock y precios de productos (PERMITIDO)
UPDATE productos SET stock = 160 WHERE id_producto = 1;

-- S3. Agregar nuevos productos (PERMITIDO)
INSERT INTO productos (nombre, precio, stock, id_proveedor) 
VALUES ('Fideos Don Vittorio 500g', 3.20, 90, 1);

-- S4. Intentar crear un nuevo usuario del sistema (DENEGADO)
-- El supervisor no tiene permisos sobre la tabla de usuarios
INSERT INTO usuarios (username, password_hash, id_rol, activo) 
VALUES ('hack_user', '123', 3, TRUE);

-- S5. Intentar limpiar/eliminar los logs de auditoria (DENEGADO)
-- El supervisor solo puede leer (SELECT) en auditoria_logs, no borrar (DELETE)
DELETE FROM auditoria_logs;


-- =====================================================================
-- CASO 3: PRUEBAS PARA cajero (Operador/Cajero - Transacciones y Clientes)
-- Conectar como: cajero / cajero
-- =====================================================================

-- C1. Consultar productos y registrar un nuevo cliente (PERMITIDO)
SELECT id_producto, nombre, precio, stock FROM productos;
INSERT INTO clientes (nombre_completo, dni, email) 
VALUES ('Patricia Morales Vega', pgp_sym_encrypt('76543210', 'llave_secreta_estancia'), pgp_sym_encrypt('patricia.morales@email.com', 'llave_secreta_estancia'));

-- C2. Registrar una venta en caja (PERMITIDO)
-- Nota: Requiere permisos de INSERT en ventas y USAGE en su secuencia.
INSERT INTO ventas (id_usuario, id_cliente, total) 
VALUES (3, 1, 35.50);

-- C3. Intentar modificar el precio de un producto (DENEGADO)
-- El cajero solo puede ver los productos, no alterar sus precios o stocks
UPDATE productos SET precio = 1.00 WHERE id_producto = 1;

-- C4. Intentar eliminar una venta realizada (DENEGADO)
-- Medida de control: Las ventas registradas no se pueden eliminar de la BD por cajeros
DELETE FROM ventas WHERE id_venta = 1;

-- C5. Intentar consultar la bitacora de auditoria (DENEGADO)
-- El cajero no tiene acceso a los logs del sistema
SELECT * FROM auditoria_logs;


-- =====================================================================
-- CASO 4: PRUEBAS PARA consultor (Consultor - Reportes Solo Lectura)
-- Conectar como: consultor / consultor
-- =====================================================================

-- CO1. Consultar productos y ventas para reportes (PERMITIDO)
SELECT * FROM productos;
SELECT * FROM ventas;

-- CO2. Intentar registrar un nuevo cliente o venta (DENEGADO)
-- El consultor es estrictamente de lectura (SELECT)
INSERT INTO clientes (nombre_completo, dni, email) 
VALUES ('Juan Perez', pgp_sym_encrypt('99999999', 'llave_secreta_estancia'), pgp_sym_encrypt('juan@email.com', 'llave_secreta_estancia'));

-- CO3. Intentar leer la tabla de auditoria (DENEGADO)
SELECT * FROM auditoria_logs;


-- =====================================================================
-- CASO 5: PRUEBAS PARA auditor (Auditor - Seguridad y Bitacora)
-- Conectar como: auditor / auditor
-- =====================================================================

-- AU1. Consultar logs de auditoria, usuarios y roles (PERMITIDO)
SELECT * FROM auditoria_logs;
SELECT * FROM usuarios;
SELECT * FROM roles;

-- AU2. Intentar registrar un producto o venta (DENEGADO)
-- El auditor debe ser pasivo, no realiza operaciones comerciales
INSERT INTO productos (nombre, precio, stock) VALUES ('Intruso', 10.00, 5);

-- AU3. Intentar eliminar o alterar la tabla de auditoria (DENEGADO)
-- Control critico: Los auditores no pueden eliminar evidencia fisica
DELETE FROM auditoria_logs;
DROP TABLE auditoria_logs;
