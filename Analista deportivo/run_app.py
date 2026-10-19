"""
Katakuri AI — Lanzador Automático Fullstack (Backend FastAPI + Frontend Vite)
Inicia ambos servidores y abre el navegador automáticamente.
"""
import os
import sys
import time
import subprocess
import webbrowser
import signal

def main():
    root_dir = os.path.abspath(os.path.dirname(__file__))
    frontend_dir = os.path.join(root_dir, "frontend")
    
    # Ruta del ejecutable de python del entorno virtual
    venv_python = os.path.join(root_dir, ".venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        venv_python = sys.executable

    print("=" * 70)
    print("           KATAKURI AI — SPORTS PREDICTION PLATFORM")
    print("=" * 70)
    print()
    print("[1/3] Iniciando Servidor Backend FastAPI en puerto 8000...")
    backend_cmd = [
        venv_python,
        "-m", "uvicorn",
        "backend.app.main:app",
        "--host", "127.0.0.1",
        "--port", "8000"
    ]
    
    # Iniciar backend
    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=root_dir
    )

    print("[2/3] Iniciando Servidor Frontend Vite en puerto 5173...")
    # Iniciar frontend con npm
    frontend_proc = subprocess.Popen(
        "npm run dev",
        cwd=frontend_dir,
        shell=True
    )

    print()
    print("=" * 70)
    print("  SERVIDORES ACTIVOS:")
    print("  • Backend API  : http://localhost:8000/docs")
    print("  • Frontend UI  : http://localhost:5173")
    print("=" * 70)
    print()
    print("[3/3] Sincronizando y verificando disponibilidad del Backend FastAPI...")
    import urllib.request
    backend_ready = False
    for attempt in range(25):
        time.sleep(1)
        if backend_proc.poll() is not None:
            print("\n[ERROR] El servidor Backend terminó inesperadamente antes de iniciar.")
            break
        try:
            with urllib.request.urlopen("http://127.0.0.1:8000/api/health", timeout=1.5) as resp:
                if resp.status == 200:
                    backend_ready = True
                    print("      [OK] Backend activo y respondiendo en http://127.0.0.1:8000")
                    break
        except Exception:
            pass

    if not backend_ready and backend_proc.poll() is None:
        print("      [AVISO] El backend tardó más de lo previsto en responder. Abriendo navegador de todos modos...")

    print("\nAbriendo navegador en http://localhost:5173...")
    webbrowser.open("http://localhost:5173")

    print("\nPresiona CTRL+C en esta consola para detener ambos servidores.\n")

    backend_restarts = 0
    try:
        while True:
            time.sleep(1)
            # Si el backend se detiene inesperadamente, intentar recuperarlo
            if backend_proc.poll() is not None:
                if backend_restarts < 3:
                    backend_restarts += 1
                    print(f"\n[AVISO] El servidor Backend se detuvo. Auto-recuperando (intento {backend_restarts}/3)...")
                    backend_proc = subprocess.Popen(backend_cmd, cwd=root_dir)
                    time.sleep(2)
                    continue
                else:
                    print("\n[ERROR] El servidor Backend se ha detenido repetidamente.")
                    break
            if frontend_proc.poll() is not None:
                print("\n[AVISO] El servidor Frontend se ha detenido.")
                break
    except KeyboardInterrupt:
        print("\nDeteniendo servidores Katakuri AI...")
    finally:
        # Terminar procesos hijos
        try:
            backend_proc.terminate()
        except Exception:
            pass
        try:
            # En Windows matar árbol de procesos de npm/node
            subprocess.run(f"taskkill /f /t /pid {frontend_proc.pid}", shell=True, capture_output=True)
            frontend_proc.terminate()
        except Exception:
            pass
        print("[OK] Servidores detenidos exitosamente.")

if __name__ == "__main__":
    main()
