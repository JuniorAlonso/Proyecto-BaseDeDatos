package com.market.LaEstancia.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpSession;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.sql.*;
import java.util.*;

@RestController
@RequestMapping("/api/ventas")
public class VentasController extends BaseController {

    private final ObjectMapper objectMapper = new ObjectMapper();

    @GetMapping
    public ResponseEntity<?> getVentas(HttpSession session) {
        List<Map<String, Object>> list = new ArrayList<>();
        String sql = "SELECT v.id_venta, v.id_usuario, v.id_cliente, v.fecha_venta, v.total, v.voucher, v.status, " +
                     "v.payment_method, v.items, u.username as cashier " +
                     "FROM ventas v " +
                     "JOIN usuarios u ON v.id_usuario = u.id_usuario " +
                     "ORDER BY v.id_venta DESC";
        
        try (Connection conn = getConnection(session);
             Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {
            
            while (rs.next()) {
                Map<String, Object> map = new HashMap<>();
                int id = rs.getInt("id_venta");
                map.put("id", "VTA-" + String.format("%03d", id));
                map.put("voucher", rs.getString("voucher"));
                map.put("cashier", rs.getString("cashier"));
                map.put("total", rs.getDouble("total"));
                map.put("status", rs.getString("status"));
                map.put("paymentMethod", rs.getString("payment_method"));
                map.put("createdAt", rs.getTimestamp("fecha_venta").toInstant().toString());
                
                String jsonItems = rs.getString("items");
                if (jsonItems != null && !jsonItems.isEmpty()) {
                    try {
                        map.put("items", objectMapper.readValue(jsonItems, List.class));
                    } catch (Exception ex) {
                        map.put("items", new ArrayList<>());
                    }
                } else {
                    map.put("items", new ArrayList<>());
                }
                list.add(map);
            }
            return ResponseEntity.ok(list);
            
        } catch (SQLException e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", "Error de Base de Datos: " + e.getMessage()));
        }
    }

    @PostMapping
    public ResponseEntity<?> createVenta(@RequestBody Map<String, Object> body, HttpSession session) {
        String sql = "INSERT INTO ventas (id_usuario, id_cliente, total, voucher, status, payment_method, items) " +
                     "VALUES (?, ?, ?, ?, ?, ?, ?::jsonb) RETURNING id_venta, fecha_venta";
        
        try (Connection conn = getConnection(session)) {
            // 1. Determinar el id_usuario correspondiente en la aplicacion
            String dbUser = (String) session.getAttribute("dbUser");
            int appUserId = 3; // carlos_cajero por defecto
            if ("administrador".equalsIgnoreCase(dbUser) || "admin".equalsIgnoreCase(dbUser)) {
                appUserId = 1; // juan_admin
            } else if ("supervisor".equalsIgnoreCase(dbUser)) {
                appUserId = 2; // ana_supervisor
            }
            
            // 2. Resolver el ID del cliente o dejarlo NULL
            Integer clienteId = null;
            Object cliObj = body.get("id_cliente");
            if (cliObj != null && !cliObj.toString().isEmpty()) {
                clienteId = Integer.parseInt(cliObj.toString());
            }
            
            // 3. Obtener el numero de voucher correlativo
            String voucherType = "BOL-";
            if (clienteId != null) {
                // Si tiene cliente registrado, supongamos que es factura
                voucherType = "FAC-";
            }
            
            String countSql = "SELECT COUNT(*) + 1 as next_val FROM ventas";
            int nextVal = 1001;
            try (Statement countStmt = conn.createStatement();
                 ResultSet countRs = countStmt.executeQuery(countSql)) {
                if (countRs.next()) {
                    nextVal = 1450 + countRs.getInt("next_val");
                }
            }
            String voucherCode = voucherType + nextVal;
            
            // 4. Obtener total e items
            double total = Double.parseDouble(body.get("total").toString());
            String paymentMethod = body.get("paymentMethod") != null ? body.get("paymentMethod").toString() : "Efectivo";
            List<?> itemsList = (List<?>) body.get("items");
            String itemsJson = objectMapper.writeValueAsString(itemsList);
            
            // 5. Ejecutar la insercion
            try (PreparedStatement ps = conn.prepareStatement(sql)) {
                ps.setInt(1, appUserId);
                if (clienteId != null) {
                    ps.setInt(2, clienteId);
                } else {
                    ps.setNull(2, Types.INTEGER);
                }
                ps.setBigDecimal(3, new java.math.BigDecimal(String.valueOf(total)));
                ps.setString(4, voucherCode);
                ps.setString(5, "Completado");
                ps.setString(6, paymentMethod);
                ps.setString(7, itemsJson);
                
                try (ResultSet rs = ps.executeQuery()) {
                    if (rs.next()) {
                        int newId = rs.getInt("id_venta");
                        Timestamp createdAt = rs.getTimestamp("fecha_venta");
                        
                        Map<String, Object> response = new HashMap<>(body);
                        response.put("id", "VTA-" + String.format("%03d", newId));
                        response.put("voucher", voucherCode);
                        response.put("createdAt", createdAt.toInstant().toString());
                        response.put("status", "Completado");
                        return ResponseEntity.ok(response);
                    }
                }
            }
            throw new SQLException("No se pudo registrar la venta.");
            
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(Map.of("error", "Acceso Denegado por PostgreSQL: " + e.getMessage()));
        }
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<?> deleteVenta(@PathVariable String id, HttpSession session) {
        // Extraer la parte numerica del ID, ej. VTA-003 -> 3
        int numId;
        try {
            numId = Integer.parseInt(id.replace("VTA-", ""));
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(Map.of("error", "Formato de ID invalido."));
        }
        
        String sql = "DELETE FROM ventas WHERE id_venta = ?";
        try (Connection conn = getConnection(session);
             PreparedStatement ps = conn.prepareStatement(sql)) {
            
            ps.setInt(1, numId);
            int deleted = ps.executeUpdate();
            
            if (deleted > 0) {
                return ResponseEntity.ok(Map.of("status", "deleted"));
            } else {
                return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("error", "Venta no encontrada."));
            }
            
        } catch (SQLException e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(Map.of("error", "Acceso Denegado por PostgreSQL: " + e.getMessage()));
        }
    }
}
