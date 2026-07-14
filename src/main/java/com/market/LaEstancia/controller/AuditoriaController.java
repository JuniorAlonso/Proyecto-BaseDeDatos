package com.market.LaEstancia.controller;

import jakarta.servlet.http.HttpSession;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.sql.*;
import java.util.*;

@RestController
@RequestMapping("/api/auditoria")
public class AuditoriaController extends BaseController {

    @GetMapping
    public ResponseEntity<?> getAuditoriaLogs(HttpSession session) {
        List<Map<String, Object>> list = new ArrayList<>();
        String sql = "SELECT id_log, tabla_afectada, operacion, usuario_db, fecha_hora, valor_anterior, valor_nuevo " +
                     "FROM auditoria_logs " +
                     "ORDER BY id_log DESC";
        
        try (Connection conn = getConnection(session);
             Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {
            
            while (rs.next()) {
                Map<String, Object> map = new HashMap<>();
                int id = rs.getInt("id_log");
                map.put("id", "LOG-" + String.format("%03d", id));
                map.put("createdAt", rs.getTimestamp("fecha_hora").toInstant().toString());
                map.put("user", rs.getString("usuario_db"));
                map.put("action", rs.getString("operacion"));
                
                String tabla = rs.getString("tabla_afectada");
                String valAnt = rs.getString("valor_anterior");
                String valNue = rs.getString("valor_nuevo");
                
                String detail = "Operacion en tabla '" + tabla + "'";
                if (valNue != null && !valNue.isEmpty()) {
                    detail += " | Registro: " + valNue;
                } else if (valAnt != null && !valAnt.isEmpty()) {
                    detail += " | Borrado: " + valAnt;
                }
                
                map.put("detail", detail);
                list.add(map);
            }
            return ResponseEntity.ok(list);
            
        } catch (SQLException e) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body(Map.of("error", "Acceso Denegado por PostgreSQL: " + e.getMessage()));
        }
    }
}
