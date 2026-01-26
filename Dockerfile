# Folosim o versiune ușoară de Python 3.10
FROM python:3.10-slim

# Setăm directorul de lucru în container
WORKDIR /app

# Instalăm dependențe de sistem necesare pentru networking și compilare (dacă extindem proiectul)
# net-tools: pentru ifconfig/netstat
# iputils-ping: pentru ping
# procps: pentru comanda 'ps' ca să testăm procesul ghost
RUN apt-get update && apt-get install -y \
    net-tools \
    iputils-ping \
    procps \
    gcc \
    netcat-traditional \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copiem fișierul de dependențe și le instalăm
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiem codul sursă
COPY . .

# Comanda default (poate fi suprascrisă)
# Ține containerul activ pentru a putea intra în el
CMD ["tail", "-f", "/dev/null"]