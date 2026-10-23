import sys
import webview
from src.config import APP_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT, INDEX_HTML
from src.database import init_db
from src.api_bridge import ApiBridge

def main():
    # 1. Inicializar base de datos local SQLite
    init_db()

    # 2. Instanciar puente de comunicación API (Python <-> JS)
    bridge = ApiBridge()

    # 3. Crear ventana nativa con PyWebView
    window = webview.create_window(
        title=APP_TITLE,
        url=str(INDEX_HTML),
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        min_size=(880, 640),
        js_api=bridge,
        background_color='#F8FAFC'
    )
    
    bridge.set_window(window)

    # 4. Iniciar bucle de eventos de la ventana de escritorio
    webview.start(debug=False)

if __name__ == "__main__":
    main()
