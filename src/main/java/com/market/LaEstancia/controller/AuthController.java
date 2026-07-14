package com.market.LaEstancia.controller;

import jakarta.servlet.http.HttpSession;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.sql.*;
import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/auth")
public class AuthController extends BaseController {

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody Map<String, String> credentials, HttpSession session) {
        String username = credentials.get("username");
        String password = credentials.get("password");

        if (username == null || password == null || username.trim().isEmpty() || password.trim().isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("error", "Usuario y contrasena son requeridos."));
        }

        String url = "jdbc:postgresql://localhost:5432/marketDB";
        try (Connection conn = DriverManager.getConnection(url, username, password)) {
            
            // Consultar dinamicamente que rol (rol_...) posee este usuario de base de datos
            String roleQuery = "SELECT rolname FROM pg_roles WHERE pg_has_role(current_user, oid, 'member') AND rolname LIKE 'rol_%'";
            String role = "sin_rol";
            
            try (Statement stmt = conn.createStatement();
                 ResultSet rs = stmt.executeQuery(roleQuery)) {
                if (rs.next()) {
                    role = rs.getString("rolname");
                }
            }

            // Almacenar las credenciales en la sesion HTTP
            session.setAttribute("dbUser", username);
            session.setAttribute("dbPass", password);
            session.setAttribute("dbRole", role);

            Map<String, String> response = new HashMap<>();
            response.put("username", username);
            response.put("role", role);
            response.put("status", "success");
            return ResponseEntity.ok(response);
            
        } catch (SQLException e) {
            return ResponseEntity.status(401).body(Map.of("error", "Error de conexion a PostgreSQL: " + e.getMessage()));
        }
    }

    @PostMapping("/logout")
    public ResponseEntity<?> logout(HttpSession session) {
        session.invalidate();
        return ResponseEntity.ok(Map.of("status", "logged_out"));
    }

    @GetMapping("/status")
    public ResponseEntity<?> status(HttpSession session) {
        String dbUser = (String) session.getAttribute("dbUser");
        String dbRole = (String) session.getAttribute("dbRole");

        if (dbUser == null) {
            return ResponseEntity.ok(Map.of("loggedIn", false));
        }

        Map<String, Object> response = new HashMap<>();
        response.put("loggedIn", true);
        response.put("username", dbUser);
        response.put("role", dbRole);
        return ResponseEntity.ok(response);
    }
}
