# =====================================================================
# Script para Ejecutar Pruebas de Permisos y Registrar Evidencias
# Proyecto: Market "La Estancia"
# =====================================================================

$outputFile = "C:\Users\Anyel\OneDrive\Desktop\Base de datos 2-proyecto-market la estancia\Proyecto-BaseDeDatos\database\evidencias_pruebas.md"

# Crear o limpiar el archivo de salida
Set-Content -Path $outputFile -Value "# Evidencias de Pruebas de Control de Acceso y Auditoria" -Encoding utf8
Add-Content -Path $outputFile -Value ""
Add-Content -Path $outputFile -Value "Este documento contiene el resultado real de la ejecucion de pruebas de permisos en la base de datos **marketDB** del Market \"La Estancia\"."
Add-Content -Path $outputFile -Value "Las pruebas verifican los accesos permitidos (exitos) y los accesos denegados (errores de privilegios) para cada rol, ademas de verificar la bitacora de auditoria.`n"
Add-Content -Path $outputFile -Value "La base de datos corre sobre un contenedor Docker y se ejecutan las consultas usando la herramienta `psql` interna con credenciales especificas de cada usuario de base de datos.`n"
Add-Content -Path $outputFile -Value "---"

# Funcion auxiliar para ejecutar consultas SQL con un usuario y loguear el resultado
function Run-TestQuery {
    param(
        [string]$title,
        [string]$user,
        [string]$query
    )
    Write-Host "Ejecutando prueba: $title como $user..."
    Add-Content -Path $outputFile -Value "### $title"
    Add-Content -Path $outputFile -Value "**Usuario**: \`$user\`"
    Add-Content -Path $outputFile -Value "**Consulta SQL**:"
    Add-Content -Path $outputFile -Value "\`\`\`sql`n$query`n\`\`\`"
    Add-Content -Path $outputFile -Value "**Resultado de la ejecucion**:"
    
    # Ejecutar en Docker y capturar stdout y stderr redirigiendo streams
    $result = docker exec -i container_market psql -U $user -d marketDB -c "$query" 2>&1
    
    Add-Content -Path $outputFile -Value "\`\`\`text"
    foreach ($line in $result) {
        # Limpiar el formato de salida si viene en objetos de error de PowerShell
        if ($line -is [System.Management.Automation.ErrorRecord]) {
            Add-Content -Path $outputFile -Value $line.Exception.Message
        } else {
            Add-Content -Path $outputFile -Value $line
        }
    }
    Add-Content -Path $outputFile -Value "\`\`\`"
    Add-Content -Path $outputFile -Value "`n---`n"
}

# 1. Admin Estancia
Add-Content -Path $outputFile -Value "## 1. Pruebas de Acceso: admin_estancia (Rol: rol_administrador)"
Run-TestQuery -title "A1. Lectura de tablas comerciales (productos)" -user "admin_estancia" -query "SELECT * FROM productos LIMIT 2;"
Run-TestQuery -title "A2. Lectura de tabla de usuarios de aplicacion" -user "admin_estancia" -query "SELECT id_usuario, username, id_rol, activo FROM usuarios;"
Run-TestQuery -title "A3. Lectura de tabla de logs de auditoria" -user "admin_estancia" -query "SELECT id_log, tabla_afectada, operacion, usuario_db FROM auditoria_logs LIMIT 3;"
Run-TestQuery -title "A4. Insercion de un nuevo producto (Gestion comercial total)" -user "admin_estancia" -query "INSERT INTO productos (nombre, precio, stock, id_proveedor) VALUES ('Chocolate Sublime 30g', 1.80, 100, 1) RETURNING *;"
Run-TestQuery -title "A5. Modificacion de precio del producto" -user "admin_estancia" -query "UPDATE productos SET precio = 2.00 WHERE nombre = 'Chocolate Sublime 30g' RETURNING *;"
Run-TestQuery -title "A6. Eliminacion del producto insertado" -user "admin_estancia" -query "DELETE FROM productos WHERE nombre = 'Chocolate Sublime 30g' RETURNING *;"

# 2. Supervisor Estancia
Add-Content -Path $outputFile -Value "## 2. Pruebas de Acceso: supervisor_estancia (Rol: rol_supervisor)"
Run-TestQuery -title "S1. Lectura de inventario (productos)" -user "supervisor_estancia" -query "SELECT * FROM productos LIMIT 2;"
Run-TestQuery -title "S2. Modificacion de stock de un producto (Gestion de stock)" -user "supervisor_estancia" -query "UPDATE productos SET stock = 160 WHERE id_producto = 1 RETURNING *;"
Run-TestQuery -title "S3. Agregar nuevos productos (Inventario permitido)" -user "supervisor_estancia" -query "INSERT INTO productos (nombre, precio, stock, id_proveedor) VALUES ('Fideos Don Vittorio 500g', 3.20, 90, 1) RETURNING *;"
Run-TestQuery -title "S4. Intentar crear un nuevo usuario de aplicacion (DENEGADO)" -user "supervisor_estancia" -query "INSERT INTO usuarios (username, password_hash, id_rol, activo) VALUES ('hack_user', '123', 3, TRUE);"
Run-TestQuery -title "S5. Lectura de logs de auditoria (PERMITIDO)" -user "supervisor_estancia" -query "SELECT id_log, tabla_afectada, operacion, usuario_db, fecha_hora FROM auditoria_logs ORDER BY id_log DESC LIMIT 3;"
Run-TestQuery -title "S6. Intentar eliminar los logs de auditoria (DENEGADO)" -user "supervisor_estancia" -query "DELETE FROM auditoria_logs;"
Run-TestQuery -title "S7. Intentar modificar la estructura de la tabla productos (DENEGADO)" -user "supervisor_estancia" -query "ALTER TABLE productos ADD COLUMN descripcion_adicional TEXT;"

