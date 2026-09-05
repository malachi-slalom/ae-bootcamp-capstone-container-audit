FROM debian:12

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    openssh-server \
    lynis \
    procps \
    iproute2 \
    net-tools \
    sudo \
    python3 \
    python3-pip \
    python3-venv \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-dev.txt /tmp/requirements-dev.txt
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r /tmp/requirements-dev.txt \
    && rm /tmp/requirements-dev.txt

ENV PATH="/opt/venv/bin:${PATH}"

# Prepare runtime dirs
RUN mkdir -p /run/sshd /var/run/sshd /opt/demo /srv/demo /etc/issue.d

# Intentionally insecure/demo-friendly SSH config
RUN if [ -f /etc/ssh/sshd_config ]; then \
      sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config || true; \
      sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config || true; \
      grep -q '^PermitRootLogin yes' /etc/ssh/sshd_config || echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config; \
      grep -q '^PasswordAuthentication yes' /etc/ssh/sshd_config || echo 'PasswordAuthentication yes' >> /etc/ssh/sshd_config; \
    fi

# World-writable demo files
RUN echo "demo secret-ish file" > /opt/demo/insecure.txt \
    && chmod 0666 /opt/demo/insecure.txt \
    && echo "service demo file" > /srv/demo/public.txt \
    && chmod 0666 /srv/demo/public.txt

# Deliberately weak umask in a demo-owned shell profile
RUN echo 'umask 000' > /opt/demo/weak_profile.sh \
    && chmod 0644 /opt/demo/weak_profile.sh

# No login banner configured; create empty placeholders to make absence explicit
RUN : > /etc/issue \
    && : > /etc/issue.net

# Do NOT install unattended-upgrades
# Do NOT install aide
# This omission is intentional for demo findings.

# Simple content for the extra listener on port 8080
RUN mkdir -p /opt/demo/www \
    && echo "hello from the demo web service" > /opt/demo/www/index.html

COPY docker/demo/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 22 8080

ENTRYPOINT ["/entrypoint.sh"]