package com.market.LaEstancia.controller;

import jakarta.servlet.http.HttpSession;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.sql.*;
import java.util.*;

@RestController
@RequestMapping("/api/usuarios")
public class UsuariosController extends BaseController {

    @GetMapping
    public ResponseEntity<?> getUsuarios(HttpSession session) {
        List<Map<String, Object>> list = new ArrayList<>();
        String sql = "SELECT u.id_usuario, u.username, u.activo, r.nombre as rol_name " +
                     "FROM usuarios u " +
                     "JOIN roles r ON u.id_rol = r.id_rol " +
                     "ORDER BY u.id_usuario";
        
        try (Connection conn = getConnection(session);
             Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {
            
            while (rs.next()) {
                Map<String, Object> map = new HashMap<>();
                int id = rs.getInt("id_usuario");
                map.put("id", "EMP-" + (100 + id));
                map.put("nombre", rs.getString("username"));
                map.put("login", rs.getString("username"));
                map.put("rol", rs.getString("rol_name"));
                map.put("estado", rs.getBoolean("activo") ? "Activo" : "Inactivo");
                list.add(map);
            }
            return ResponseEntity.ok(list);
            
        } catch (SQLException e) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body(Map.of("error", "Acceso Denegado por PostgreSQL: " + e.getMessage()));
        }
    }

