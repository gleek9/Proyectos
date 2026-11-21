import React, { useState } from "react";
import { Lock, User, ArrowRight } from "lucide-react";
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
    <div className="min-h-screen w-full flex items-center justify-center p-4 bg-[#0B0C0E]">
      <div className="w-full max-w-sm bg-[#121316] border border-[#22242B] rounded-xl p-7 flex flex-col gap-6">
        <div className="flex flex-col gap-1">
          <div className="flex items-center justify-between text-[11px] font-mono text-[#828794]">
            <span>Social Analyzer</span>
            <span>v2</span>
          </div>
          <h1 className="text-lg font-semibold tracking-tight text-[#E4E5E9] mt-2">
            Iniciar sesión
          </h1>
          <p className="text-xs text-[#9499A6]">
            Inteligencia competitiva y guiones 60–90s.
          </p>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-400">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="flex flex-col gap-4">
          <Input
            label="Usuario"
            placeholder="Usuario"
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

          <Button
            variant="primary"
            size="md"
            type="submit"
            className="w-full mt-1"
            loading={loading}
            icon={<ArrowRight size={15} strokeWidth={2} />}
          >
            Entrar
          </Button>
        </form>

        <div className="pt-3 border-t border-[#22242B] text-[11px] font-mono text-[#646975] flex items-center justify-between">
          <span>Local</span>
          <span className="text-[#9499A6]">Admin / Admin</span>
        </div>
      </div>
    </div>
  );
};
