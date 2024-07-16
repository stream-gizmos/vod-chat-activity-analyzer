FROM python:3.11-slim AS packages

RUN <<EOT
set -ex
python -m ensurepip --upgrade
python -m pip install --upgrade pip setuptools

apt update -y
apt install -y git
EOT

WORKDIR /var/app/

COPY requirements.txt .

RUN <<EOT
set -ex
pip install -r requirements.txt
EOT



FROM python:3.11-slim

COPY --from=packages /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

WORKDIR /var/app/

COPY . .

VOLUME ./data

STOPSIGNAL SIGINT

CMD ["python", "web_app.py"]
