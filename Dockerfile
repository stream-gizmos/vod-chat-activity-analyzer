ARG PYTHON_TAG=3.11-slim

FROM python:$PYTHON_TAG AS packages

RUN <<EOT
set -ex

apt update -y
apt install -y git

python -m ensurepip --upgrade
EOT

WORKDIR /var/app/

COPY --link requirements.txt .

RUN --mount=type=ssh <<EOT
set -ex

mkdir -p -m 0600 ~/.ssh
ssh-keyscan github.com >> ~/.ssh/known_hosts

python -m venv --upgrade-deps venv
./venv/bin/pip install -r requirements.txt
EOT



FROM python:$PYTHON_TAG

WORKDIR /var/app/

COPY --from=packages /var/app/ .
COPY --link . .

ENV PATH="/var/app/venv/bin:$PATH"

VOLUME ./data

STOPSIGNAL SIGINT

CMD ["python", "web_app.py"]
