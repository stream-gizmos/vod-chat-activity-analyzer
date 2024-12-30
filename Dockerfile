FROM python:3.11-slim AS packages

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

python -m venv --clear --upgrade-deps venv
./venv/bin/pip install -r requirements.txt
EOT



FROM python:3.11-slim

COPY --from=packages /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

WORKDIR /var/app/

COPY --from=packages /var/app/ .
COPY --link . .

VOLUME ./data

STOPSIGNAL SIGINT

CMD ["./venv/bin/python", "web_app.py"]
