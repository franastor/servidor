-- Tabla de roles
CREATE TABLE IF NOT EXISTS roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT
);

-- Tabla de permisos
CREATE TABLE IF NOT EXISTS permisos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT
);

-- Tabla de relación roles-permisos
CREATE TABLE IF NOT EXISTS roles_permisos (
    rol_id INT,
    permiso_id INT,
    PRIMARY KEY (rol_id, permiso_id),
    FOREIGN KEY (rol_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permiso_id) REFERENCES permisos(id) ON DELETE CASCADE
);

-- Modificar la tabla usuarios existente
ALTER TABLE usuarios
ADD COLUMN nombre VARCHAR(100),
ADD COLUMN email VARCHAR(100) UNIQUE,
ADD COLUMN rol_id INT,
ADD COLUMN activo BOOLEAN DEFAULT true,
ADD COLUMN fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD FOREIGN KEY (rol_id) REFERENCES roles(id);

-- Insertar roles básicos
INSERT INTO roles (nombre, descripcion) VALUES
('admin', 'Administrador con acceso total'),
('usuario', 'Usuario estándar'),
('invitado', 'Usuario con acceso limitado');

-- Insertar permisos básicos
INSERT INTO permisos (nombre, descripcion) VALUES
('ver_gastos', 'Puede ver gastos'),
('crear_gastos', 'Puede crear nuevos gastos'),
('editar_gastos', 'Puede editar gastos existentes'),
('eliminar_gastos', 'Puede eliminar gastos'),
('ver_deudas', 'Puede ver deudas'),
('crear_deudas', 'Puede crear nuevas deudas'),
('editar_deudas', 'Puede editar deudas existentes'),
('eliminar_deudas', 'Puede eliminar deudas'),
('gestionar_usuarios', 'Puede gestionar usuarios');

-- Asignar permisos a roles
INSERT INTO roles_permisos (rol_id, permiso_id)
SELECT r.id, p.id
FROM roles r, permisos p
WHERE r.nombre = 'admin';

INSERT INTO roles_permisos (rol_id, permiso_id)
SELECT r.id, p.id
FROM roles r, permisos p
WHERE r.nombre = 'usuario' 
AND p.nombre IN ('ver_gastos', 'crear_gastos', 'ver_deudas', 'crear_deudas');

INSERT INTO roles_permisos (rol_id, permiso_id)
SELECT r.id, p.id
FROM roles r, permisos p
WHERE r.nombre = 'invitado' 
AND p.nombre IN ('ver_gastos', 'ver_deudas');

-- Actualizar usuario existente como admin
UPDATE usuarios 
SET rol_id = (SELECT id FROM roles WHERE nombre = 'admin'),
    nombre = 'Administrador',
    email = 'admin@example.com'
WHERE usuario = 'franastor';

-- Insertar algunos usuarios de ejemplo
INSERT INTO usuarios (usuario, password, nombre, email, rol_id) VALUES
('usuario1', 'password1', 'Usuario Normal', 'usuario1@example.com', (SELECT id FROM roles WHERE nombre = 'usuario')),
('invitado1', 'password1', 'Usuario Invitado', 'invitado1@example.com', (SELECT id FROM roles WHERE nombre = 'invitado')); 