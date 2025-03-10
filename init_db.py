import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# Cargar variables de entorno
load_dotenv()

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        return connection
    except Error as e:
        print(f"Error al conectar a MySQL: {e}")
        return None

def init_database():
    connection = get_db_connection()
    if connection is None:
        return
    
    try:
        cursor = connection.cursor()
        
        # Crear tabla de roles
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(50) NOT NULL UNIQUE,
                descripcion TEXT
            )
        """)
        
        # Crear tabla de permisos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS permisos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(50) NOT NULL UNIQUE,
                descripcion TEXT
            )
        """)
        
        # Crear tabla de relación roles-permisos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS roles_permisos (
                rol_id INT,
                permiso_id INT,
                PRIMARY KEY (rol_id, permiso_id),
                FOREIGN KEY (rol_id) REFERENCES roles(id) ON DELETE CASCADE,
                FOREIGN KEY (permiso_id) REFERENCES permisos(id) ON DELETE CASCADE
            )
        """)
        
        # Crear tabla de usuarios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INT AUTO_INCREMENT PRIMARY KEY,
                usuario VARCHAR(100) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                nombre VARCHAR(100),
                email VARCHAR(100) UNIQUE,
                rol_id INT,
                activo BOOLEAN DEFAULT true,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (rol_id) REFERENCES roles(id)
            )
        """)
        
        # Crear tabla de gastos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                amount DECIMAL(10,2) NOT NULL,
                category VARCHAR(50) NOT NULL,
                description TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INT NOT NULL,
                invoice MEDIUMBLOB,
                invoice_name VARCHAR(255),
                invoice_type VARCHAR(10),
                FOREIGN KEY (user_id) REFERENCES usuarios(id)
            )
        """)
        
        # Crear tabla de deudores
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS debtors (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                email VARCHAR(100),
                telefono VARCHAR(20),
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Crear tabla de deudas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS debts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                amount DECIMAL(10,2) NOT NULL,
                description TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                isPaid BOOLEAN DEFAULT FALSE,
                user_id INT NOT NULL,
                debtor_id INT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES usuarios(id),
                FOREIGN KEY (debtor_id) REFERENCES debtors(id)
            )
        """)

        # Crear tabla de logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                accion VARCHAR(50) NOT NULL,
                tabla VARCHAR(50) NOT NULL,
                usuario VARCHAR(100) NOT NULL,
                ip VARCHAR(45),
                dispositivo TEXT,
                detalles JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insertar roles básicos
        cursor.execute("""
            INSERT IGNORE INTO roles (nombre, descripcion) VALUES
            ('admin', 'Administrador con acceso total'),
            ('usuario', 'Usuario estándar'),
            ('invitado', 'Usuario con acceso limitado')
        """)
        
        # Insertar permisos básicos
        cursor.execute("""
            INSERT IGNORE INTO permisos (nombre, descripcion) VALUES
            ('ver_gastos', 'Puede ver gastos'),
            ('crear_gastos', 'Puede crear nuevos gastos'),
            ('editar_gastos', 'Puede editar gastos existentes'),
            ('eliminar_gastos', 'Puede eliminar gastos'),
            ('ver_deudas', 'Puede ver deudas'),
            ('crear_deudas', 'Puede crear nuevas deudas'),
            ('editar_deudas', 'Puede editar deudas existentes'),
            ('eliminar_deudas', 'Puede eliminar deudas'),
            ('gestionar_usuarios', 'Puede gestionar usuarios'),
            ('ver_logs', 'Puede ver los logs del sistema')
        """)
        
        # Asignar permisos a roles
        cursor.execute("""
            INSERT IGNORE INTO roles_permisos (rol_id, permiso_id)
            SELECT r.id, p.id
            FROM roles r, permisos p
            WHERE r.nombre = 'admin'
        """)
        
        cursor.execute("""
            INSERT IGNORE INTO roles_permisos (rol_id, permiso_id)
            SELECT r.id, p.id
            FROM roles r, permisos p
            WHERE r.nombre = 'usuario' 
            AND p.nombre IN ('ver_gastos', 'crear_gastos', 'ver_deudas', 'crear_deudas')
        """)
        
        cursor.execute("""
            INSERT IGNORE INTO roles_permisos (rol_id, permiso_id)
            SELECT r.id, p.id
            FROM roles r, permisos p
            WHERE r.nombre = 'invitado' 
            AND p.nombre IN ('ver_gastos', 'ver_deudas')
        """)
        
        # Crear usuario admin
        admin_password = generate_password_hash(os.getenv('ADMIN_PASSWORD'))
        print(f"Hash generado para la contraseña: {admin_password}")
        cursor.execute("""
            INSERT IGNORE INTO usuarios (usuario, password, nombre, email, rol_id)
            SELECT %s, %s, %s, %s, id
            FROM roles WHERE nombre = 'admin'
        """, (os.getenv('ADMIN_USER'), admin_password, 'Administrador', os.getenv('ADMIN_EMAIL')))
        
        # Crear usuario de prueba
        prueba_password = generate_password_hash('prueba')
        cursor.execute("""
            INSERT IGNORE INTO usuarios (usuario, password, nombre, rol_id)
            SELECT 'prueba', %s, 'Usuario Prueba', id
            FROM roles WHERE nombre = 'usuario'
        """, (prueba_password,))
        
        connection.commit()
        print("Base de datos inicializada correctamente")
        
    except Error as e:
        print(f"Error: {e}")
        
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Conexión cerrada")

if __name__ == "__main__":
    init_database() 