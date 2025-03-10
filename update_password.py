from controllers.database import get_db_connection
from werkzeug.security import generate_password_hash
from mysql.connector import Error

def update_password():
    connection = get_db_connection()
    if connection is None:
        return
    
    try:
        cursor = connection.cursor()
        
        # Generar hash de la contraseña
        password_hash = generate_password_hash('pepito')
        
        # Actualizar la contraseña
        cursor.execute("""
            UPDATE usuarios 
            SET password = %s
            WHERE usuario = 'franastor'
        """, (password_hash,))
        
        connection.commit()
        print("Contraseña actualizada correctamente")
        
    except Error as e:
        print(f"Error: {e}")
        
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Conexión cerrada")

if __name__ == "__main__":
    update_password() 