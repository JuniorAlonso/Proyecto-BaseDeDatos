-- =====================================================================
-- SCRIPT 02: SEGURIDAD, ROLES, PERMISOS Y AUDITORIA
-- Proyecto: Market "La Estancia"
-- Compatibilidad: PostgreSQL 15+
-- =====================================================================

-- =====================================================================
-- 1. LIMPIEZA DE OBJETOS PREVIOS
-- =====================================================================
-- Eliminar disparadores (triggers)
DROP TRIGGER IF EXISTS trg_auditoria_productos ON productos;
DROP TRIGGER IF EXISTS trg_auditoria_clientes ON clientes;
DROP TRIGGER IF EXISTS trg_auditoria_ventas ON ventas;
DROP TRIGGER IF EXISTS trg_auditoria_usuarios ON usuarios;

-- Eliminar funcion de auditoria
DROP FUNCTION IF EXISTS fn_auditar_tabla();

-- Eliminar tabla de auditoria
DROP TABLE IF EXISTS auditoria_logs CASCADE;

-- Revocar TODOS los privilegios de los roles existentes en el esquema public
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'rol_administrador') THEN
        REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM rol_administrador;
        REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM rol_administrador;
        REVOKE ALL PRIVILEGES ON SCHEMA public FROM rol_administrador;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'rol_supervisor') THEN
        REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM rol_supervisor;
        REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM rol_supervisor;
        REVOKE ALL PRIVILEGES ON SCHEMA public FROM rol_supervisor;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'rol_operador') THEN
        REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM rol_operador;
        REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM rol_operador;
        REVOKE ALL PRIVILEGES ON SCHEMA public FROM rol_operador;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'rol_consultor') THEN
        REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM rol_consultor;
        REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM rol_consultor;
        REVOKE ALL PRIVILEGES ON SCHEMA public FROM rol_consultor;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'rol_auditor') THEN
        REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM rol_auditor;
        REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM rol_auditor;
        REVOKE ALL PRIVILEGES ON SCHEMA public FROM rol_auditor;
    END IF;
END $$;

-- Eliminar usuarios de base de datos anteriores con sufijo _estancia
DROP USER IF EXISTS admin_estancia;
DROP USER IF EXISTS supervisor_estancia;
DROP USER IF EXISTS cajero_estancia;
DROP USER IF EXISTS consultor_estancia;
DROP USER IF EXISTS auditor_estancia;

-- Eliminar usuarios de base de datos sin sufijo
DROP USER IF EXISTS administrador;
DROP USER IF EXISTS supervisor;
DROP USER IF EXISTS cajero;
DROP USER IF EXISTS consultor;
DROP USER IF EXISTS auditor;

-- Intentar eliminar los roles ahora que no tienen privilegios concedidos en objetos
DROP ROLE IF EXISTS rol_administrador;
DROP ROLE IF EXISTS rol_supervisor;
DROP ROLE IF EXISTS rol_operador;
DROP ROLE IF EXISTS rol_consultor;
DROP ROLE IF EXISTS rol_auditor;

-- =====================================================================
-- 2. CREACION DE ROLES (Grupos de Acceso)
-- =====================================================================
CREATE ROLE rol_administrador WITH CREATEROLE;
CREATE ROLE rol_supervisor;
CREATE ROLE rol_operador;
CREATE ROLE rol_consultor;
CREATE ROLE rol_auditor;

COMMENT ON ROLE rol_administrador IS 'Acceso total y configuracion de la base de datos (DBA).';
COMMENT ON ROLE rol_supervisor IS 'Gestion del negocio (productos, proveedores, clientes) y visualizacion de auditoria.';
COMMENT ON ROLE rol_operador IS 'Operador de caja. Registra ventas y clientes, visualiza productos.';
COMMENT ON ROLE rol_consultor IS 'Solo lectura para reportes y visualizacion del negocio.';
COMMENT ON ROLE rol_auditor IS 'Auditoria interna. Solo lectura de logs y configuracion de seguridad.';

-- =====================================================================
-- 3. ASIGNACION DE PERMISOS (Principio de Minimo Privilegio)
-- =====================================================================

-- Otorgar uso del esquema publico a todos los roles
GRANT USAGE ON SCHEMA public TO rol_administrador, rol_supervisor, rol_operador, rol_consultor, rol_auditor;

-- 3.1. Administrador (Control Total)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO rol_administrador;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO rol_administrador;

-- 3.2. Supervisor (Gestion de Inventario y Clientes)
GRANT SELECT, INSERT, UPDATE, DELETE ON productos, clientes, proveedores TO rol_supervisor;
GRANT SELECT, INSERT ON ventas TO rol_supervisor; -- El supervisor registra ventas pero no puede alterarlas
GRANT SELECT ON roles, usuarios TO rol_supervisor; -- Puede ver los usuarios de la aplicacion
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO rol_supervisor;

