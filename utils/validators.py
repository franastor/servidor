import re

def is_valid_email(email: str) -> bool:
    """Valida que el email tenga un formato correcto."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def normalize_username(username: str) -> str:
    """Normaliza el nombre de usuario para comparaciones."""
    return username.lower().strip()

def generate_password(length: int = 12) -> str:
    """Genera una contraseña aleatoria segura."""
    import secrets
    import string
    
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