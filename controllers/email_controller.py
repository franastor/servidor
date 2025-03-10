from flask import jsonify
from flask_jwt_extended import jwt_required
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

class EmailController:
    @staticmethod
    @jwt_required()
    def send_email():
        try:
            # Configuración del servidor SMTP
            smtp_server = "mail.your-server.de"  # Servidor SMTP de Hetzner
            smtp_port = 587
            sender_email = os.getenv('HETZNER_EMAIL')
            sender_password = os.getenv('HETZNER_PASSWORD')
            receiver_email = "cristinagarzoguerra83@gmail.com"

            # Crear el mensaje
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = receiver_email
            msg['Subject'] = "te quiero"

            # Crear el contenido HTML
            html = """
            <html>
                <body style="display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background-color: #f0f0f0;">
                    <div style="text-align: center;">
                        <h1 style="color: #ff4d4d; font-size: 48px; margin-bottom: 20px;">❤️</h1>
                        <p style="color: #ff4d4d; font-size: 24px;">te quiero mucho</p>
                    </div>
                </body>
            </html>
            """

            # Adjuntar el contenido HTML al mensaje
            msg.attach(MIMEText(html, 'html'))

            # Crear conexión SMTP y enviar el email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)

            return jsonify({'message': 'Email enviado exitosamente'}), 200

        except Exception as e:
            return jsonify({'error': str(e)}), 500 