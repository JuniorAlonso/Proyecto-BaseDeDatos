package com.market.LaEstancia.controller;

import jakarta.servlet.http.HttpSession;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.sql.*;
import java.util.*;

@RestController
@RequestMapping("/api/clientes")
public class ClientesController extends BaseController {

    @GetMapping
    public ResponseEntity<?> getClientes(HttpSession session) {
        List<Map<String, Object>> list = new ArrayList<>();
        String sql = "SELECT id_cliente, nombre_completo, " +
                     "pgp_sym_decrypt(dni, 'llave_secreta_estancia') AS dni, " +
                     "pgp_sym_decrypt(email, 'llave_secreta_estancia') AS email, " +
                     "pgp_sym_decrypt(telefono, 'llave_secreta_estancia') AS telefono, " +
                     "puntos FROM clientes ORDER BY id_cliente";
        
        try (Connection conn = getConnection(session);
             Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {
            
            while (rs.next()) {
                Map<String, Object> map = new HashMap<>();
                map.put("id", rs.getInt("id_cliente"));
                map.put("documento", rs.getString("dni"));
                map.put("nombre", rs.getString("nombre_completo"));
                map.put("telefono", rs.getString("telefono"));
                map.put("correo", rs.getString("email"));
                map.put("puntos", rs.getInt("puntos"));
                list.add(map);
            }
            return ResponseEntity.ok(list);
            
        } catch (SQLException e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", "Error de Base de Datos: " + e.getMessage()));
        }
    }

    @PostMapping
    public ResponseEntity<?> createCliente(@RequestBody Map<String, Object> body, HttpSession session) {
        String sql = "INSERT INTO clientes (nombre_completo, dni, email, telefono, puntos) " +
                     "VALUES (?, pgp_sym_encrypt(?, 'llave_secreta_estancia'), pgp_sym_encrypt(?, 'llave_secreta_estancia'), pgp_sym_encrypt(?, 'llave_secreta_estancia'), ?) RETURNING id_cliente";
        
        try (Connection conn = getConnection(session);
             PreparedStatement ps = conn.prepareStatement(sql)) {
            
            ps.setString(1, (String) body.get("nombre"));
            ps.setString(2, (String) body.get("documento"));
            ps.setString(3, (String) body.get("correo"));
            ps.setString(4, (String) body.get("telefono"));
            
            Object pts = body.get("puntos");
            ps.setInt(5, pts != null && !pts.toString().isEmpty() ? Integer.parseInt(pts.toString()) : 0);
            
            try (ResultSet rs = ps.executeQuery()) {
                if (rs.next()) {
                    body.put("id", rs.getInt("id_cliente"));
                    return ResponseEntity.ok(body);
                }
            }
            throw new SQLException("No se pudo obtener el ID del cliente generado.");
            
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(Map.of("error", "Acceso Denegado por PostgreSQL: " + e.getMessage()));
        }
    }

    @PutMapping("/{id}")
    public ResponseEntity<?> updateCliente(@PathVariable int id, @RequestBody Map<String, Object> body, HttpSession session) {
        String sql = "UPDATE clientes SET nombre_completo = ?, " +
                     "dni = pgp_sym_encrypt(?, 'llave_secreta_estancia'), " +
                     "email = pgp_sym_encrypt(?, 'llave_secreta_estancia'), " +
                     "telefono = pgp_sym_encrypt(?, 'llave_secreta_estancia'), " +
                     "puntos = ? WHERE id_cliente = ?";
        
        try (Connection conn = getConnection(session);
             PreparedStatement ps = conn.prepareStatement(sql)) {
            
            ps.setString(1, (String) body.get("nombre"));
            ps.setString(2, (String) body.get("documento"));
            ps.setString(3, (String) body.get("correo"));
            ps.setString(4, (String) body.get("telefono"));
            
            Object pts = body.get("puntos");
            ps.setInt(5, pts != null && !pts.toString().isEmpty() ? Integer.parseInt(pts.toString()) : 0);
            ps.setInt(6, id);
            
            int updated = ps.executeUpdate();
            if (updated > 0) {
                body.put("id", id);
                return ResponseEntity.ok(body);
            } else {
                return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("error", "Cliente no encontrado."));
            }
            
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(Map.of("error", "Acceso Denegado por PostgreSQL: " + e.getMessage()));
        }
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<?> deleteCliente(@PathVariable int id, HttpSession session) {
        String sql = "DELETE FROM clientes WHERE id_cliente = ?";
        
        try (Connection conn = getConnection(session);
             PreparedStatement ps = conn.prepareStatement(sql)) {
            
            ps.setInt(1, id);
            int deleted = ps.executeUpdate();
            
            if (deleted > 0) {
                return ResponseEntity.ok(Map.of("status", "deleted"));
            } else {
                return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("error", "Cliente no encontrado."));
            }
            
        } catch (SQLException e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(Map.of("error", "Acceso Denegado por PostgreSQL: " + e.getMessage()));
        }
    }
}
