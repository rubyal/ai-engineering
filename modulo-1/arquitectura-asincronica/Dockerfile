# Python 3.12+ (requisito del ejercicio: asyncio.timeout)
FROM python:3.12-slim

# - PYTHONUNBUFFERED: los logs salen en tiempo real (sin buffer)
# - PYTHONDONTWRITEBYTECODE: no genera archivos .pyc dentro del contenedor
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# El script solo usa la librería estándar, no hay dependencias que instalar
COPY orquestador.py .

# Buena práctica: no ejecutar como root
RUN useradd --create-home appuser
USER appuser

CMD ["python", "orquestador.py"]