-- 3.3. Operador / Cajero (Ventas y Registro de Clientes)
GRANT SELECT ON productos, proveedores, ventas TO rol_operador;
GRANT SELECT, INSERT, UPDATE ON clientes TO rol_operador; -- Registra o actualiza datos del cliente
GRANT INSERT ON ventas TO rol_operador; -- Registra ventas en caja. No puede eliminar ni modificar ventas.
GRANT SELECT (id_usuario, username) ON usuarios TO rol_operador; -- Permite unir para ver el cajero en el POS
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO rol_operador;

-- 3.4. Consultor (Reportes de Negocio - Solo Lectura)
GRANT SELECT ON productos, clientes, proveedores, ventas TO rol_consultor;
GRANT SELECT (id_usuario, username) ON usuarios TO rol_consultor; -- Permite unir para reportes de ventas

-- 3.5. Auditor (Visualizacion de Seguridad y Auditoria - Solo Lectura)
GRANT SELECT ON ALL TABLES IN SCHEMA public TO rol_auditor;
-- El auditor tiene acceso a ver todo, pero NINGUN permiso de escritura (INSERT, UPDATE, DELETE) en ninguna tabla.

-- =====================================================================
-- 4. CREACION DE USUARIOS DE BASE DE DATOS (Nombres Simplificados)
-- =====================================================================
CREATE USER administrador WITH PASSWORD 'admin';
GRANT rol_administrador TO administrador;

CREATE USER supervisor WITH PASSWORD 'super';
GRANT rol_supervisor TO supervisor;

CREATE USER cajero WITH PASSWORD 'cajero';
GRANT rol_operador TO cajero;

CREATE USER consultor WITH PASSWORD 'consultor';
GRANT rol_consultor TO consultor;

CREATE USER auditor WITH PASSWORD 'auditor';
GRANT rol_auditor TO auditor;

-- =====================================================================
-- 5. IMPLEMENTACION DE AUDITORIA AVANZADA (Logs Automaticos)
-- =====================================================================

-- Tabla para guardar el historial detallado de cambios (DML)
CREATE TABLE auditoria_logs (
    id_log SERIAL PRIMARY KEY,
    tabla_afectada VARCHAR(50) NOT NULL,
    operacion VARCHAR(10) NOT NULL, -- INSERT, UPDATE, DELETE
    usuario_db VARCHAR(50) NOT NULL, -- Usuario de BD que ejecuto el comando
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    valor_anterior JSONB,            -- Estado previo del registro (NULL en INSERT)
    valor_nuevo JSONB                -- Estado nuevo del registro (NULL en DELETE)
);

COMMENT ON TABLE auditoria_logs IS 'Bitacora de auditoria detallada de operaciones de insercion, actualizacion y borrado.';

-- Asignacion de permisos sobre la tabla de auditoria
REVOKE ALL ON auditoria_logs FROM PUBLIC;
GRANT SELECT ON auditoria_logs TO rol_administrador;
GRANT SELECT ON auditoria_logs TO rol_supervisor;
GRANT SELECT ON auditoria_logs TO rol_auditor;

-- Funcion de Auditoria Generica con SECURITY DEFINER
CREATE OR REPLACE FUNCTION fn_auditar_tabla() RETURNS TRIGGER AS $$
DECLARE
    v_old_data JSONB := NULL;
    v_new_data JSONB := NULL;
BEGIN
    IF (TG_OP = 'UPDATE') THEN
        v_old_data := to_jsonb(OLD);
        v_new_data := to_jsonb(NEW);
    ELSIF (TG_OP = 'INSERT') THEN
        v_new_data := to_jsonb(NEW);
    ELSIF (TG_OP = 'DELETE') THEN
        v_old_data := to_jsonb(OLD);
    END IF;

    INSERT INTO auditoria_logs (tabla_afectada, operacion, usuario_db, valor_anterior, valor_nuevo)
    VALUES (TG_TABLE_NAME, TG_OP, session_user, v_old_data, v_new_data);

    IF (TG_OP = 'DELETE') THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================================
-- 6. ASOCIACION DE DISPARADORES (Triggers)
-- =====================================================================

-- Trigger para la tabla productos (Inventario)
CREATE TRIGGER trg_auditoria_productos
AFTER INSERT OR UPDATE OR DELETE ON productos
FOR EACH ROW EXECUTE FUNCTION fn_auditar_tabla();

-- Trigger para la tabla clientes
CREATE TRIGGER trg_auditoria_clientes
AFTER INSERT OR UPDATE OR DELETE ON clientes
FOR EACH ROW EXECUTE FUNCTION fn_auditar_tabla();

-- Trigger para la tabla ventas (Ventas cabecera)
CREATE TRIGGER trg_auditoria_ventas
AFTER INSERT OR UPDATE OR DELETE ON ventas
FOR EACH ROW EXECUTE FUNCTION fn_auditar_tabla();

-- Trigger para la tabla usuarios (Seguridad de la aplicacion)
CREATE TRIGGER trg_auditoria_usuarios
AFTER INSERT OR UPDATE OR DELETE ON usuarios
FOR EACH ROW EXECUTE FUNCTION fn_auditar_tabla();