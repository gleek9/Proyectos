import React, { useState } from 'react';
import { Lock, ShieldCheck, AlertCircle, ArrowRight, User } from 'lucide-react';

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
      } catch (netErr) {
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
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: 'var(--bg-base)',
      padding: '1.5rem'
    }}>
      <div style={{
        width: '100%',
        maxWidth: '420px',
        backgroundColor: 'var(--bg-panel)',
        border: '1px solid var(--border-dim)',
        borderRadius: '8px',
        padding: '2rem 1.75rem',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.45)',
        display: 'flex',
        flexDirection: 'column',
        gap: '1.5rem'
      }}>
        {/* Header del Login */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            background: 'rgba(56, 189, 248, 0.1)',
            border: '1px solid var(--cyan)',
            padding: '0.5rem',
            borderRadius: '6px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Lock size={20} color="var(--cyan)" />
          </div>
          <div>
            <div style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '1.15rem',
              fontWeight: 700,
              color: 'var(--text-main)',
              letterSpacing: '-0.02em'
            }}>
              KATAKURI // ACCESO
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
              Autenticación requerida para acceder al analista
            </div>
          </div>
        </div>

        {/* Mensaje de Error */}
        {error && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.12)',
            border: '1px solid var(--red)',
            color: '#fca5a5',
            padding: '0.65rem 0.85rem',
            borderRadius: '6px',
            fontSize: '0.8rem',
            fontFamily: 'var(--font-mono)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            <AlertCircle size={15} color="var(--red)" />
            <span>{error}</span>
          </div>
        )}

        {/* Formulario */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
            <label style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.75rem',
              color: 'var(--text-secondary)',
              textTransform: 'uppercase'
            }}>
              Usuario
            </label>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              background: 'var(--bg-input)',
              border: '1px solid var(--border-dim)',
              borderRadius: '6px',
              padding: '0.55rem 0.75rem',
              gap: '0.5rem'
            }}>
              <User size={15} color="var(--text-dim)" />
              <input
                id="login-username-input"
                type="text"
                placeholder="Nombre de usuario"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                disabled={loading}
                style={{
                  background: 'transparent',
                  border: 'none',
                  outline: 'none',
                  color: 'var(--text-main)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.85rem',
                  width: '100%'
                }}
                required
              />
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
            <label style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.75rem',
              color: 'var(--text-secondary)',
              textTransform: 'uppercase'
            }}>
              Contraseña
            </label>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              background: 'var(--bg-input)',
              border: '1px solid var(--border-dim)',
              borderRadius: '6px',
              padding: '0.55rem 0.75rem',
              gap: '0.5rem'
            }}>
              <Lock size={15} color="var(--text-dim)" />
              <input
                id="login-password-input"
                type="password"
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                disabled={loading}
                style={{
                  background: 'transparent',
                  border: 'none',
                  outline: 'none',
                  color: 'var(--text-main)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.85rem',
                  width: '100%'
                }}
                required
              />
            </div>
          </div>

          <button
            id="login-submit-btn"
            type="submit"
            disabled={loading}
            style={{
              background: 'var(--cyan)',
              color: '#050508',
              border: 'none',
              borderRadius: '6px',
              padding: '0.65rem',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.85rem',
              fontWeight: 700,
              cursor: loading ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem',
              marginTop: '0.5rem',
              transition: 'all 0.15s ease'
            }}
          >
            {loading ? (
              <span>VERIFICANDO CREDENCIALES...</span>
            ) : (
              <>
                <span>ACCEDER A LA TERMINAL</span>
                <ArrowRight size={15} />
              </>
            )}
          </button>
        </form>

        <div style={{
          borderTop: '1px solid var(--border-dim)',
          paddingTop: '0.75rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.7rem',
          color: 'var(--text-muted)'
        }}>
          <span>ESTADO: ENTORNO PROTEGIDO</span>
          <span>KATAKURI v3.0</span>
        </div>
      </div>
    </div>
  );
}
