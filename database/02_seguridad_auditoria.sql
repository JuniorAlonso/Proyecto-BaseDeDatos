-- 
-- SCRIPT 02: SEGURIDAD, ROLES Y AUDITORÍA

-- 1. CREACIÓN DE ROLES (Grupos de acceso)
DROP ROLE IF EXISTS rol_administrador;
DROP ROLE IF EXISTS rol_operador;
DROP ROLE IF EXISTS rol_consultor;

CREATE ROLE rol_administrador;
CREATE ROLE rol_operador;
CREATE ROLE rol_consultor;

-- 2. ASIGNACIÓN DE PERMISOS (Principio de mínimo privilegio)
-- Administrador: Control total
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO rol_administrador;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO rol_administrador;

-- Operador: Solo puede gestionar negocio, no configurar ni auditar
GRANT SELECT, INSERT, UPDATE ON productos, ventas, clientes, proveedores TO rol_operador;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO rol_operador;

-- Consultor: Solo lectura (ideal para reportes)
GRANT SELECT ON ALL TABLES IN SCHEMA public TO rol_consultor;

-- 3. CREACIÓN DE USUARIOS DE BASE DE DATOS
DROP USER IF EXISTS admin_estancia;
DROP USER IF EXISTS cajero_estancia;
DROP USER IF EXISTS auditor_estancia;

CREATE USER admin_estancia WITH PASSWORD 'admin_seguro123';
GRANT rol_administrador TO admin_estancia;

CREATE USER cajero_estancia WITH PASSWORD 'cajero_123';
GRANT rol_operador TO cajero_estancia;

CREATE USER auditor_estancia WITH PASSWORD 'auditor_123';
GRANT rol_consultor TO auditor_estancia;

-- 4. IMPLEMENTACIÓN DE AUDITORÍA (Logs automáticos)

-- Tabla que guarda la evidencia de operaciones
CREATE TABLE IF NOT EXISTS auditoria_logs (
    id_log SERIAL PRIMARY KEY,
    tabla_afectada VARCHAR(50),
    operacion VARCHAR(10),
    usuario_db VARCHAR(50),
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    detalles TEXT
);

-- Función que captura los cambios en los productos (ej. cambios de precio o stock)
CREATE OR REPLACE FUNCTION fn_auditar_productos() RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        INSERT INTO auditoria_logs (tabla_afectada, operacion, usuario_db, detalles)
        VALUES ('productos', 'INSERT', current_user, 'Nuevo producto ID: ' || NEW.id_producto || ' - ' || NEW.nombre);
        RETURN NEW;
    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO auditoria_logs (tabla_afectada, operacion, usuario_db, detalles)
        VALUES ('productos', 'UPDATE', current_user, 'Modificado producto ID: ' || NEW.id_producto || ' | Precio/Stock actualizado');
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        INSERT INTO auditoria_logs (tabla_afectada, operacion, usuario_db, detalles)
        VALUES ('productos', 'DELETE', current_user, 'Eliminado producto ID: ' || OLD.id_producto);
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Disparador (Trigger) que activa la función automáticamente
DROP TRIGGER IF EXISTS trg_auditoria_productos ON productos;
CREATE TRIGGER trg_auditoria_productos
AFTER INSERT OR UPDATE OR DELETE ON productos
FOR EACH ROW EXECUTE FUNCTION fn_auditar_productos();