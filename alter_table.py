from controllers.database import get_db_connection
from mysql.connector import Error

def alter_table():
    connection = get_db_connection()
    if connection is None:
        return
    
    try:
        cursor = connection.cursor()
        
        # Modificar la columna password
        cursor.execute("""
            ALTER TABLE usuarios 
            MODIFY COLUMN password VARCHAR(255) NOT NULL
        """)
        
        # Añadir columnas para archivos adjuntos
        cursor.execute("""
            ALTER TABLE expenses 
            ADD COLUMN invoice MEDIUMBLOB,
            ADD COLUMN invoice_name VARCHAR(255),
            ADD COLUMN invoice_type VARCHAR(10)
        """)
        
        connection.commit()
        print("Tabla modificada correctamente")
        
    except Error as e:
        print(f"Error: {e}")
        
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Conexión cerrada")

if __name__ == "__main__":
    alter_table() 