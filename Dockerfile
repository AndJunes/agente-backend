# Mirag. La imagen no instala NADA: el nucleo es biblioteca estandar pura.
#
# Eso no es una curiosidad, es la mejor propiedad de seguridad que tiene este contenedor.
# Sin `pip install` no hay cadena de suministro que comprometer, no hay CVE de dependencia
# que parchear a las 3 de la mañana, y la superficie es la del interprete y nada mas.
# Si algun dia esto necesita una dependencia, que sea una decision consciente y con lock.
#
# 3.14-slim para igualar la version con la que se probo (3.14.6 en el host).
FROM python:3.14-slim

# PYTHONDONTWRITEBYTECODE: sin __pycache__, que en esta imagen solo seria basura que el
#   usuario sin privilegios ni siquiera podria escribir.
# PYTHONUNBUFFERED: los logs salen cuando pasan, no cuando se llena el buffer. Sin esto
#   `docker logs` va ciego justo cuando hace falta ver algo.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Usuario sin privilegios, creado ANTES de copiar para poder repartir dueños en el COPY.
RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin mirag

WORKDIR /app

# El codigo se copia como ROOT y el proceso corre como `mirag`. La consecuencia es la que
# importa: este agente ejecuta codigo que escribe un modelo, y ese codigo corre como
# `mirag`, que NO PUEDE reescribir /app. O sea que una ejecucion hostil no puede dejar
# nada plantado en el agente para la siguiente peticion. Sin esto, un `test_algo.py` que
# abra `server.py` en modo escritura se persiste en la imagen viva.
COPY --chown=root:root . /app

# Las unicas rutas que el proceso puede escribir, creadas y cedidas una por una.
# Los dos .jsonl existen de antemano a proposito: `traza.escribir` hace `open(archivo,"a")`
# sin try/except (traza.py:110), y el directorio /app no es escribible por `mirag`, asi que
# si el archivo no existiera la primera peticion moriria con PermissionError.
RUN mkdir -p /app/artefactos /app/salida \
 && touch /app/trazas.jsonl /app/trazas_noche.jsonl \
 && chown mirag:mirag /app/artefactos /app/salida /app/trazas.jsonl /app/trazas_noche.jsonl

# 0.0.0.0 aqui NO es relajar el bind: dentro del contenedor no hay mas red que la suya, y
# es la unica forma de que un puerto publicado alcance al proceso. Lo que aisla es publicar
# con `-p 127.0.0.1:8000:8000`. El defecto del codigo sigue siendo localhost.
# MIRAG_OFFLINE=1 de fabrica: una imagen recien construida no puede gastar dinero de nadie.
ENV MIRAG_HOST=0.0.0.0 \
    MIRAG_PORT=8000 \
    MIRAG_OFFLINE=1

USER mirag
EXPOSE 8000

# Sin curl en la imagen (slim, y no vale la pena añadir un binario de red solo para esto):
# el healthcheck lo hace el mismo interprete que ya esta dentro.
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request,sys;\
sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/',timeout=4).status==200 else 1)"

CMD ["python", "server.py"]
