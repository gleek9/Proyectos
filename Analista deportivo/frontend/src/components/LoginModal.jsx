import React, { useState } from 'react';
import { Lock, AlertCircle, ArrowRight, User } from 'lucide-react';

export default function LoginModal({ onLoginSuccess }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError('Por favor ingresa usuario y contraseña.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      let res;
      try {
        res = await fetch('/api/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            username: username.trim(),
            password: password.trim()
          })
        });
      } catch {
        res = await fetch('http://127.0.0.1:8000/api/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            username: username.trim(),
            password: password.trim()
          })
        });
      }

      if (res && (res.status === 502 || res.status === 503 || res.status === 504)) {
        await new Promise(r => setTimeout(r, 1200));
        res = await fetch('http://127.0.0.1:8000/api/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            username: username.trim(),
            password: password.trim()
          })
        }).catch(() => res);
      }

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        if (res.status === 502 || res.status === 503 || res.status === 504) {
          throw new Error(`El servidor backend no está respondiendo (HTTP ${res.status}). Espera a que termine de iniciar.`);
        }
        throw new Error(data.detail || 'Credenciales inválidas');
      }

      // Guardar token y usuario en localStorage
      localStorage.setItem('katakuri_token', data.access_token);
      localStorage.setItem('katakuri_user', data.username);
      onLoginSuccess(data.username);
    } catch (err) {
      if (err.message === 'Failed to fetch') {
        setError('No se pudo conectar con el servidor backend (http://127.0.0.1:8000). Asegúrate de que el servidor esté activo.');
      } else {
        setError(err.message || 'Error autenticando credenciales');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page-backdrop">
      <div className="login-card">
        {/* Header del Login */}
        <div className="login-header-group">
          <div className="login-brand-icon">
            <Lock size={20} color="var(--azure)" />
          </div>
          <div>
            <div className="login-brand-title">
              Katakuri · Acceso al sistema
            </div>
            <div className="login-brand-sub">
              Autenticación requerida para acceder al analista
            </div>
          </div>
        </div>

        {/* Mensaje de Error */}
        {error && (
          <div style={{
            background: 'rgba(244, 63, 94, 0.12)',
            border: '1px solid var(--crimson)',
            color: '#fca5a5',
            padding: '0.65rem 0.85rem',
            borderRadius: '6px',
            fontSize: '0.8rem',
            fontFamily: 'var(--font-mono)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            <AlertCircle size={15} color="var(--crimson)" />
            <span>{error}</span>
          </div>
        )}

        {/* Formulario */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="login-input-group">
            <label className="login-input-label">
              Usuario
            </label>
            <div className="login-input-box">
              <User size={15} color="var(--text-dim)" />
              <input
                id="login-username-input"
                type="text"
                className="login-input-field"
                placeholder="Nombre de usuario"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                disabled={loading}
                required
              />
            </div>
          </div>

          <div className="login-input-group">
            <label className="login-input-label">
              Contraseña
            </label>
            <div className="login-input-box">
              <Lock size={15} color="var(--text-dim)" />
              <input
                id="login-password-input"
                type="password"
                className="login-input-field"
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                disabled={loading}
                required
              />
            </div>
          </div>

          <button
            id="login-submit-btn"
            type="submit"
            className="login-submit-btn"
            disabled={loading}
          >
            {loading ? (
              <span>Verificando credenciales...</span>
            ) : (
              <>
                <span>Iniciar sesión</span>
                <ArrowRight size={15} />
              </>
            )}
          </button>
        </form>

        <div className="login-footer-meta">
          <span>Conexión segura JWT</span>
          <span>Katakuri v3.5</span>
        </div>
      </div>
    </div>
  );
}