    @PostMapping
    public ResponseEntity<?> createUsuario(@RequestBody Map<String, Object> body, HttpSession session) {
        String username = (String) body.get("login");
        String password = (String) body.get("password");
        String rolStr = (String) body.get("rol");
        boolean activo = "Activo".equalsIgnoreCase((String) body.get("estado"));

        if (username == null || username.trim().isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("error", "El nombre de usuario es obligatorio."));
        }
        if (password == null || password.trim().isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("error", "La contrasena es obligatoria para nuevos usuarios."));
        }

        username = username.trim().toLowerCase();
        if (!username.matches("^[a-z0-9_]+$")) {
            return ResponseEntity.badRequest().body(Map.of("error", "El usuario debe contener solo letras minusculas, numeros y guion bajo."));
        }

        int idRol = 3; // Cajero por defecto
        String pgRole = "rol_operador";
        if ("Administrador".equalsIgnoreCase(rolStr)) {
            idRol = 1;
            pgRole = "rol_administrador";
        } else if ("Supervisor".equalsIgnoreCase(rolStr)) {
            idRol = 2;
            pgRole = "rol_supervisor";
        } else if ("Consultor".equalsIgnoreCase(rolStr)) {
            idRol = 4;
            pgRole = "rol_consultor";
        } else if ("Auditor".equalsIgnoreCase(rolStr)) {
            idRol = 5;
            pgRole = "rol_auditor";
        }

        try (Connection conn = getConnection(session)) {
            // 1. Ejecutar DDL en Postgres para crear el usuario real de base de datos
            try (Statement stmt = conn.createStatement()) {
                stmt.execute("CREATE USER " + username + " WITH PASSWORD '" + password.replace("'", "''") + "'");
                if (!activo) {
                    stmt.execute("ALTER ROLE " + username + " NOLOGIN");
                }
                stmt.execute("GRANT " + pgRole + " TO " + username);
            }

            // 2. Insertar en la tabla de control logico (DML)
            String sql = "INSERT INTO usuarios (username, password_hash, id_rol, activo) VALUES (?, ?, ?, ?) RETURNING id_usuario";
            try (PreparedStatement ps = conn.prepareStatement(sql)) {
                ps.setString(1, username);
                ps.setString(2, "$2a$10$dummybcryptpasswordhash"); // dummy hash
                ps.setInt(3, idRol);
                ps.setBoolean(4, activo);
                
                try (ResultSet rs = ps.executeQuery()) {
                    if (rs.next()) {
                        int newId = rs.getInt("id_usuario");
                        body.put("id", "EMP-" + (100 + newId));
                        body.put("nombre", username);
                        body.remove("password");
                        return ResponseEntity.ok(body);
                    }
                }
            }
            throw new SQLException("No se pudo obtener el ID del usuario generado.");
            
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(Map.of("error", "Error de PostgreSQL: " + e.getMessage()));
        }
    }

    @PutMapping("/{id}")
    public ResponseEntity<?> updateUsuario(@PathVariable String id, @RequestBody Map<String, Object> body, HttpSession session) {
        int numId;
        try {
            numId = Integer.parseInt(id.replace("EMP-", "")) - 100;
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(Map.of("error", "Formato de ID invalido."));
        }
        
        String username = (String) body.get("login");
        String password = (String) body.get("password");
        String rolStr = (String) body.get("rol");
        boolean activo = "Activo".equalsIgnoreCase((String) body.get("estado"));

        if (username == null || username.trim().isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("error", "El nombre de usuario es obligatorio."));
        }

        username = username.trim().toLowerCase();
        if (!username.matches("^[a-z0-9_]+$")) {
            return ResponseEntity.badRequest().body(Map.of("error", "El usuario debe contener solo letras minusculas, numeros y guion bajo."));
        }
        
        int idRol = 3;
        String pgRole = "rol_operador";
        if ("Administrador".equalsIgnoreCase(rolStr)) {
            idRol = 1;
            pgRole = "rol_administrador";
        } else if ("Supervisor".equalsIgnoreCase(rolStr)) {
            idRol = 2;
            pgRole = "rol_supervisor";
        } else if ("Consultor".equalsIgnoreCase(rolStr)) {
            idRol = 4;
            pgRole = "rol_consultor";
        } else if ("Auditor".equalsIgnoreCase(rolStr)) {
            idRol = 5;
            pgRole = "rol_auditor";
        }
        
        try (Connection conn = getConnection(session)) {
            // Obtener usuario anterior para auditar el renombramiento
            String oldUsername = null;
            try (PreparedStatement checkPs = conn.prepareStatement("SELECT username FROM usuarios WHERE id_usuario = ?")) {
                checkPs.setInt(1, numId);
                try (ResultSet rs = checkPs.executeQuery()) {
                    if (rs.next()) {
                        oldUsername = rs.getString("username");
                    }
                }
            }

            if (oldUsername == null) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("error", "Usuario no encontrado en la base de datos."));
            }

            // 1. Ejecutar DDL en Postgres para alterar el login real de base de datos
            try (Statement stmt = conn.createStatement()) {
                if (!oldUsername.equalsIgnoreCase(username)) {
                    stmt.execute("ALTER USER " + oldUsername + " RENAME TO " + username);
                }
                if (password != null && !password.trim().isEmpty()) {
                    stmt.execute("ALTER USER " + username + " WITH PASSWORD '" + password.replace("'", "''") + "'");
                }
                if (activo) {
                    stmt.execute("ALTER ROLE " + username + " LOGIN");
                } else {
                    stmt.execute("ALTER ROLE " + username + " NOLOGIN");
                }
                
                stmt.execute("REVOKE rol_administrador, rol_supervisor, rol_operador, rol_consultor, rol_auditor FROM " + username);
                stmt.execute("GRANT " + pgRole + " TO " + username);
            }

            // 2. Ejecutar DML para actualizar la tabla de control
            String sql = "UPDATE usuarios SET username = ?, id_rol = ?, activo = ? WHERE id_usuario = ?";
            try (PreparedStatement ps = conn.prepareStatement(sql)) {
                ps.setString(1, username);
                ps.setInt(2, idRol);
                ps.setBoolean(3, activo);
                ps.setInt(4, numId);
                
                int updated = ps.executeUpdate();
                if (updated > 0) {
                    body.put("id", id);
                    body.put("nombre", username);
                    body.remove("password");
                    return ResponseEntity.ok(body);
                } else {
                    return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("error", "Usuario no encontrado."));
                }
            }
            
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(Map.of("error", "Error de PostgreSQL: " + e.getMessage()));
        }
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<?> deleteUsuario(@PathVariable String id, HttpSession session) {
        int numId;
        try {
            numId = Integer.parseInt(id.replace("EMP-", "")) - 100;
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(Map.of("error", "Formato de ID invalido."));
        }

        try (Connection conn = getConnection(session)) {
            String username = null;
            try (PreparedStatement checkPs = conn.prepareStatement("SELECT username FROM usuarios WHERE id_usuario = ?")) {
                checkPs.setInt(1, numId);
                try (ResultSet rs = checkPs.executeQuery()) {
                    if (rs.next()) {
                        username = rs.getString("username");
                    }
                }
            }

            if (username == null) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("error", "Usuario no encontrado."));
            }

            // 1. Ejecutar DDL en Postgres para eliminar el usuario real de base de datos
            try (Statement stmt = conn.createStatement()) {
                stmt.execute("DROP USER " + username);
            }

            // 2. Eliminar de la tabla de control logica (DML)
            String sql = "DELETE FROM usuarios WHERE id_usuario = ?";
            try (PreparedStatement ps = conn.prepareStatement(sql)) {
                ps.setInt(1, numId);
                int deleted = ps.executeUpdate();
                
                if (deleted > 0) {
                    return ResponseEntity.ok(Map.of("status", "deleted"));
                } else {
                    return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("error", "Usuario no encontrado."));
                }
            }
            
        } catch (SQLException e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(Map.of("error", "Error de PostgreSQL: " + e.getMessage()));
        }
    }
}
