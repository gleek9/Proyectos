import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from src.config import DB_PATH

def get_connection() -> sqlite3.Connection:
    """Obtiene una conexión a la base de datos SQLite con row_factory para diccionarios."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa las tablas de la base de datos si no existen."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Tabla de configuración (API Keys y preferencias)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. Tabla del perfil profesional del usuario
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT,
                email TEXT,
                phone TEXT,
                location TEXT,
                linkedin TEXT,
                portfolio TEXT,
                summary TEXT,
                raw_json TEXT NOT NULL,
                original_filename TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 3. Tabla de historial de ofertas y análisis
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_title TEXT,
                company TEXT,
                url TEXT,
                job_description TEXT,
                match_percentage REAL,
                analysis_json TEXT,
                generated_cv_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

# --- Funciones de Configuración ---

def get_config(key: str, default: Optional[str] = None) -> Optional[str]:
    """Obtiene un valor de configuración por clave."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row["value"] if row else default

def set_config(key: str, value: str):
    """Guarda o actualiza un valor de configuración."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO config (key, value, updated_at) 
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET 
                value = excluded.value,
                updated_at = CURRENT_TIMESTAMP
        """, (key, value))
        conn.commit()

def delete_config(key: str):
    """Elimina una clave de configuración."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM config WHERE key = ?", (key,))
        conn.commit()

# --- Funciones de Perfil de Usuario ---

def get_user_profile() -> Optional[Dict[str, Any]]:
    """Obtiene el perfil profesional más reciente del usuario."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, full_name, email, phone, location, linkedin, portfolio, 
                   summary, raw_json, original_filename, updated_at
            FROM user_profile 
            ORDER BY id DESC LIMIT 1
        """)
        row = cursor.fetchone()
        if not row:
            return None
        
        result = dict(row)
        try:
            result["parsed_data"] = json.loads(result["raw_json"])
        except Exception:
            result["parsed_data"] = {}
        return result

def save_user_profile(profile_data: Dict[str, Any], original_filename: Optional[str] = None) -> int:
    """Guarda o actualiza el perfil del usuario."""
    full_name = profile_data.get("full_name", "")
    email = profile_data.get("email", "")
    phone = profile_data.get("phone", "")
    location = profile_data.get("location", "")
    linkedin = profile_data.get("linkedin", "")
    portfolio = profile_data.get("portfolio", "")
    summary = profile_data.get("summary", "")
    raw_json = json.dumps(profile_data, ensure_ascii=False)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_profile (
                full_name, email, phone, location, linkedin, portfolio, 
                summary, raw_json, original_filename, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            full_name, email, phone, location, linkedin, portfolio,
            summary, raw_json, original_filename
        ))
        conn.commit()
        return cursor.lastrowid

def delete_user_profile():
    """Elimina el perfil profesional del usuario en SQLite."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_profile")
        conn.commit()

# --- Funciones de Historial de Vacantes ---

def save_job_analysis(
    job_title: str,
    company: str,
    url: str,
    job_description: str,
    match_percentage: float,
    analysis_data: Dict[str, Any],
    generated_cv_path: Optional[str] = None
) -> int:
    """Guarda el resultado del análisis de una vacante en el historial."""
    analysis_json = json.dumps(analysis_data, ensure_ascii=False)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO job_history (
                job_title, company, url, job_description, 
                match_percentage, analysis_json, generated_cv_path, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            job_title, company, url, job_description, 
            match_percentage, analysis_json, generated_cv_path
        ))
        conn.commit()
        return cursor.lastrowid

def update_job_history_cv(history_id: int, generated_cv_path: str):
    """Actualiza la ruta del CV generado para un registro en el historial."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE job_history 
            SET generated_cv_path = ?
            WHERE id = ?
        """, (generated_cv_path, history_id))
        conn.commit()

def get_job_history(limit: int = 10) -> List[Dict[str, Any]]:
    """Recupera los últimos análisis de vacantes registrados."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, job_title, company, url, match_percentage, 
                   analysis_json, generated_cv_path, created_at
            FROM job_history
            ORDER BY id DESC LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        results = []
        for row in rows:
            item = dict(row)
            try:
                item["analysis"] = json.loads(item["analysis_json"])
            except Exception:
                item["analysis"] = {}
            results.append(item)
        return results
