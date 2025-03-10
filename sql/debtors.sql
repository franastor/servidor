-- Crear tabla de deudores
CREATE TABLE IF NOT EXISTS debtors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    telefono VARCHAR(50),
    notas TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_nombre (nombre)
);

-- Modificar tabla de deudas para usar la nueva tabla de deudores
ALTER TABLE debts
    DROP COLUMN debtorName,
    ADD COLUMN debtor_id INT NOT NULL,
    ADD COLUMN invoice LONGBLOB,
    ADD FOREIGN KEY (debtor_id) REFERENCES debtors(id);

-- Crear índices
CREATE INDEX idx_debtor_nombre ON debtors(nombre);
CREATE INDEX idx_debt_debtor ON debts(debtor_id); 