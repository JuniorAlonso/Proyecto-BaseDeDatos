-- =====================================================================
-- SCRIPT 03: DATOS DE PRUEBA SIMPLIFICADOS (SEMILLA)
-- Proyecto: Market "La Estancia"
-- Compatibilidad: PostgreSQL 15+
-- =====================================================================

-- Limpiar datos existentes en las tablas de negocio (en orden inverso de dependencias)
TRUNCATE TABLE ventas RESTART IDENTITY CASCADE;
TRUNCATE TABLE clientes RESTART IDENTITY CASCADE;
TRUNCATE TABLE productos RESTART IDENTITY CASCADE;
TRUNCATE TABLE proveedores RESTART IDENTITY CASCADE;
TRUNCATE TABLE usuarios RESTART IDENTITY CASCADE;
TRUNCATE TABLE roles RESTART IDENTITY CASCADE;

-- 1. Insertar roles de la aplicacion (Los 5 roles para evitar fallos de JOIN en la UI)
INSERT INTO roles (nombre, descripcion) VALUES
('Administrador', 'Acceso completo al panel administrativo de la aplicacion'),
('Supervisor', 'Gestion de inventario y supervision de ventas'),
('Cajero', 'Registro de ventas en caja y atencion al cliente'),
('Consultor', 'Solo lectura de reportes comerciales y estadisticas'),
('Auditor', 'Visualizacion de logs de seguridad y configuracion de accesos');

-- 2. Insertar los 5 usuarios reales en la tabla logica para su visualizacion y administracion
INSERT INTO usuarios (username, password_hash, id_rol, activo) VALUES
('administrador', '$2a$10$eImiTxAkJyT785O55aT9.eBfU8iT5V7yMvF/g0zXq3xU18.mGPyqC', 1, TRUE),
('supervisor', '$2a$10$oY753kQG4xR5VjH3vG.2K.1xU5Zq4hG8yF9zW2xV3xU18.mGPyqD', 2, TRUE),
('cajero', '$2a$10$dY953kQG4xR5VjH3vG.3K.2xU5Zq4hG8yF9zW2xV3xU18.mGPyqE', 3, TRUE),
('consultor', '$2a$10$fY953kQG4xR5VjH3vG.4K.3xU5Zq4hG8yF9zW2xV3xU18.mGPyqF', 4, TRUE),
('auditor', '$2a$10$gY953kQG4xR5VjH3vG.5K.4xU5Zq4hG8yF9zW2xV3xU18.mGPyqG', 5, TRUE);

-- 3. Insertar exactamente 2 proveedores
INSERT INTO proveedores (nombre_empresa, contacto, telefono) VALUES
('Distribuidora La Estancia S.A.C.', 'Carlos Gomez', '987654321'),
('Lacteos del Sur S.A.', 'Maria Mendoza', '912345678');

-- 4. Insertar exactamente 3 productos en el inventario
INSERT INTO productos (nombre, categoria, precio, stock, id_proveedor) VALUES
('Arroz Integral Costeno 1kg', 'Abarrotes', 4.50, 150, 1),
('Aceite Vegetal Primor 1L', 'Abarrotes', 8.90, 80, 1),
('Leche Evaporada Gloria 400g', 'Lacteos', 4.20, 200, 2);

-- 5. Insertar exactamente 2 clientes
INSERT INTO clientes (nombre_completo, dni, email, telefono, puntos) VALUES
('Luis Alberto Quispe Ramos', pgp_sym_encrypt('12345678', 'llave_secreta_estancia'), pgp_sym_encrypt('luis.quispe@email.com', 'llave_secreta_estancia'), pgp_sym_encrypt('987654321', 'llave_secreta_estancia'), 120),
('Sofia Elena Torres Benitez', pgp_sym_encrypt('87654321', 'llave_secreta_estancia'), pgp_sym_encrypt('sofia.torres@email.com', 'llave_secreta_estancia'), pgp_sym_encrypt('945612378', 'llave_secreta_estancia'), 85);

-- 6. Ventas iniciales vacias para iniciar la demostracion desde cero
-- La tabla 'ventas' comienza vacia para registrar comprobantes desde el POS en vivo.

SELECT 'Datos de prueba (ventas vacias) con los 5 usuarios reales insertados correctamente' AS resultado;
