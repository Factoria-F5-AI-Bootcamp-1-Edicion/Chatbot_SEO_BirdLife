# Imagen base
FROM python:3.8

# Copiar el archivo requirements.txt y ejecutar pip install
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt

# Copiar el código fuente al contenedor
COPY main.py /app/main.py

# Copiar el archivo .env al contenedor
COPY .env /app/.env

COPY instructions.txt /app/instructions.txt

# Especificar el comando que se ejecutará al iniciar el contenedor
CMD ["python", "main.py"]