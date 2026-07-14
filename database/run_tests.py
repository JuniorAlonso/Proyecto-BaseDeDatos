# =====================================================================
# Script para Ejecutar Pruebas de Permisos y Registrar Evidencias
# Proyecto: Market "La Estancia"
# =====================================================================

import subprocess
import os

OUTPUT_FILE = r"C:\Users\Anyel\OneDrive\Desktop\Base de datos 2-proyecto-market la estancia\Proyecto-BaseDeDatos\database\evidencias_pruebas.md"

tests = [
    # 1. Administrador
    {"section": "1. Pruebas de Acceso: administrador (Rol: rol_administrador)"},
    {"title": "A1. Lectura de tablas comerciales (productos)", "user": "administrador", "query": "SELECT * FROM productos LIMIT 2;"},
    {"title": "A2. Lectura de tabla de usuarios de aplicación", "user": "administrador", "query": "SELECT id_usuario, username, id_rol, activo FROM usuarios;"},
    {"title": "A3. Lectura de tabla de logs de auditoría", "user": "administrador", "query": "SELECT id_log, tabla_afectada, operacion, usuario_db FROM auditoria_logs LIMIT 3;"},
    {"title": "A4. Inserción de un nuevo producto (Gestión comercial total)", "user": "administrador", "query": "INSERT INTO productos (nombre, precio, stock, id_proveedor) VALUES ('Chocolate Sublime 30g', 1.80, 100, 1) RETURNING *;"},
    {"title": "A5. Modificación de precio del producto", "user": "administrador", "query": "UPDATE productos SET precio = 2.00 WHERE nombre = 'Chocolate Sublime 30g' RETURNING *;"},
    {"title": "A6. Eliminación del producto insertado", "user": "administrador", "query": "DELETE FROM productos WHERE nombre = 'Chocolate Sublime 30g' RETURNING *;"},

    # 2. Supervisor
    {"section": "2. Pruebas de Acceso: supervisor (Rol: rol_supervisor)"},
    {"title": "S1. Lectura de inventario (productos)", "user": "supervisor", "query": "SELECT * FROM productos LIMIT 2;"},
    {"title": "S2. Modificación de stock de un producto (Gestión de stock)", "user": "supervisor", "query": "UPDATE productos SET stock = 160 WHERE id_producto = 1 RETURNING *;"},
    {"title": "S3. Agregar nuevos productos (Inventario permitido)", "user": "supervisor", "query": "INSERT INTO productos (nombre, precio, stock, id_proveedor) VALUES ('Fideos Don Vittorio 500g', 3.20, 90, 1) RETURNING *;"},
    {"title": "S4. Intentar crear un nuevo usuario de aplicación (DENEGADO)", "user": "supervisor", "query": "INSERT INTO usuarios (username, password_hash, id_rol, activo) VALUES ('hack_user', '123', 3, TRUE);"},
    {"title": "S5. Lectura de logs de auditoría (PERMITIDO)", "user": "supervisor", "query": "SELECT id_log, tabla_afectada, operacion, usuario_db, fecha_hora FROM auditoria_logs ORDER BY id_log DESC LIMIT 3;"},
    {"title": "S6. Intentar eliminar los logs de auditoría (DENEGADO)", "user": "supervisor", "query": "DELETE FROM auditoria_logs;"},
    {"title": "S7. Intentar modificar la estructura de la tabla productos (DENEGADO)", "user": "supervisor", "query": "ALTER TABLE productos ADD COLUMN descripcion_adicional TEXT;"},

    # 3. Cajero
    {"section": "3. Pruebas de Acceso: cajero (Rol: rol_operador)"},
    {"title": "C1. Consultar productos disponibles", "user": "cajero", "query": "SELECT id_producto, nombre, precio, stock FROM productos LIMIT 2;"},
    {"title": "C2. Registrar un nuevo cliente", "user": "cajero", "query": "INSERT INTO clientes (nombre_completo, dni, email) VALUES ('Patricia Morales Vega', pgp_sym_encrypt('76543210', 'llave_secreta_estancia'), pgp_sym_encrypt('patricia.morales@email.com', 'llave_secreta_estancia')) RETURNING id_cliente, nombre_completo, puntos;"},
    {"title": "C3. Registrar una venta", "user": "cajero", "query": "INSERT INTO ventas (id_usuario, id_cliente, total) VALUES (3, 2, 35.50) RETURNING *;"},
    {"title": "C4. Intentar modificar el precio de un producto (DENEGADO)", "user": "cajero", "query": "UPDATE productos SET precio = 1.00 WHERE id_producto = 1;"},
    {"title": "C5. Intentar eliminar una venta realizada (DENEGADO - Control de Integridad)", "user": "cajero", "query": "DELETE FROM ventas WHERE id_venta = 1;"},
    {"title": "C6. Intentar consultar la bitácora de auditoría (DENEGADO)", "user": "cajero", "query": "SELECT * FROM auditoria_logs;"},
    {"title": "C7. Intentar consultar los usuarios del sistema (DENEGADO)", "user": "cajero", "query": "SELECT * FROM usuarios;"},
 
    # 4. Consultor
    {"section": "4. Pruebas de Acceso: consultor (Rol: rol_consultor)"},
    {"title": "CO1. Consultar inventario para reportes", "user": "consultor", "query": "SELECT * FROM productos LIMIT 2;"},
    {"title": "CO2. Consultar ventas para reportes", "user": "consultor", "query": "SELECT * FROM ventas LIMIT 2;"},
    {"title": "CO3. Intentar registrar un nuevo cliente (DENEGADO)", "user": "consultor", "query": "INSERT INTO clientes (nombre_completo, dni, email) VALUES ('Juan Pérez', pgp_sym_encrypt('99999999', 'llave_secreta_estancia'), pgp_sym_encrypt('juan@email.com', 'llave_secreta_estancia'));"},
    {"title": "CO4. Intentar ver la tabla de auditoría (DENEGADO)", "user": "consultor", "query": "SELECT * FROM auditoria_logs;"},

    # 5. Auditor
    {"section": "5. Pruebas de Acceso: auditor (Rol: rol_auditor)"},
    {"title": "AU1. Consultar logs de auditoría (PERMITIDO)", "user": "auditor", "query": "SELECT id_log, tabla_afectada, operacion, usuario_db, fecha_hora FROM auditoria_logs ORDER BY id_log DESC LIMIT 5;"},
    {"title": "AU2. Consultar configuración de usuarios del sistema (PERMITIDO)", "user": "auditor", "query": "SELECT id_usuario, username, id_rol, activo FROM usuarios;"},
    {"title": "AU3. Intentar registrar un producto comercial (DENEGADO)", "user": "auditor", "query": "INSERT INTO productos (nombre, precio, stock) VALUES ('Intruso', 10.00, 5);"},
    {"title": "AU4. Intentar eliminar o alterar la bitácora de auditoría (DENEGADO)", "user": "auditor", "query": "DELETE FROM auditoria_logs;"},

    # 6. Auditoría
    {"section": "6. Verificación de la Auditoría Generada por las Pruebas"},
    {"title": "Verificar las últimas operaciones registradas en la auditoría", "user": "administrador", "query": "SELECT id_log, tabla_afectada, operacion, usuario_db, valor_nuevo FROM auditoria_logs ORDER BY id_log DESC LIMIT 5;"}
]

