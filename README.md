# Servidor Flask con JWT y MySQL

Este es un servidor básico en Flask que utiliza autenticación JWT y se conecta a una base de datos MySQL.

## Requisitos

- Python 3.x
- MySQL

## Instalación

1. Instalar las dependencias:
```bash
pip install -r requirements.txt
```

2. Configurar las variables de entorno:
   - Copia el archivo `.env.example` a `.env`
   - Modifica el archivo `.env` con tus credenciales y configuración

3. Ejecutar el servidor:
```bash
python app.py
```

## Uso

### Autenticación

Para obtener un token JWT, primero debes hacer login:

```bash
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"usuario": "tu_usuario", "password": "tu_contraseña"}'
```

La respuesta será un token JWT válido por 1 hora:
```json
{
    "mensaje": "Login exitoso",
    "token": "tu_token_jwt",
    "usuario": "tu_usuario"
}
```

### Documentación de la API

La documentación de la API está disponible en el endpoint `/docs`. Para acceder a ella, necesitas:

1. Un token JWT válido
2. Un usuario con permisos de acceso a la documentación (campo `tiene_acceso_docs = 1` en la base de datos)

Para acceder a la documentación:

```bash
curl -H "Authorization: Bearer <tu_token>" http://localhost:5000/docs
```

La documentación está en formato OpenAPI 3.0 y puede ser utilizada con herramientas como Swagger UI.

### Endpoints Protegidos

Para acceder a los endpoints protegidos, necesitas incluir el token JWT en el header de la petición:

```
Authorization: Bearer <tu_token>
```

### Endpoints disponibles

#### Públicos
- POST `/login`: Autenticación de usuario y generación de token

#### Protegidos
- GET `/inicio`: Devuelve "Hola"
- GET `/fin`: Devuelve "Adios"
- GET `/docs`: Documentación de la API (requiere permisos especiales)

## Testing

El proyecto incluye una suite completa de tests unitarios. Para ejecutar los tests:

```bash
pytest
```

Para ver la cobertura de código:
```bash
pytest --cov=. --cov-report=term-missing
```

### Estructura de Tests

Los tests están organizados en la carpeta `tests/`:

- `conftest.py`: Configuración global de pytest y fixtures comunes
- `test_auth_controller.py`: Tests para el controlador de autenticación
- `test_basic_controller.py`: Tests para el controlador básico
- `test_docs_controller.py`: Tests para el controlador de documentación

### Casos de Prueba

Los tests cubren los siguientes escenarios:

#### Autenticación
- Login exitoso
- Credenciales inválidas
- Usuario no existente en la base de datos
- Datos faltantes
- Errores de base de datos

#### Endpoints Básicos
- Acceso exitoso con token válido
- Acceso denegado sin token
- Respuestas correctas

#### Documentación
- Acceso exitoso con permisos
- Acceso denegado sin permisos
- Acceso denegado sin token
- Errores de base de datos

## Configuración

El servidor utiliza variables de entorno para la configuración. Las variables necesarias son:

- `JWT_SECRET_KEY`: Clave secreta para firmar los tokens JWT
- `DB_HOST`: Host de la base de datos
- `DB_USER`: Usuario de la base de datos
- `DB_PASSWORD`: Contraseña de la base de datos
- `DB_NAME`: Nombre de la base de datos

## Seguridad

- Se utilizan parámetros preparados para prevenir inyecciones SQL
- Los tokens JWT expiran después de 1 hora
- Las contraseñas se comparan de forma segura en la base de datos
- La documentación de la API está protegida y requiere permisos especiales

## Estructura del Proyecto

```
servidor/
├── controllers/
│   ├── __init__.py
│   ├── auth_controller.py
│   ├── basic_controller.py
│   └── docs_controller.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth_controller.py
│   ├── test_basic_controller.py
│   └── test_docs_controller.py
├── app.py
├── database.py
├── requirements.txt
├── pytest.ini
├── .env
├── .env.example
└── README.md
```

## Contribución

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles. 