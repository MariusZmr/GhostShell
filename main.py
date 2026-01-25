import typer
import sys
import socket
import threading
import os
import time
# Importăm noua bibliotecă de stealth
import setproctitle 
from typing import List, Optional
from typing_extensions import Annotated
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

app = typer.Typer(help="GhostShell - Utilitar de Securitate Ofensivă")
console = Console()

# --- MODUL 1: MANIPULARE OS (Ghost Mode V2) ---

@app.command()
def ghost(
    name: str = typer.Option("kworker/u4:0", help="Numele fals sub care să ruleze procesul")
):
    """
    [OS TRICK] Activează 'Ghost Mode'. Suprascrie ARGV și Process Title.
    """
    console.print(Panel.fit(f"[bold red]Inițiere Protocol GHOST[/bold red]\nTarget Name: [cyan]{name}[/cyan]", border_style="red"))
    
    # Folosim spinner-ul 'dots' care este standard
    with console.status("[bold green]Suprascriere memorie proces (argv)...[/bold green]", spinner="dots"):
        time.sleep(1)
        # Aici e magia care păcălește ps aux:
        setproctitle.setproctitle(name)
    
    console.print(f"[bold green]✔ Succes![/bold green] Identitate schimbată în '{name}'.")
    console.print("[yellow]Verificare:[/yellow] Rulează `ps aux | grep nginx` în celălalt terminal.")
    
    # Ținem procesul viu ca să îl putem vedea
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Ghost Mode dezactivat.[/yellow]")

# --- MODUL 2: SCANNER REȚEA ---

def scan_port(ip, port, open_ports):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex((ip, port))
        if result == 0:
            open_ports.append(port)
        sock.close()
    except:
        pass

@app.command()
def scan(
    target: str = typer.Argument(..., help="Adresa IP țintă"),
    ports: str = typer.Option("1-1000", help="Interval de porturi (ex: 1-1000)"),
    threads: int = typer.Option(100, help="Numărul de thread-uri paralele")
):
    """
    Scanner de porturi TCP multi-threaded.
    """
    console.print(f"[bold blue]Inițiere scanare pe {target}...[/bold blue]")
    
    try:
        start_port, end_port = map(int, ports.split('-'))
    except ValueError:
        console.print("[red]Format porturi invalid. Folosește 'start-end' (ex: 1-100).[/red]")
        return

    port_range = range(start_port, end_port + 1)
    open_ports = []
    thread_list = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task(f"[cyan]Scanare {len(port_range)} porturi...", total=len(port_range))
        
        for port in port_range:
            t = threading.Thread(target=scan_port, args=(target, port, open_ports))
            thread_list.append(t)
            t.start()
            while len(threading.enumerate()) > threads:
                time.sleep(0.01)
            progress.advance(task)

        for t in thread_list:
            t.join()

    table = Table(title=f"Rezultate Scanare: {target}")
    table.add_column("Port", justify="right", style="cyan", no_wrap=True)
    table.add_column("Stare", style="green")
    table.add_column("Serviciu", style="magenta")

    common_ports = {22: "SSH", 80: "HTTP", 443: "HTTPS", 21: "FTP", 3306: "MySQL"}
    
    if open_ports:
        for port in sorted(open_ports):
            service = common_ports.get(port, "Unknown")
            table.add_row(str(port), "OPEN", service)
        console.print(table)
    else:
        console.print("[bold red]Niciun port deschis găsit.[/bold red]")

# --- MODUL 3: AUDIT KERNEL ---

@app.command()
def audit():
    console.print(Panel("Analiză Versiune Kernel", title="Kernel Audit", border_style="yellow"))
    try:
        kernel_version = os.uname().release
        console.print(f"Versiune Kernel: [bold white]{kernel_version}[/bold white]")
        console.print(f"Sistem: [bold white]{os.uname().sysname}[/bold white]")
    except Exception as e:
        console.print(f"[red]Eroare: {e}[/red]")

if __name__ == "__main__":
    app()