def run_query(user, query):
    cmd = ["docker", "exec", "-i", "container_market", "psql", "-U", user, "-d", "marketDB", "-c", query]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=10)
        output = result.stdout if result.stdout else ""
        error = result.stderr if result.stderr else ""
        return (output + "\n" + error).strip()
    except Exception as e:
        return str(e)

def main():
    print("Iniciando ejecución de pruebas de seguridad...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# Evidencias de Pruebas de Control de Acceso y Auditoría\n\n")
        f.write("Este documento contiene el resultado real de la ejecución de pruebas de permisos en la base de datos **marketDB** del Market \"La Estancia\".\n\n")
        f.write("Las pruebas verifican los accesos permitidos (éxitos) y los accesos denegados (errores de privilegios) para cada rol, además de verificar la bitácora de auditoría.\n\n")
        f.write("La base de datos corre sobre un contenedor Docker y se ejecutan las consultas usando la herramienta `psql` interna con credenciales específicas de cada usuario de base de datos.\n\n")
        f.write("---\n\n")
        
        for item in tests:
            if "section" in item:
                f.write(f"## {item['section']}\n\n")
                print(f"Procesando sección: {item['section']}")
            else:
                title = item["title"]
                user = item["user"]
                query = item["query"]
                print(f" Ejecutando: {title} como {user}")
                
                f.write(f"### {title}\n")
                f.write(f"**Usuario**: `{user}`\n\n")
                f.write("**Consulta SQL**:\n")
                f.write(f"```sql\n{query}\n```\n\n")
                f.write("**Resultado de la ejecución**:\n")
                
                result_text = run_query(user, query)
                
                f.write(f"```text\n{result_text}\n```\n\n")
                f.write("---\n\n")
                
    print(f"Ejecución finalizada. Resultados guardados en {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
