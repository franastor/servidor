import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'port': 3306
}

try:
    connection = mysql.connector.connect(**db_config)
    
    if connection.is_connected():
        cursor = connection.cursor()
        
        # Crear tabla logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                accion VARCHAR(50) NOT NULL,
                tabla VARCHAR(50) NOT NULL,
                usuario VARCHAR(100) NOT NULL,
                ip VARCHAR(45) NOT NULL,
                dispositivo VARCHAR(255),
                detalles JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Crear índices
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_accion ON logs(accion)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_usuario ON logs(usuario)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_fecha ON logs(created_at)')
        
        connection.commit()
        print('✓ Tabla logs y sus índices creados correctamente')
        
except Error as e:
    print(f'✗ Error: {e}')
finally:
    if connection and connection.is_connected():
        cursor.close()
        connection.close()
        print('✓ Conexión cerrada') 