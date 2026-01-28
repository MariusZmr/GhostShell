# --- Stage 1: Builder (Compilare) ---
FROM python:3.10-slim as builder

WORKDIR /app

# Instalăm gcc doar pentru compilarea pachetelor Python (dacă e necesar)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Instalăm pachetele într-un director temporar (/install)
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Stage 2: Runtime (Imaginea Finală) ---
FROM python:3.10-slim

WORKDIR /app

# Instalăm DOAR dependențele de runtime (fără gcc)
# Folosim --no-install-recommends pentru a ține imaginea mică
RUN apt-get update && apt-get install -y --no-install-recommends \
    net-tools \
    iputils-ping \
    procps \
    netcat-traditional \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copiem bibliotecile Python deja instalate din stagiul de builder
COPY --from=builder /install /usr/local

# Copiem codul sursă
COPY . .

# Comanda default: Pornim cron, simulăm boot-ul pentru persistență și ținem containerul activ
CMD service cron start && tail -f /dev/null