# 3. Cajero Estancia
Add-Content -Path $outputFile -Value "## 3. Pruebas de Acceso: cajero_estancia (Rol: rol_operador)"
Run-TestQuery -title "C1. Consultar productos disponibles" -user "cajero_estancia" -query "SELECT id_producto, nombre, precio, stock FROM productos LIMIT 2;"
Run-TestQuery -title "C2. Registrar un nuevo cliente" -user "cajero_estancia" -query "INSERT INTO clientes (nombre_completo, dni, email) VALUES ('Patricia Morales Vega', pgp_sym_encrypt('76543210', 'llave_secreta_estancia'), pgp_sym_encrypt('patricia.morales@email.com', 'llave_secreta_estancia')) RETURNING id_cliente, nombre_completo, puntos;"
Run-TestQuery -title "C3. Registrar una venta" -user "cajero_estancia" -query "INSERT INTO ventas (id_usuario, id_cliente, total) VALUES (3, 4, 35.50) RETURNING *;"
Run-TestQuery -title "C4. Intentar modificar el precio de un producto (DENEGADO)" -user "cajero_estancia" -query "UPDATE productos SET precio = 1.00 WHERE id_producto = 1;"
Run-TestQuery -title "C5. Intentar eliminar una venta realizada (DENEGADO - Control de Integridad)" -user "cajero_estancia" -query "DELETE FROM ventas WHERE id_venta = 1;"
Run-TestQuery -title "C6. Intentar consultar la bitacora de auditoria (DENEGADO)" -user "cajero_estancia" -query "SELECT * FROM auditoria_logs;"
Run-TestQuery -title "C7. Intentar consultar los usuarios del sistema (DENEGADO)" -user "cajero_estancia" -query "SELECT * FROM usuarios;"

# 4. Consultor Estancia
Add-Content -Path $outputFile -Value "## 4. Pruebas de Acceso: consultor_estancia (Rol: rol_consultor)"
Run-TestQuery -title "CO1. Consultar inventario para reportes" -user "consultor_estancia" -query "SELECT * FROM productos LIMIT 2;"
Run-TestQuery -title "CO2. Consultar ventas para reportes" -user "consultor_estancia" -query "SELECT * FROM ventas LIMIT 2;"
Run-TestQuery -title "CO3. Intentar registrar un nuevo cliente (DENEGADO)" -user "consultor_estancia" -query "INSERT INTO clientes (nombre_completo, dni, email) VALUES ('Juan Perez', pgp_sym_encrypt('99999999', 'llave_secreta_estancia'), pgp_sym_encrypt('juan@email.com', 'llave_secreta_estancia'));"
Run-TestQuery -title "CO4. Intentar ver la tabla de auditoria (DENEGADO)" -user "consultor_estancia" -query "SELECT * FROM auditoria_logs;"

# 5. Auditor Estancia
Add-Content -Path $outputFile -Value "## 5. Pruebas de Acceso: auditor_estancia (Rol: rol_auditor)"
Run-TestQuery -title "AU1. Consultar logs de auditoria (PERMITIDO)" -user "auditor_estancia" -query "SELECT id_log, tabla_afectada, operacion, usuario_db, fecha_hora FROM auditoria_logs ORDER BY id_log DESC LIMIT 5;"
Run-TestQuery -title "AU2. Consultar configuracion de usuarios del sistema (PERMITIDO)" -user "auditor_estancia" -query "SELECT id_usuario, username, id_rol, activo FROM usuarios;"
Run-TestQuery -title "AU3. Intentar registrar un producto comercial (DENEGADO)" -user "auditor_estancia" -query "INSERT INTO productos (nombre, precio, stock) VALUES ('Intruso', 10.00, 5);"
Run-TestQuery -title "AU4. Intentar eliminar o alterar la bitacora de auditoria (DENEGADO)" -user "auditor_estancia" -query "DELETE FROM auditoria_logs;"

# 6. Auditoria de los Cambios de los Usuarios
Add-Content -Path $outputFile -Value "## 6. Verificacion de la Auditoria Generada por las Pruebas"
Run-TestQuery -title "Verificar las ultimas operaciones registradas en la auditoria" -user "admin_estancia" -query "SELECT id_log, tabla_afectada, operacion, usuario_db, valor_nuevo FROM auditoria_logs ORDER BY id_log DESC LIMIT 5;"

Write-Host "Pruebas finalizadas. Resultados guardados en: $outputFile"
