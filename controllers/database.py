import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Verificar que las variables de entorno están cargadas
required_env_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
for var in required_env_vars:
    value = os.getenv(var)
    if not value:
        raise ValueError(f"Variable de entorno {var} no encontrada")
    logger.info(f"Variable {var} cargada correctamente")

# Configuración de la base de datos
db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'port': 3306,  # Puerto por defecto de MySQL
    'raise_on_warnings': True,
    'connection_timeout': 10
}

def get_db_connection():
    try:
        logger.info(f"Intentando conectar a la base de datos en {db_config['host']}")
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            db_info = connection.get_server_info()
            logger.info(f"Conectado a MySQL versión {db_info}")
            return connection
    except Error as e:
        logger.error(f"Error al conectar a la base de datos: {e}")
        return None 