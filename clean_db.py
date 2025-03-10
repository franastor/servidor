import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'gastos')
}

try:
    connection = mysql.connector.connect(**db_config)
    
    if connection.is_connected():
        cursor = connection.cursor()
        
        # Eliminar tablas existentes
        tables = ['expenses', 'debts', 'roles_permisos', 'usuarios', 'roles', 'permisos']
        for table in tables:
            try:
                cursor.execute(f'DROP TABLE IF EXISTS {table}')
                print(f'✓ Tabla {table} eliminada')
            except Error as e:
                print(f'✗ Error al eliminar tabla {table}: {e}')
        
        # Crear tabla usuarios
        cursor.execute('''
            CREATE TABLE usuarios (
                id INT AUTO_INCREMENT PRIMARY KEY,
                usuario VARCHAR(100) NOT NULL UNIQUE,
                password VARCHAR(100) NOT NULL,
                nombre VARCHAR(100),
                email VARCHAR(100) UNIQUE,
                rol_id INT,
                activo BOOLEAN DEFAULT true,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print('✓ Tabla usuarios creada')
        
        connection.commit()
        print('✓ Base de datos limpiada correctamente')
        
except Error as e:
    print(f'✗ Error: {e}')
finally:
    if connection and connection.is_connected():
        cursor.close()
        connection.close()
        print('✓ Conexión cerrada') 