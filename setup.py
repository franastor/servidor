from setuptools import setup, find_packages

setup(
    name="servidor",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'flask==3.0.2',
        'flask-jwt-extended==4.6.0',
        'mysql-connector-python==8.3.0',
        'python-dotenv==1.0.1',
        'flask-swagger-ui==4.11.1',
    ],
) 