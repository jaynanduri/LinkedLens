#!/bin/bash
apt-get update
apt-get install -y git
apt-get install -y ca-certificates curl

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

usermod -aG docker $USER

systemctl enable docker

DOCKER_USER="apeksha.suhas.joshi"
DOCKER_HOME="/home/$DOCKER_USER/.docker"

if [ -d "$DOCKER_HOME" ]; then
echo "Setting permissions for Docker home directory..."
chown "$DOCKER_USER:$DOCKER_USER" "$DOCKER_HOME" -R
chmod g+rwx "$DOCKER_HOME" -R
fi