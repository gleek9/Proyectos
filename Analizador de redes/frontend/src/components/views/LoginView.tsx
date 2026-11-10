import React, { useState } from "react";
import { Sparkles, Lock, User, ArrowRight } from "lucide-react";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { api } from "../../api";

interface LoginViewProps {
  onSuccess: (username: string) => void;
}

export const LoginView: React.FC<LoginViewProps> = ({ onSuccess }) => {
  const [username, setUsername] = useState("Admin");
  const [password, setPassword] = useState("Admin");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const data = await api.login(username.trim(), password);
      localStorage.setItem("citi_auth_token", data.access_token);
      localStorage.setItem("citi_auth_user", data.username);
      onSuccess(data.username);
    } catch (err: any) {
      setError(err.message || "Error al iniciar sesión.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen w-full flex items-center justify-center p-4 bg-[#090A0D] bg-tech-grid overflow-hidden">
      {/* Resplandor técnico central muy sutil */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-[#58FF9C]/5 blur-[120px] rounded-full pointer-events-none" />

      {/* Tarjeta de Acceso Sobria */}
      <div className="relative w-full max-w-sm bg-[#111318] border border-[#1E222B] rounded-2xl p-7 sm:p-8 shadow-[0_20px_50px_rgba(0,0,0,0.7)] flex flex-col gap-6">
        {/* Identidad */}
        <div className="flex flex-col items-center text-center">
          <div className="w-12 h-12 rounded-xl bg-[#171A21] border border-[#1E222B] flex items-center justify-center text-[#58FF9C] shadow-[0_0_16px_rgba(88,255,156,0.12)] mb-4">
            <Sparkles size={22} strokeWidth={1.5} />
          </div>
          <h1 className="text-xl font-bold tracking-tight text-[#F8FAFC]">
            Citi Analyzer
          </h1>
          <p className="text-xs text-[#94A3B8] mt-1 font-mono">
            Acceso al Sistema de Inteligencia Viral
          </p>
        </div>

        {/* Mensaje de error */}
        {error && (
          <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/25 text-xs text-red-400 text-center">
            {error}
          </div>
        )}

        {/* Formulario */}
        <form onSubmit={handleLogin} className="flex flex-col gap-4">
          <Input
            label="Usuario"
            placeholder="Usuario del sistema"
            icon={<User size={15} strokeWidth={1.5} />}
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />

          <Input
            label="Contraseña"
            type="password"
            placeholder="••••••••"
            icon={<Lock size={15} strokeWidth={1.5} />}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          <div className="pt-2">
            <Button
              variant="primary"
              size="md"
              type="submit"
              className="w-full"
              loading={loading}
              icon={<ArrowRight size={16} strokeWidth={2} />}
            >
              Entrar al Hub
            </Button>
          </div>
        </form>

        {/* Credenciales sugeridas por defecto */}
        <div className="pt-3 border-t border-[#1E222B] text-center text-[11px] font-mono text-[#64748B]">
          Credenciales predeterminadas: <span className="text-[#94A3B8]">Admin / Admin</span>
        </div>
      </div>
    </div>
  );
};
