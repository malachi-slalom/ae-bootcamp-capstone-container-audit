FROM debian:12

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    openssh-server \
    procps \
    iproute2 \
    net-tools \
    sudo \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Prepare ssh runtime dirs
RUN mkdir -p /run/sshd /var/run/sshd

# Intentionally insecure/demo-friendly SSH config
RUN if [ -f /etc/ssh/sshd_config ]; then \
      sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config || true; \
      sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config || true; \
      grep -q '^PermitRootLogin yes' /etc/ssh/sshd_config || echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config; \
      grep -q '^PasswordAuthentication yes' /etc/ssh/sshd_config || echo 'PasswordAuthentication yes' >> /etc/ssh/sshd_config; \
    fi

# Create a low-hanging-fruit permissions issue
RUN mkdir -p /opt/demo \
    && echo "demo secret-ish file" > /opt/demo/insecure.txt \
    && chmod 0666 /opt/demo/insecure.txt

# Optional extra demo file
RUN echo "hello from demo container" > /opt/demo/readme.txt

COPY docker/demo/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 22

ENTRYPOINT ["/entrypoint.sh"]