"""
Katakuri v4.0 — Lanzador Automático Fullstack (Backend FastAPI + Frontend Vite)
Inicia ambos servidores y abre el navegador automáticamente con motor de predicción de alta precisión.
"""
import os
import sys
import time
import subprocess
import webbrowser
import signal

def _disable_windows_quickedit():
    """Desactiva el modo QuickEdit de la consola de Windows para evitar que un clic en la ventana congele stdout y cuelgue el servidor."""
    if os.name == "nt":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            h_stdin = kernel32.GetStdHandle(-10)  # STD_INPUT_HANDLE
            mode = ctypes.c_uint32()
            if kernel32.GetConsoleMode(h_stdin, ctypes.byref(mode)):
                # Desactivar ENABLE_QUICK_EDIT_MODE (0x0040) y activar ENABLE_EXTENDED_FLAGS (0x0080)
                new_mode = (mode.value & ~0x0040) | 0x0080
                kernel32.SetConsoleMode(h_stdin, new_mode)
        except Exception:
            pass

def main():
    _disable_windows_quickedit()
    root_dir = os.path.abspath(os.path.dirname(__file__))
    frontend_dir = os.path.join(root_dir, "frontend")
    
    # Ruta del ejecutable de python del entorno virtual
    venv_python = os.path.join(root_dir, ".venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        venv_python = sys.executable

    print("=" * 70)
    print("      KATAKURI v4.1 — ALTA PRECISIÓN & ANALÍTICA DEPORTIVA")
    print(" 4,749 Partidos Oficiales · Elo Dinámico · Walk-Forward Validado")
    print("=" * 70)
    print()
    print("[1/3] Iniciando Servidor Backend FastAPI en puerto 8000...")
    backend_cmd = [
        venv_python,
        "-m", "uvicorn",
        "backend.app.main:app",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--timeout-keep-alive", "75"
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
    last_backend_start = time.time()
    try:
        while True:
            time.sleep(1)
            # Si el backend lleva más de 60s estable, resetear el contador de reinicios
            if backend_proc.poll() is None and (time.time() - last_backend_start) > 60:
                backend_restarts = 0

            # Si el backend se detiene inesperadamente, auto-recuperarlo
            if backend_proc.poll() is not None:
                if backend_restarts < 5:
                    backend_restarts += 1
                    print(f"\n[AVISO] El servidor Backend se detuvo. Auto-recuperando (intento {backend_restarts}/5)...")
                    backend_proc = subprocess.Popen(backend_cmd, cwd=root_dir)
                    last_backend_start = time.time()
                    time.sleep(2)
                    continue
                else:
                    print("\n[ERROR] El servidor Backend se ha detenido repetidamente.")
                    break

            # Si el frontend se detiene inesperadamente, auto-recuperarlo en lugar de cerrar la sesión
            if frontend_proc.poll() is not None:
                print("\n[AVISO] El servidor Frontend se detuvo. Auto-recuperando Vite...")
                frontend_proc = subprocess.Popen("npm run dev", cwd=frontend_dir, shell=True)
                time.sleep(2)
                continue
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
