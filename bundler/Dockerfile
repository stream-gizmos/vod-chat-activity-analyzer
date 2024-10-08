# Highly inspired by https://github.com/engineervix/docker-pyinstaller
FROM ubuntu:20.04

ARG WINE_VERSION=winehq-stable
ARG PYTHON_VERSION=3.11.9
ARG PYINSTALLER_VERSION=6.8

# PYPI repository location
ENV PYPI_URL=https://pypi.python.org/
# PYPI index location
ENV PYPI_INDEX_URL=https://pypi.python.org/simple

# wine settings
ENV WINEARCH win64
ENV WINEDEBUG fixme-all
ENV WINEPREFIX /wine

# xvfb settings
ENV DISPLAY :0

ENV W_DRIVE_C=/wine/drive_c
ENV W_WINDIR_UNIX="$W_DRIVE_C/windows"
ENV W_SYSTEM64_DLLS="$W_WINDIR_UNIX/system32"
ENV W_TMP="$W_DRIVE_C/windows/temp/_$0"

ENV DEBIAN_FRONTEND noninteractive

COPY --link bundler/entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

RUN <<EOT
set -ex

chmod a+x /entrypoint.sh

# we need wine for this to work, so we'll use the PPA
dpkg --add-architecture i386
apt update -y
apt install --no-install-recommends -y \
  apt-transport-https \
  cabextract \
  curl \
  gpg-agent \
  rename \
  software-properties-common \
  unzip \
  wget \
  winbind \
  xvfb \
  xdotool \
  x11-utils \
  xterm \
  zip

wget -nv https://dl.winehq.org/wine-builds/winehq.key
apt-key add winehq.key
add-apt-repository 'https://dl.winehq.org/wine-builds/ubuntu/'
apt update -y
apt install --install-recommends -y \
  $WINE_VERSION

apt clean
rm -rf /var/lib/apt/lists/*

wget -nv https://raw.githubusercontent.com/Winetricks/winetricks/master/src/winetricks
chmod +x winetricks
mv winetricks /usr/local/bin

# wine-gecko
mkdir -p /usr/share/wine/gecko
curl -o /usr/share/wine/gecko/wine_gecko-2.47-x86.msi http://dl.winehq.org/wine/wine-gecko/2.47/wine_gecko-2.47-x86.msi
curl -o /usr/share/wine/gecko/wine_gecko-2.47-x86_64.msi http://dl.winehq.org/wine/wine-gecko/2.47/wine_gecko-2.47-x86_64.msi

echo 'Xvfb $DISPLAY -screen 0 1024x768x24 &' >> /root/.bashrc

# windows 10 environment
winetricks -q win10

# install python in wine, using the msi packages to install, extracting
# the files directly, since installing isn't running correctly.
for msifile in `echo core dev exe lib path pip tcltk tools`; do
    wget -nv "https://www.python.org/ftp/python/$PYTHON_VERSION/amd64/${msifile}.msi"
    wine msiexec /i "${msifile}.msi" /qb TARGETDIR=C:/Python3
    rm ${msifile}.msi
done

cd /wine/drive_c/Python3
echo 'wine '\''C:\Python3\python.exe'\'' "$@"' > /usr/bin/python
echo 'wine '\''C:\Python3\Scripts\easy_install.exe'\'' "$@"' > /usr/bin/easy_install
echo 'wine '\''C:\Python3\Scripts\pip.exe'\'' "$@"' > /usr/bin/pip
echo 'wine '\''C:\Python3\Scripts\pyinstaller.exe'\'' "$@"' > /usr/bin/pyinstaller
echo 'wine '\''C:\Python3\Scripts\pyupdater.exe'\'' "$@"' > /usr/bin/pyupdater
echo 'assoc .py=PythonScript' | wine cmd
echo 'ftype PythonScript=c:\Python3\python.exe "%1" %*' | wine cmd
while pgrep wineserver >/dev/null; do echo "Waiting for wineserver"; sleep 1; done
chmod +x /usr/bin/python /usr/bin/easy_install /usr/bin/pip /usr/bin/pyinstaller /usr/bin/pyupdater
(pip install -U pip || true)
rm -rf /tmp/.wine-*

# install Microsoft Visual C++ Redistributable for Visual Studio 2015, 2017 and 2019 dll files
rm -f "$W_TMP"/*
wget -P "$W_TMP" https://aka.ms/vs/16/release/vc_redist.x64.exe
cabextract -q --directory="$W_TMP" "$W_TMP"/vc_redist.x64.exe
ls -la "$W_TMP/"
#cabextract -q --directory="$W_TMP" "$W_TMP/a10"
cabextract -q --directory="$W_TMP" "$W_TMP/a11"
cd "$W_TMP"
rename 's/_/\-/g' *.dll
cp "$W_TMP"/*.dll "$W_SYSTEM64_DLLS"/

# install pyinstaller
/usr/bin/pip install pyinstaller==$PYINSTALLER_VERSION

# put the src folder inside wine
mkdir /src/
ln -s /src /wine/drive_c/src

mkdir -p /wine/drive_c/tmp
EOT

VOLUME /src/
WORKDIR /wine/drive_c/src/

# Pre-install dependencies
COPY --link requirements.txt /src/
COPY --link src/ /src/src/

RUN <<EOT
#!/bin/bash
set -e

# In case the user specified a custom URL for PYPI, then use
# that one, instead of the default one.
if [[ "$PYPI_URL" != "https://pypi.python.org/" ]] || \
   [[ "$PYPI_INDEX_URL" != "https://pypi.python.org/simple" ]]; then
    # the funky looking regexp just extracts the hostname, excluding port
    # to be used as a trusted-host.
    mkdir -p /wine/drive_c/users/root/pip
    echo "[global]" > /wine/drive_c/users/root/pip/pip.ini
    echo "index = $PYPI_URL" >> /wine/drive_c/users/root/pip/pip.ini
    echo "index-url = $PYPI_INDEX_URL" >> /wine/drive_c/users/root/pip/pip.ini
    echo "trusted-host = $(echo $PYPI_URL | perl -pe 's|^.*?://(.*?)(:.*?)?/.*$|$1|')" >> /wine/drive_c/users/root/pip/pip.ini

    echo "Using custom pip.ini: "
    cat /wine/drive_c/users/root/pip/pip.ini
fi

if [ -f requirements.txt ]; then
    pip install -r requirements.txt
fi
EOT
