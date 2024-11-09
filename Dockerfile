FROM python
RUN pip install -r requirements.txt

COPY resources /mnt/app
COPY requirements.txt /mnt/app
COPY src/webserver.py /mnt/app

WORKDIR /mnt/app
ENTRYPOINT fastapi run --port 80 webserver.py