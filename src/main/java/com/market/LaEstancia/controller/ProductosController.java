package com.market.LaEstancia.controller;

import jakarta.servlet.http.HttpSession;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.sql.*;
import java.util.*;

@RestController
@RequestMapping("/api/productos")
public class ProductosController extends BaseController {

    @GetMapping
    public ResponseEntity<?> getProductos(HttpSession session) {
        List<Map<String, Object>> list = new ArrayList<>();
        String sql = "SELECT id_producto, nombre, categoria, precio, stock, id_proveedor FROM productos ORDER BY id_producto";
        
        try (Connection conn = getConnection(session);
             Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {
            
            while (rs.next()) {
                Map<String, Object> map = new HashMap<>();
                int id = rs.getInt("id_producto");
                map.put("code", "PRD-" + String.format("%03d", id));
                map.put("id", id);
                map.put("nombre", rs.getString("nombre"));
                map.put("categoria", rs.getString("categoria"));
                map.put("precio", rs.getDouble("precio"));
                map.put("stock", rs.getInt("stock"));
                map.put("id_proveedor", rs.getObject("id_proveedor"));
                list.add(map);
            }
            return ResponseEntity.ok(list);
            
        } catch (SQLException e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", "Error de Base de Datos: " + e.getMessage()));
        }
    }

    @PostMapping
    public ResponseEntity<?> createProducto(@RequestBody Map<String, Object> body, HttpSession session) {
        String sql = "INSERT INTO productos (nombre, categoria, precio, stock, id_proveedor) VALUES (?, ?, ?, ?, ?) RETURNING id_producto";
        
        try (Connection conn = getConnection(session);
             PreparedStatement ps = conn.prepareStatement(sql)) {
            
            ps.setString(1, (String) body.get("nombre"));
            ps.setString(2, (String) body.get("categoria"));
            ps.setBigDecimal(3, new java.math.BigDecimal(body.get("precio").toString()));
            ps.setInt(4, Integer.parseInt(body.get("stock").toString()));
            
            Object provObj = body.get("id_proveedor");
            if (provObj != null && !provObj.toString().isEmpty()) {
                ps.setInt(5, Integer.parseInt(provObj.toString()));
            } else {
                ps.setNull(5, Types.INTEGER);
            }
            
            try (ResultSet rs = ps.executeQuery()) {
                if (rs.next()) {
                    int newId = rs.getInt("id_producto");
                    body.put("id", newId);
                    body.put("code", "PRD-" + String.format("%03d", newId));
                    return ResponseEntity.ok(body);
                }
            }
            throw new SQLException("No se pudo obtener el ID del producto generado.");
            
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(Map.of("error", "Acceso Denegado por PostgreSQL: " + e.getMessage()));
        }
    }

    @PutMapping("/{id}")
    public ResponseEntity<?> updateProducto(@PathVariable int id, @RequestBody Map<String, Object> body, HttpSession session) {
        String sql = "UPDATE productos SET nombre = ?, categoria = ?, precio = ?, stock = ? WHERE id_producto = ?";
        
        try (Connection conn = getConnection(session);
             PreparedStatement ps = conn.prepareStatement(sql)) {
            
            ps.setString(1, (String) body.get("nombre"));
            ps.setString(2, (String) body.get("categoria"));
            ps.setBigDecimal(3, new java.math.BigDecimal(body.get("precio").toString()));
            ps.setInt(4, Integer.parseInt(body.get("stock").toString()));
            ps.setInt(5, id);
            
            int updated = ps.executeUpdate();
            if (updated > 0) {
                body.put("id", id);
                body.put("code", "PRD-" + String.format("%03d", id));
                return ResponseEntity.ok(body);
            } else {
                return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("error", "Producto no encontrado."));
            }
            
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(Map.of("error", "Acceso Denegado por PostgreSQL: " + e.getMessage()));
        }
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<?> deleteProducto(@PathVariable int id, HttpSession session) {
        String sql = "DELETE FROM productos WHERE id_producto = ?";
        
        try (Connection conn = getConnection(session);
             PreparedStatement ps = conn.prepareStatement(sql)) {
            
            ps.setInt(1, id);
            int deleted = ps.executeUpdate();
            
            if (deleted > 0) {
                return ResponseEntity.ok(Map.of("status", "deleted"));
            } else {
                return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("error", "Producto no encontrado."));
            }
            
        } catch (SQLException e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(Map.of("error", "Acceso Denegado por PostgreSQL: " + e.getMessage()));
        }
    }
}
