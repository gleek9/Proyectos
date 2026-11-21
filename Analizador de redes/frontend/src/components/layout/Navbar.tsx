import React from "react";
import { Plus, LogOut } from "lucide-react";
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
    <header className="sticky top-0 z-40 w-full bg-[#0B0C0E]/90 backdrop-blur-md border-b border-[#22242B]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <span className="text-sm font-semibold tracking-tight text-[#E4E5E9]">
            Social Analyzer
          </span>
          <span className="text-[11px] font-mono text-[#828794] border border-[#22242B] px-1.5 py-0.5 rounded">
            v2
          </span>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden md:flex items-center gap-2 px-2.5 py-1 rounded-md bg-[#121316] border border-[#22242B] text-[11px] font-mono text-[#9499A6]">
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                isHealthy ? "bg-[#6E857B]" : "bg-[#9E886B]"
              }`}
              aria-hidden="true"
            />
            <span>{isHealthy ? "En línea" : "Conectando"}</span>
          </div>

          <Button
            variant="primary"
            size="sm"
            icon={<Plus size={14} strokeWidth={2} />}
            onClick={onNewProfile}
          >
            Nuevo perfil
          </Button>

          <div className="flex items-center gap-2 pl-2 border-l border-[#22242B]">
            <span className="hidden lg:inline text-xs font-mono text-[#646975]">
              @{user}
            </span>
            <button
              onClick={onLogout}
              className="p-1.5 text-[#646975] hover:text-[#E4E5E9] rounded-lg hover:bg-[#191B20] transition-colors cursor-pointer"
              title="Cerrar sesión"
              aria-label="Cerrar sesión"
            >
              <LogOut size={15} strokeWidth={1.5} />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
