import React from "react";
import { Plus, Radio, LogOut, Sparkles } from "lucide-react";
import { Button } from "../ui/Button";
import { HealthStatus } from "../../api";

interface NavbarProps {
  health: HealthStatus | null;
  onNewProfile: () => void;
  onLogout: () => void;
  user: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  health,
  onNewProfile,
  onLogout,
  user,
}) => {
  const isHealthy = health?.status === "operational";

  return (
    <header className="sticky top-0 z-40 w-full bg-[#090A0D]/90 backdrop-blur-md border-b border-[#1E222B]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Marca y Logotipo Tipográfico */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-[#111318] border border-[#1E222B] flex items-center justify-center text-[#58FF9C] shadow-[0_0_12px_rgba(88,255,156,0.12)]">
            <Sparkles size={18} strokeWidth={1.5} />
          </div>
          <div>
            <span className="text-base font-bold tracking-tight text-[#F8FAFC]">
              Citi Analyzer
            </span>
            <span className="hidden sm:inline-block ml-2 text-[10px] font-mono text-[#64748B] border border-[#1E222B] px-1.5 py-0.5 rounded">
              ACE MVP
            </span>
          </div>
        </div>

        {/* Acciones y Monitor del Motor */}
        <div className="flex items-center gap-4">
          {/* Monitor de Estado de APIs */}
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#111318] border border-[#1E222B] text-xs font-mono">
            <span className="relative flex h-2 w-2">
              <span
                className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                  isHealthy ? "bg-[#58FF9C]" : "bg-amber-400"
                }`}
              />
              <span
                className={`relative inline-flex rounded-full h-2 w-2 ${
                  isHealthy ? "bg-[#58FF9C]" : "bg-amber-400"
                }`}
              />
            </span>
            <span className="text-[#94A3B8]">
              {isHealthy ? "Motor Gemini 3.0 & Apify Online" : "Conectando Motor..."}
            </span>
          </div>

          {/* Botón Primario + Nuevo Perfil */}
          <Button
            variant="primary"
            size="sm"
            icon={<Plus size={16} strokeWidth={2} />}
            onClick={onNewProfile}
          >
            Nuevo Perfil
          </Button>

          {/* Sesión y Salir */}
          <div className="flex items-center gap-2 pl-2 border-l border-[#1E222B]">
            <span className="hidden lg:inline text-xs font-mono text-[#64748B]">
              @{user}
            </span>
            <button
              onClick={onLogout}
              className="p-1.5 text-[#64748B] hover:text-red-400 rounded-lg hover:bg-[#171A21] transition-colors"
              title="Cerrar sesión"
            >
              <LogOut size={16} strokeWidth={1.5} />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
