import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

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

def setup_database():
    connection = get_db_connection()
    if connection is None:
        return
    
    try:
        cursor = connection.cursor()
        
        # Crear tabla de gastos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                amount DECIMAL(10,2) NOT NULL,
                category VARCHAR(50) NOT NULL,
                description TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INT NOT NULL,
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        
        connection.commit()
        print("Base de datos actualizada correctamente")
        
    except Error as e:
        print(f"Error: {e}")
        
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Conexión cerrada")

if __name__ == "__main__":
    setup_database() 