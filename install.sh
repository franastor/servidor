#!/bin/bash

# Detener en caso de error
set -e

echo "🚀 Iniciando instalación del backend..."

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no está instalado. Por favor, instálalo antes de continuar."
    exit 1
fi

# Verificar pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 no está instalado. Instalando..."
    python3 -m ensurepip --upgrade
fi

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "🔧 Creando entorno virtual..."
    python3 -m venv venv
fi

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source venv/bin/activate

# Instalar dependencias
echo "📥 Instalando dependencias..."
pip install -r requirements.txt

# Crear archivo .env si no existe
if [ ! -f .env ]; then
    echo "🔧 Creando archivo .env..."
    cat > .env << EOL
# Configuración de la base de datos
DB_HOST=hq1m.your-database.de
DB_USER=jatines
DB_PASSWORD=bDzSCm2ST1aPZGtP
DB_NAME=franas_db1

# Configuración de JWT
JWT_SECRET_KEY=tu-clave-secreta-aqui
MASTER_TOKEN=test_master_token_123

# Configuración de correo Hetzner
HETZNER_EMAIL=admin@franastor.com
HETZNER_PASSWORD=rIU%ii$45DAaab
EOL
fi

# Verificar conexión a la base de datos
echo "🔍 Verificando conexión a la base de datos..."
python3 -c "
from dotenv import load_dotenv
import os
import mysql.connector
load_dotenv()
try:
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
    if conn.is_connected():
        print('✅ Conexión exitosa a la base de datos')
        conn.close()
except Exception as e:
    print('❌ Error al conectar a la base de datos:', str(e))
    exit(1)
"

echo "✅ Instalación completada con éxito!"
echo "
Para iniciar el servidor:
  source venv/bin/activate  # Si no está activado
  python3 app.py

El servidor se ejecutará en:
  http://localhost:5001
" 