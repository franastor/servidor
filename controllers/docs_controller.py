from flask import Response, request, render_template_string
from functools import wraps
import os
from dotenv import load_dotenv
from controllers.database import get_db_connection
import mysql.connector
from mysql.connector import Error

# Cargar variables de entorno
load_dotenv()

def check_auth(username, password):
    """Verifica las credenciales contra la base de datos."""
    try:
        connection = get_db_connection()
        if not connection:
            return False

        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM usuarios WHERE usuario = %s AND password = %s AND tiene_acceso_docs = 1"
        cursor.execute(query, (username, password))
        
        user = cursor.fetchone()
        cursor.close()
        connection.close()

        return user is not None

    except Error as e:
        print(f"Error en la base de datos: {str(e)}")
        return False
    except Exception as e:
        print(f"Error general: {str(e)}")
        return False

def authenticate():
    """Envía una respuesta 401 que permite al navegador mostrar el diálogo de autenticación básica."""
    return Response(
        'No autorizado', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

class DocsController:
    @staticmethod
    @requires_auth
    def get_docs():
        """Endpoint para obtener la documentación de la API."""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Documentación de la API</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                .endpoint {
                    background-color: white;
                    border-radius: 8px;
                    padding: 20px;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .method {
                    display: inline-block;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-weight: bold;
                    margin-right: 10px;
                }
                .get { background-color: #61affe; color: white; }
                .post { background-color: #49cc90; color: white; }
                .url {
                    font-family: monospace;
                    background-color: #f8f9fa;
                    padding: 4px 8px;
                    border-radius: 4px;
                }
                .description {
                    margin: 10px 0;
                    color: #666;
                }
                .section {
                    margin: 20px 0;
                }
                .section-title {
                    color: #333;
                    border-bottom: 2px solid #ddd;
                    padding-bottom: 10px;
                }
                .example {
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 4px;
                    margin: 10px 0;
                }
                .example pre {
                    margin: 0;
                    white-space: pre-wrap;
                }
                .response {
                    margin-top: 10px;
                    padding: 10px;
                    background-color: #e9ecef;
                    border-radius: 4px;
                }
                .note {
                    background-color: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 10px;
                    margin: 10px 0;
                }
                .error {
                    background-color: #f8d7da;
                    border-left: 4px solid #dc3545;
                    padding: 10px;
                    margin: 10px 0;
                }
            </style>
        </head>
        <body>
            <h1>Documentación de la API</h1>
            
            <div class="section">
                <h2 class="section-title">Información General</h2>
                <p>Esta API proporciona endpoints para autenticación y operaciones básicas. Todos los endpoints protegidos requieren un token JWT válido.</p>
            </div>

            <div class="section">
                <h2 class="section-title">Endpoints Disponibles</h2>

                <div class="endpoint">
                    <h3><span class="method post">POST</span> <span class="url">/login</span></h3>
                    <div class="description">Autenticación de usuario y obtención de token JWT</div>
                    
                    <h4>Request Body:</h4>
                    <div class="example">
                        <pre>{
    "usuario": "string",
    "password": "string"
}</pre>
                    </div>

                    <h4>Ejemplo de uso con curl:</h4>
                    <div class="example">
                        <pre>curl -X POST http://localhost:5001/login \\
     -H "Content-Type: application/json" \\
     -d '{"usuario": "usuario", "password": "contraseña"}'</pre>
                    </div>

                    <h4>Respuesta exitosa:</h4>
                    <div class="response">
                        <pre>{
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "mensaje": "Login exitoso",
    "usuario": "usuario"
}</pre>
                    </div>
                </div>

                <div class="endpoint">
                    <h3><span class="method get">GET</span> <span class="url">/inicio</span></h3>
                    <div class="description">Endpoint protegido que devuelve un mensaje de bienvenida</div>
                    
                    <h4>Headers requeridos:</h4>
                    <div class="example">
                        <pre>Authorization: Bearer &lt;token&gt;</pre>
                    </div>

                    <h4>Ejemplo de uso con curl:</h4>
                    <div class="example">
                        <pre>curl http://localhost:5001/inicio \\
     -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."</pre>
                    </div>

                    <h4>Respuesta exitosa:</h4>
                    <div class="response">
                        <pre>{
    "mensaje": "¡Bienvenido a la API!"
}</pre>
                    </div>
                </div>

                <div class="endpoint">
                    <h3><span class="method get">GET</span> <span class="url">/fin</span></h3>
                    <div class="description">Endpoint protegido que devuelve un mensaje de despedida</div>
                    
                    <h4>Headers requeridos:</h4>
                    <div class="example">
                        <pre>Authorization: Bearer &lt;token&gt;</pre>
                    </div>

                    <h4>Ejemplo de uso con curl:</h4>
                    <div class="example">
                        <pre>curl http://localhost:5001/fin \\
     -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."</pre>
                    </div>

                    <h4>Respuesta exitosa:</h4>
                    <div class="response">
                        <pre>{
    "mensaje": "¡Hasta luego!"
}</pre>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2 class="section-title">Notas Importantes</h2>
                <div class="note">
                    <p>• Todos los endpoints protegidos requieren un token JWT válido en el header de Authorization</p>
                    <p>• El token debe incluirse en el formato: <code>Bearer &lt;token&gt;</code></p>
                    <p>• Los tokens expiran después de un tiempo determinado</p>
                    <p>• En caso de error de autenticación, se devolverá un código 401</p>
                    <p>• Para acceder a la documentación, el usuario debe tener el campo 'tiene_acceso_docs' activado en la base de datos</p>
                </div>
            </div>

            <div class="section">
                <h2 class="section-title">Códigos de Estado</h2>
                <ul>
                    <li><strong>200:</strong> Operación exitosa</li>
                    <li><strong>400:</strong> Error en la solicitud (datos inválidos)</li>
                    <li><strong>401:</strong> No autorizado (token inválido o expirado)</li>
                    <li><strong>403:</strong> Acceso denegado (usuario sin permisos)</li>
                    <li><strong>404:</strong> Recurso no encontrado</li>
                    <li><strong>500:</strong> Error interno del servidor</li>
                </ul>
            </div>
        </body>
        </html>
        """
        return render_template_string(html_template) 