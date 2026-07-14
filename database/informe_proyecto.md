-- 1. CREACIÓN DE ROLES (Agrupadores de permisos para la base de datos)
CREATE ROLE rol_administrador WITH CREATEROLE;
CREATE ROLE rol_supervisor;
CREATE ROLE rol_operador;
CREATE ROLE rol_consultor;
CREATE ROLE rol_auditor;

-- 2. ACCESO AL ESQUEMA (Permite a los roles interactuar con las tablas públicas)
GRANT USAGE ON SCHEMA public TO rol_administrador, rol_supervisor, rol_operador, rol_consultor, rol_auditor;

-- 3. PERMISOS DE ADMINISTRADOR (Tiene control total sobre tablas y secuencias)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO rol_administrador;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO rol_administrador;

-- 4. PERMISOS DE SUPERVISOR (Puede gestionar productos, clientes y proveedores, y ver auditorías)
GRANT SELECT, INSERT, UPDATE, DELETE ON productos, clientes, proveedores TO rol_supervisor;
GRANT SELECT, INSERT ON ventas TO rol_supervisor;
GRANT SELECT ON roles, usuarios TO rol_supervisor;
GRANT SELECT ON auditoria_logs TO rol_supervisor;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO rol_supervisor;

-- 5. PERMISOS DE CAJERO/OPERADOR (Puede registrar ventas, crear/editar clientes y leer productos)
GRANT SELECT ON productos, proveedores, ventas TO rol_operador;
GRANT SELECT, INSERT, UPDATE ON clientes TO rol_operador;
GRANT INSERT ON ventas TO rol_operador;
GRANT SELECT (id_usuario, username) ON usuarios TO rol_operador; -- Permiso seguro: solo ve id y nombre de usuarios
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO rol_operador;

-- 6. PERMISOS DE CONSULTOR (Acceso de solo lectura comercial para reportes)
GRANT SELECT ON productos, clientes, proveedores, ventas TO rol_consultor;
GRANT SELECT (id_usuario, username) ON usuarios TO rol_consultor;

-- 7. PERMISOS DE AUDITOR (Lectura completa de todos los datos y de la bitácora de auditoría)
GRANT SELECT ON ALL TABLES IN SCHEMA public TO rol_auditor;

-- 8. CREACIÓN DE USUARIOS REALES (Cuentas con las que se inicia sesión en la aplicación)
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

-- 9. FUNCIÓN DE AUDITORÍA (Registra automáticamente cualquier cambio DML en formato JSONB)
CREATE OR REPLACE FUNCTION fn_auditar_tabla() RETURNS TRIGGER AS $$
DECLARE
    v_old_data JSONB := NULL;
    v_new_data JSONB := NULL;
BEGIN
    -- Identifica si es inserción, actualización o borrado y guarda los estados de las filas
    IF (TG_OP = 'UPDATE') THEN
        v_old_data := to_jsonb(OLD);
        v_new_data := to_jsonb(NEW);
    ELSIF (TG_OP = 'INSERT') THEN
        v_new_data := to_jsonb(NEW);
    ELSIF (TG_OP = 'DELETE') THEN
        v_old_data := to_jsonb(OLD);
    END IF;

    -- Guarda la tabla afectada, la operación, el usuario real (session_user) y los datos en JSONB
    INSERT INTO auditoria_logs (tabla_afectada, operacion, usuario_db, valor_anterior, valor_nuevo)
    VALUES (TG_TABLE_NAME, TG_OP, session_user, v_old_data, v_new_data);

    -- Devuelve el registro para completar la operación original
    IF (TG_OP = 'DELETE') THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER; -- SECURITY DEFINER permite auditar sin dar permisos de escritura directa al cajero

-- 10. ASOCIACIÓN DEL TRIGGER (Activa la auditoría automática al modificar la tabla de productos)
CREATE TRIGGER trg_auditoria_productos
AFTER INSERT OR UPDATE OR DELETE ON productos
FOR EACH ROW EXECUTE FUNCTION fn_auditar_tabla();
