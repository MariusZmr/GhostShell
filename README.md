# 👻 GhostShell

Framework de Manipulare a Proceselor (OS) & Security Auditing

GhostShell este un utilitar CLI (Command Line Interface) dezvoltat pentru disciplina Sisteme de Operare. Proiectul demonstrează concepte avansate de interacțiune cu Kernel-ul Linux, manipularea memoriei proceselor și networking la nivel scăzut.

> **Notă:** Deși este un tool de "Ethical Hacking", scopul principal este **educațional**: înțelegerea structurii proceselor (task_struct, argv) și a virtualizării.

---

## 🚀 Funcționalități Cheie

### 1. 🕵️ Ghost Mode (Process Masquerading)

Ascunde identitatea procesului curent față de utilitarele standard de monitorizare (`ps`, `top`, `htop`).

**Tehnică:**
- Nu doar schimbă numele thread-ului (`prctl`), ci suprascrie memoria alocată argumentelor liniei de comandă (`argv`) folosind biblioteca `setproctitle`.

**Rezultat:** Transformă `python main.py` în orice proces legitim (ex: `nginx-worker`, `kworker`).

### 2. 📡 Network Scanner

Un scanner de porturi TCP Connect multi-threaded.

- Folosește threading pentru a scana sute de porturi simultan
- Demonstrează gestionarea concurenței și a socket-urilor Berkeley (`AF_INET`, `SOCK_STREAM`)

### 3. 🛡️ Kernel Audit

Verifică versiunea kernel-ului curent pentru vulnerabilități critice cunoscute, specific Dirty Pipe (CVE-2022-0847).

---

## 🛠️ Instalare și Configurare

Proiectul este containerizat complet. Nu contează dacă ești pe Windows, macOS sau Linux, pașii sunt identici.

### Cerințe

- ✅ Docker Desktop instalat și pornit
- ✅ Git (opțional, pentru clonare)

### Pasul 1: Clonare Repository

```bash
git clone https://github.com/MariusZmr/GhostShell.git
cd GhostShell-Proiect-SO
```

### Pasul 2: Pornire Mediu (Docker)

Această comandă va construi imaginea și va instala toate dependențele izolat.

```bash
docker-compose up -d --build
```

### Pasul 3: Accesare Shell

Toate comenzile de hacking se rulează în interiorul containerului.

```bash
docker-compose exec ghostshell bash
```

> Acum prompt-ul tău ar trebui să fie: `root@docker-desktop:/app#`

---

## 💻 Utilizare

Odată intrat în container, poți folosi CLI-ul `main.py`.

### 👻 Activare Ghost Mode

Ascunde procesul curent sub un nume fals.

```bash
python main.py ghost --name "systemd-daemon"
```

**Verificare:** Deschide un alt terminal, intră în container și rulează `ps aux`. Vei vedea procesul `systemd-daemon` rulând, nu `python`.

### 📡 Scanare Rețea

Scanează o țintă (IP sau domeniu) pe un interval de porturi.

```bash
python main.py scan google.com --ports 1-100 --threads 50
```

### 🛡️ Audit Kernel

Verifică securitatea kernel-ului pe care rulează containerul.

```bash
python main.py audit
```

---

## 🏗️ Arhitectura Tehnică

| Componentă | Detalii |
|---|---|
| **Limbaj** | Python 3.10 |
| **Framework CLI** | Typer + Rich (pentru UI colorat și tabele) |
| **OS Manipulation** | `setproctitle` (C extension for Python) pentru acces la argv |
| **Infrastructure** | Docker (Debian Slim image) |

---

## ⚖️ Disclaimer

Acest software a fost creat **strict în scopuri educaționale**. Autorul nu este responsabil pentru utilizarea necorespunzătoare a acestui utilitar.