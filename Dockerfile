FROM python:3.11-slim

RUN <<EOT
set -ex
python -m ensurepip --upgrade
python -m pip install --upgrade pip setuptools
EOT

WORKDIR /var/app/

COPY . .

RUN <<EOT
set -ex
pip install -r requirements.txt
EOT

ENTRYPOINT ["python"]

CMD ["flask_app.py"]
