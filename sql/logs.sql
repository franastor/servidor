-- Crear tabla de logs
CREATE TABLE IF NOT EXISTS logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    accion VARCHAR(50) NOT NULL,
    tabla VARCHAR(50) NOT NULL,
    usuario VARCHAR(100) NOT NULL,
    ip VARCHAR(45) NOT NULL,
    dispositivo VARCHAR(255),
    detalles JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crear índices para mejorar el rendimiento de las consultas
CREATE INDEX idx_logs_accion ON logs(accion);
CREATE INDEX idx_logs_usuario ON logs(usuario);
CREATE INDEX idx_logs_fecha ON logs(created_at); 