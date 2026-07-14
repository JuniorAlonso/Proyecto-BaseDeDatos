package com.market.LaEstancia.controller;

import jakarta.servlet.http.HttpSession;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

public abstract class BaseController {

    protected Connection getConnection(HttpSession session) throws SQLException {
        String dbUser = (String) session.getAttribute("dbUser");
        String dbPass = (String) session.getAttribute("dbPass");
        
        if (dbUser == null || dbPass == null) {
            throw new SQLException("No hay una sesion activa de base de datos. Por favor, inicie sesion.");
        }
        
        // Retorna una conexion fisica utilizando las credenciales del usuario de la sesion
        return DriverManager.getConnection("jdbc:postgresql://localhost:5432/marketDB", dbUser, dbPass);
    }
}
