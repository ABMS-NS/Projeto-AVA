import subprocess
import sys
import os
import re
import signal
import threading
from pathlib import Path

CONTROLLER_DIR = Path(__file__).parent / "Controller"

processes = []
services = []

def discover_services():
    found = []
    for entry in sorted(CONTROLLER_DIR.iterdir()):
        if not entry.is_dir() or entry.name.startswith("__"):
            continue
        for py_file in sorted(entry.glob("*.py")):
            if py_file.name.startswith("__"):
                continue
            content = py_file.read_text(encoding="utf-8")
            port_match = re.search(r"port\s*=\s*(\d+)", content)
            port = int(port_match.group(1)) if port_match else None
            found.append({
                "name": py_file.stem,
                "path": str(py_file),
                "port": port,
            })
    return found


def start_service(service):
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    proc = subprocess.Popen(
        [sys.executable, service["path"]],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        text=True,
    )
    return proc


def reader_thread(service, proc):
    try:
        for line in proc.stdout:
            print(f"[{service['name']}] {line}", end="", flush=True)
    except ValueError:
        pass


def signal_handler(signum, frame):
    print(f"\nRecebido sinal {signum}. Encerrando todos os serviços...")
    for proc in processes:
        proc.terminate()
    for proc in processes:
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    sys.exit(0)


def main():
    global services
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    services = discover_services()

    if not services:
        print("Nenhum microsserviço encontrado em Controller/.")
        sys.exit(1)

    print(f"Encontrados {len(services)} microsserviço(s):\n")
    for svc in services:
        port_str = f" (porta {svc['port']})" if svc["port"] else ""
        print(f"  - {svc['name']}{port_str}")

    print("\nIniciando microsserviços...\n")

    threads = []
    for svc in services:
        proc = start_service(svc)
        processes.append(proc)
        port_str = f":{svc['port']}" if svc["port"] else ""
        print(f"  [{svc['name']}] Iniciado (PID {proc.pid}){port_str}")
        t = threading.Thread(target=reader_thread, args=(svc, proc), daemon=True)
        t.start()
        threads.append(t)

    print("\nTodos os microsserviços estão rodando. Pressione Ctrl+C para parar.\n")

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)


if __name__ == "__main__":
    main()
