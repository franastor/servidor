from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from controllers.database import get_db_connection
from mysql.connector import Error
from controllers.log_controller import LogController
from utils.auth import admin_required
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import logging
import re

load_dotenv()

logger = logging.getLogger(__name__)

class UserController:
    @staticmethod
    def normalize_username(username: str) -> str:
        """Normaliza el nombre de usuario para comparaciones."""
        return username.lower().strip()

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Valida que el email tenga un formato correcto."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def check_user_exists(cursor, username: str, email: str = None) -> tuple[bool, str]:
        """
        Verifica si el usuario o email ya existen en la base de datos.
        Retorna una tupla (existe, mensaje)
        """
        # Verificar usuario
        cursor.execute("""
            SELECT usuario 
            FROM usuarios 
            WHERE LOWER(usuario) = LOWER(%s)
        """, (username,))
        
        result = cursor.fetchone()
        if result:
            return True, "Ya existe un usuario con ese nombre"

        # Verificar email si se proporciona
        if email:
            cursor.execute("""
                SELECT email 
                FROM usuarios 
                WHERE LOWER(email) = LOWER(%s)
            """, (email,))
            
            result = cursor.fetchone()
            if result:
                return True, "Ya existe un usuario con ese email"
        
        return False, ""

    @staticmethod
    @jwt_required()
    def get_users():
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT u.id, u.usuario, u.nombre, u.email, u.activo,
                       r.nombre as rol, r.descripcion as rol_descripcion
                FROM usuarios u
                LEFT JOIN roles r ON r.id = u.rol_id
                ORDER BY u.usuario
            """)
            
            users = cursor.fetchall()
            cursor.close()
            connection.close()
            
            return jsonify({
                'usuarios': users
            }), 200
            
        except Error as e:
            print(f"Error al obtener usuarios: {str(e)}")
            return jsonify({
                'message': 'Error interno del servidor',
                'error': str(e)
            }), 500

    @staticmethod
    @jwt_required()
    @admin_required
    def toggle_user_status(user_id):
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            # Obtener el estado actual del usuario
            cursor.execute("""
                SELECT u.id, u.usuario, u.activo, u.rol_id 
                FROM usuarios u 
                WHERE u.id = %s
            """, (user_id,))
            
            user = cursor.fetchone()
            if not user:
                return jsonify({
                    'error': 'Usuario no encontrado',
                    'detalles': f'No existe un usuario con el ID {user_id}'
                }), 404

            # Verificar que no sea el usuario admin principal
            if user['rol_id'] == 1 and user['usuario'] == 'franastor':
                return jsonify({
                    'error': 'Operación no permitida',
                    'detalles': 'No se puede bloquear al usuario administrador principal'
                }), 403
            
            # Cambiar el estado
            new_status = not user['activo']
            cursor.execute("""
                UPDATE usuarios SET activo = %s WHERE id = %s
            """, (new_status, user_id))
            
            connection.commit()
            
            # Registrar la acción
            admin_id = get_jwt_identity()
            LogController.log_action(
                accion='bloquear' if not new_status else 'desbloquear',
                tabla='usuarios',
                usuario=admin_id,
                detalles={
                    'user_id': user_id,
                    'usuario': user['usuario'],
                    'nuevo_estado': new_status
                }
            )
            
            cursor.close()
            connection.close()
            
            return jsonify({
                'mensaje': f"Usuario {'bloqueado' if not new_status else 'desbloqueado'} correctamente",
                'detalles': {
                    'usuario': user['usuario'],
                    'activo': new_status
                }
            }), 200
            
        except Error as e:
            print(f"Error al cambiar estado del usuario: {str(e)}")
            return jsonify({
                'error': 'Error en la base de datos',
                'detalles': str(e)
            }), 500
        except Exception as e:
            print(f"Error inesperado: {str(e)}")
            return jsonify({
                'error': 'Error inesperado',
                'detalles': str(e)
            }), 500

    @staticmethod
    def generate_password(length: int = 12) -> str:
        """Genera una contraseña aleatoria segura."""
        # Definir los caracteres que se usarán
        letters = string.ascii_letters
        digits = string.digits
        special_chars = "!@#$%^&*"
        
        # Asegurar al menos un carácter de cada tipo
        password = [
            secrets.choice(letters.lower()),
            secrets.choice(letters.upper()),
            secrets.choice(digits),
            secrets.choice(special_chars)
        ]
        
        # Completar el resto de la contraseña
        all_chars = letters + digits + special_chars
        password.extend(secrets.choice(all_chars) for _ in range(length - 4))
        
        # Mezclar la contraseña
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)

    @staticmethod
    def send_welcome_email(email: str, username: str, password: str) -> bool:
        """Envía un correo de bienvenida al usuario con sus credenciales."""
        try:
            smtp_server = "mail.your-server.de"
            smtp_port = 587
            sender_email = os.getenv('HETZNER_EMAIL')
            sender_password = os.getenv('HETZNER_PASSWORD')

            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = email
            msg['Subject'] = "Bienvenido - Credenciales de acceso"

            html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #2c3e50;">¡Bienvenido al sistema!</h2>
                        <p>Se ha creado una cuenta para ti con las siguientes credenciales:</p>
                        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <p><strong>Usuario:</strong> {username}</p>
                            <p><strong>Contraseña:</strong> {password}</p>
                        </div>
                        <p>Por favor, cambia tu contraseña la primera vez que inicies sesión.</p>
                        <p style="color: #e74c3c;"><strong>Importante:</strong> No compartas estas credenciales con nadie.</p>
                    </div>
                </body>
            </html>
            """

            msg.attach(MIMEText(html, 'html'))

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)

            return True
        except Exception as e:
            print(f"Error al enviar email: {str(e)}")
            return False

    @staticmethod
    @jwt_required()
    def create_user():
        try:
            current_user = get_jwt_identity()
            data = request.get_json()
            
            # Validar que se recibió data
            if not data:
                return jsonify({
                    "error": "No se recibieron datos",
                    "detalles": "El cuerpo de la petición está vacío"
                }), 400

            # Validar campos requeridos
            required_fields = ['usuario', 'nombre', 'email', 'rol']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return jsonify({
                    "error": "Faltan campos requeridos",
                    "detalles": f"Los siguientes campos son obligatorios: {', '.join(missing_fields)}"
                }), 400

            # Validar formato de email
            if not UserController.is_valid_email(data['email']):
                return jsonify({
                    "error": "Email inválido",
                    "detalles": "El formato del email no es válido. Debe ser ejemplo@dominio.com"
                }), 400

            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            try:
                # Verificar permisos
                cursor.execute("""
                    SELECT COUNT(*) as tiene_permiso
                    FROM usuarios u
                    JOIN roles_permisos rp ON u.rol_id = rp.rol_id
                    JOIN permisos p ON rp.permiso_id = p.id
                    WHERE u.usuario = %s AND p.nombre = 'gestionar_usuarios'
                """, (current_user,))
                
                result = cursor.fetchone()
                if not result or result['tiene_permiso'] == 0:
                    LogController.log_action(
                        accion='acceso_denegado',
                        tabla='usuarios',
                        usuario=current_user,
                        detalles={
                            'accion_intentada': 'crear_usuario',
                            'razon': 'Sin permiso'
                        }
                    )
                    return jsonify({
                        "error": "Permiso denegado",
                        "detalles": "No tienes los permisos necesarios para crear usuarios"
                    }), 403

                # Verificar usuario y email duplicados
                exists, message = UserController.check_user_exists(cursor, data['usuario'], data['email'])
                if exists:
                    LogController.log_action(
                        accion='crear_usuario_fallido',
                        tabla='usuarios',
                        usuario=current_user,
                        detalles={
                            'usuario_intentado': data['usuario'],
                            'email_intentado': data['email'],
                            'razon': message
                        }
                    )
                    return jsonify({
                        "error": "Usuario o email duplicado",
                        "detalles": message
                    }), 400

                # Obtener el ID del rol
                cursor.execute("SELECT id, nombre FROM roles WHERE nombre = %s", (data['rol'],))
                rol = cursor.fetchone()
                if not rol:
                    LogController.log_action(
                        accion='crear_usuario_fallido',
                        tabla='usuarios',
                        usuario=current_user,
                        detalles={
                            'usuario_intentado': data['usuario'],
                            'rol_intentado': data['rol'],
                            'razon': 'Rol no existe'
                        }
                    )
                    return jsonify({
                        "error": "Rol inválido",
                        "detalles": f"El rol '{data['rol']}' no existe en el sistema"
                    }), 400

                # Generar o usar la contraseña proporcionada
                password = data.get('password')
                if not password:
                    password = UserController.generate_password()

                # Hashear la contraseña
                hashed_password = generate_password_hash(password)

                # Crear usuario
                cursor.execute("""
                    INSERT INTO usuarios (usuario, password, nombre, email, rol_id, activo)
                    VALUES (%s, %s, %s, %s, %s, true)
                """, (data['usuario'], hashed_password, data['nombre'], data['email'], rol['id']))
                
                connection.commit()

                # Enviar email con las credenciales
                email_sent = UserController.send_welcome_email(data['email'], data['usuario'], password)

                LogController.log_action(
                    accion='crear_usuario',
                    tabla='usuarios',
                    usuario=current_user,
                    detalles={
                        'usuario_creado': data['usuario'],
                        'nombre': data['nombre'],
                        'email': data['email'],
                        'rol': data['rol'],
                        'email_enviado': email_sent
                    }
                )

                response_data = {
                    "mensaje": "Usuario creado exitosamente",
                    "usuario": data['usuario'],
                    "detalles": {
                        "nombre": data['nombre'],
                        "email": data['email'],
                        "rol": data['rol']
                    }
                }

                if not email_sent:
                    response_data["warning"] = {
                        "mensaje": "Error al enviar el email",
                        "detalles": "El usuario se creó correctamente pero no se pudo enviar el email con las credenciales"
                    }

                return jsonify(response_data), 201

            finally:
                cursor.close()
                connection.close()

        except Error as e:
            return jsonify({
                "error": "Error en la base de datos",
                "detalles": str(e)
            }), 500
        except Exception as e:
            return jsonify({
                "error": "Error inesperado",
                "detalles": str(e)
            }), 500

    @staticmethod
    @jwt_required()
    def get_user_permissions():
        try:
            current_user = get_jwt_identity()
            logger.info(f"Obteniendo permisos para el usuario: {current_user}")
            
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            # Obtener el rol del usuario
            cursor.execute("""
                SELECT u.id, u.usuario, r.id as rol_id, r.nombre as rol
                FROM usuarios u
                JOIN roles r ON u.rol_id = r.id
                WHERE u.usuario = %s
            """, (current_user,))
            
            user_info = cursor.fetchone()
            logger.info(f"Información del usuario: {user_info}")
            
            if not user_info:
                logger.error(f"No se encontró el usuario {current_user}")
                return jsonify({"error": "Usuario no encontrado"}), 404
            
            # Obtener los permisos
            cursor.execute("""
                SELECT p.nombre as permiso, p.descripcion
                FROM roles_permisos rp 
                JOIN permisos p ON rp.permiso_id = p.id
                WHERE rp.rol_id = %s
            """, (user_info['rol_id'],))
            
            permisos = cursor.fetchall()
            logger.info(f"Permisos encontrados: {permisos}")
            
            cursor.close()
            connection.close()

            return jsonify({
                "usuario": current_user,
                "rol": user_info['rol'],
                "permisos": permisos
            }), 200

        except Error as e:
            logger.error(f"Error al obtener permisos: {str(e)}")
            return jsonify({"error": f"Error en la base de datos: {str(e)}"}), 500

    @staticmethod
    @jwt_required()
    @admin_required
    def update_user(user_id):
        """Actualiza la información de un usuario."""
        try:
            current_user = get_jwt_identity()
            data = request.get_json()
            
            if not data:
                return jsonify({
                    "error": "No se recibieron datos",
                    "detalles": "El cuerpo de la petición está vacío"
                }), 400

            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            try:
                # Verificar si el usuario existe
                cursor.execute("""
                    SELECT u.*, r.nombre as rol
                    FROM usuarios u
                    LEFT JOIN roles r ON r.id = u.rol_id
                    WHERE u.id = %s
                """, (user_id,))
                
                user = cursor.fetchone()
                if not user:
                    return jsonify({
                        "error": "Usuario no encontrado",
                        "detalles": f"No existe un usuario con el ID {user_id}"
                    }), 404

                # Verificar que no sea el usuario admin principal si se intenta cambiar el rol
                if user['usuario'] == 'franastor' and 'rol' in data:
                    return jsonify({
                        "error": "Operación no permitida",
                        "detalles": "No se puede cambiar el rol del administrador principal"
                    }), 403

                # Validar email si se va a actualizar
                if 'email' in data:
                    if not UserController.is_valid_email(data['email']):
                        return jsonify({
                            "error": "Email inválido",
                            "detalles": "El formato del email no es válido. Debe ser ejemplo@dominio.com"
                        }), 400
                    
                    # Verificar que el email no esté en uso por otro usuario
                    cursor.execute("""
                        SELECT id FROM usuarios 
                        WHERE LOWER(email) = LOWER(%s) AND id != %s
                    """, (data['email'], user_id))
                    
                    if cursor.fetchone():
                        return jsonify({
                            "error": "Email duplicado",
                            "detalles": "El email ya está en uso por otro usuario"
                        }), 400

                # Validar rol si se va a actualizar
                if 'rol' in data:
                    cursor.execute("SELECT id FROM roles WHERE nombre = %s", (data['rol'],))
                    rol = cursor.fetchone()
                    if not rol:
                        return jsonify({
                            "error": "Rol inválido",
                            "detalles": f"El rol '{data['rol']}' no existe en el sistema"
                        }), 400
                    data['rol_id'] = rol['id']
                    del data['rol']

                # Construir la consulta de actualización dinámicamente
                update_fields = []
                update_values = []
                valid_fields = {'nombre', 'email', 'rol_id'}
                
                for field in valid_fields:
                    if field in data:
                        update_fields.append(f"{field} = %s")
                        update_values.append(data[field])

                if not update_fields:
                    return jsonify({
                        "error": "Sin cambios",
                        "detalles": "No se proporcionaron campos válidos para actualizar"
                    }), 400

                update_values.append(user_id)
                update_query = f"""
                    UPDATE usuarios 
                    SET {', '.join(update_fields)}
                    WHERE id = %s
                """
                
                cursor.execute(update_query, update_values)
                connection.commit()

                # Obtener los datos actualizados
                cursor.execute("""
                    SELECT u.id, u.usuario, u.nombre, u.email, u.activo,
                           r.nombre as rol, r.descripcion as rol_descripcion
                    FROM usuarios u
                    LEFT JOIN roles r ON r.id = u.rol_id
                    WHERE u.id = %s
                """, (user_id,))
                
                updated_user = cursor.fetchone()

                LogController.log_action(
                    accion='actualizar_usuario',
                    tabla='usuarios',
                    usuario=current_user,
                    detalles={
                        'usuario_id': user_id,
                        'campos_actualizados': list(data.keys())
                    }
                )

                return jsonify({
                    "mensaje": "Usuario actualizado correctamente",
                    "detalles": updated_user
                }), 200

            finally:
                cursor.close()
                connection.close()

        except Error as e:
            return jsonify({
                "error": "Error en la base de datos",
                "detalles": str(e)
            }), 500
        except Exception as e:
            return jsonify({
                "error": "Error inesperado",
                "detalles": str(e)
            }), 500

    @staticmethod
    @jwt_required()
    @admin_required
    def reset_password(user_id):
        """Restablece la contraseña de un usuario y envía las nuevas credenciales por email."""
        try:
            current_user = get_jwt_identity()
            
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            try:
                # Verificar si el usuario existe
                cursor.execute("""
                    SELECT usuario, email, rol_id
                    FROM usuarios
                    WHERE id = %s
                """, (user_id,))
                
                user = cursor.fetchone()
                if not user:
                    return jsonify({
                        "error": "Usuario no encontrado",
                        "detalles": f"No existe un usuario con el ID {user_id}"
                    }), 404

                # Verificar que no sea el usuario admin principal
                if user['rol_id'] == 1 and user['usuario'] == 'franastor':
                    return jsonify({
                        "error": "Operación no permitida",
                        "detalles": "No se puede restablecer la contraseña del administrador principal"
                    }), 403

                # Generar nueva contraseña
                new_password = UserController.generate_password()
                hashed_password = generate_password_hash(new_password)

                # Actualizar contraseña
                cursor.execute("""
                    UPDATE usuarios 
                    SET password = %s 
                    WHERE id = %s
                """, (hashed_password, user_id))
                
                connection.commit()

                # Enviar email con las nuevas credenciales
                email_sent = UserController.send_password_reset_email(
                    user['email'], 
                    user['usuario'], 
                    new_password
                )

                LogController.log_action(
                    accion='restablecer_password',
                    tabla='usuarios',
                    usuario=current_user,
                    detalles={
                        'usuario_id': user_id,
                        'email_enviado': email_sent
                    }
                )

                response_data = {
                    "mensaje": "Contraseña restablecida correctamente",
                    "detalles": {
                        "usuario": user['usuario'],
                        "email": user['email']
                    }
                }

                if not email_sent:
                    response_data["warning"] = {
                        "mensaje": "Error al enviar el email",
                        "detalles": "La contraseña se restableció pero no se pudo enviar el email con las credenciales"
                    }

                return jsonify(response_data), 200

            finally:
                cursor.close()
                connection.close()

        except Error as e:
            return jsonify({
                "error": "Error en la base de datos",
                "detalles": str(e)
            }), 500
        except Exception as e:
            return jsonify({
                "error": "Error inesperado",
                "detalles": str(e)
            }), 500

    @staticmethod
    def send_password_reset_email(email: str, username: str, password: str) -> bool:
        """Envía un correo con las nuevas credenciales después de restablecer la contraseña."""
        try:
            smtp_server = "mail.your-server.de"
            smtp_port = 587
            sender_email = os.getenv('HETZNER_EMAIL')
            sender_password = os.getenv('HETZNER_PASSWORD')

            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = email
            msg['Subject'] = "Restablecimiento de contraseña"

            html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #2c3e50;">Restablecimiento de contraseña</h2>
                        <p>Se ha restablecido tu contraseña. Tus nuevas credenciales son:</p>
                        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <p><strong>Usuario:</strong> {username}</p>
                            <p><strong>Nueva contraseña:</strong> {password}</p>
                        </div>
                        <p>Por favor, cambia tu contraseña la próxima vez que inicies sesión.</p>
                        <p style="color: #e74c3c;"><strong>Importante:</strong> No compartas estas credenciales con nadie.</p>
                    </div>
                </body>
            </html>
            """

            msg.attach(MIMEText(html, 'html'))

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)

            return True
        except Exception as e:
            print(f"Error al enviar email de restablecimiento: {str(e)}")
            return False

def validate_password(password):
    """
    Valida que la contraseña cumpla con los requisitos:
    - Mínimo 8 caracteres
    - Al menos una letra mayúscula
    - Al menos una letra minúscula
    - Al menos un número
    - Al menos un carácter especial
    """
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    
    if not re.search(r"[A-Z]", password):
        return False, "La contraseña debe contener al menos una letra mayúscula"
    
    if not re.search(r"[a-z]", password):
        return False, "La contraseña debe contener al menos una letra minúscula"
    
    if not re.search(r"\d", password):
        return False, "La contraseña debe contener al menos un número"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "La contraseña debe contener al menos un carácter especial (!@#$%^&*(),.?\":{}|<>)"
    
    return True, "Contraseña válida"

def send_password_change_notification(user_email, username):
    """
    Envía un correo electrónico notificando el cambio de contraseña
    """
    try:
        msg = MIMEText(f"""
        Hola {username},

        Tu contraseña ha sido cambiada exitosamente.

        Si no has sido tú quien ha realizado este cambio, por favor contáctanos inmediatamente respondiendo a este correo.

        Saludos,
        El equipo de soporte
        """)
        
        msg['Subject'] = 'Cambio de contraseña - Notificación de seguridad'
        msg['From'] = os.getenv('EMAIL_USER')
        msg['To'] = user_email
        
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_user = os.getenv('EMAIL_USER')
        smtp_password = os.getenv('EMAIL_PASSWORD')
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            
        logger.info(f"Correo de notificación de cambio de contraseña enviado a {user_email}")
        return True
    except Exception as e:
        logger.error(f"Error al enviar correo de notificación de cambio de contraseña: {str(e)}")
        return False

@jwt_required()
def change_password():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No se recibieron datos"}), 400

        current_password = data.get('current_password')
        new_password = data.get('new_password')

        if not current_password or not new_password:
            return jsonify({"error": "Se requiere la contraseña actual y la nueva"}), 400

        # Validar la nueva contraseña
        is_valid, message = validate_password(new_password)
        if not is_valid:
            return jsonify({"error": message}), 400

        current_user = get_jwt_identity()
        connection = get_db_connection()
        if not connection:
            return jsonify({"error": "Error de conexión a la base de datos"}), 500

        cursor = connection.cursor(dictionary=True)
        try:
            # Verificar la contraseña actual y obtener datos del usuario
            cursor.execute("SELECT id, usuario, password, email FROM usuarios WHERE usuario = %s", (current_user,))
            user = cursor.fetchone()
            
            if not user or not check_password_hash(user['password'], current_password):
                return jsonify({"error": "La contraseña actual es incorrecta"}), 401

            # Actualizar la contraseña
            hashed_password = generate_password_hash(new_password)
            cursor.execute(
                "UPDATE usuarios SET password = %s WHERE usuario = %s",
                (hashed_password, current_user)
            )
            connection.commit()

            # Enviar correo de notificación
            if user['email']:
                send_password_change_notification(user['email'], user['usuario'])

            return jsonify({
                "mensaje": "Contraseña actualizada correctamente",
                "requisitos": {
                    "longitud": "Mínimo 8 caracteres",
                    "mayusculas": "Al menos una letra mayúscula",
                    "minusculas": "Al menos una letra minúscula",
                    "numeros": "Al menos un número",
                    "especiales": "Al menos un carácter especial (!@#$%^&*(),.?\":{}|<>)"
                }
            }), 200

        finally:
            cursor.close()
            connection.close()

    except Error as e:
        logger.error(f"Error de MySQL: {str(e)}")
        return jsonify({"error": f"Error en la base de datos: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500 