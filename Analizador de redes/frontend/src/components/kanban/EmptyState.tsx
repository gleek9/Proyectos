import React from "react";
import { Plus, Users } from "lucide-react";
import { Button } from "../ui/Button";

interface EmptyStateProps {
  onNewProfile: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ onNewProfile }) => {
  return (
    <div className="w-full max-w-xl mx-auto my-16 border border-dashed border-[#22242B] rounded-xl p-10 text-center bg-[#121316]/50 flex flex-col items-center justify-center">
      <div className="w-10 h-10 rounded-lg bg-[#191B20] border border-[#22242B] flex items-center justify-center text-[#9499A6] mb-4">
        <Users size={18} strokeWidth={1.5} />
      </div>

      <h3 className="text-base font-semibold text-[#E4E5E9] tracking-tight mb-1.5">
        Sin perfiles registrados
      </h3>

      <p className="text-xs text-[#9499A6] max-w-sm mb-5 leading-relaxed">
        Agrega un cliente y hasta 10 referencias para generar guiones de 60 a 90 segundos.
      </p>

      <Button
        variant="primary"
        size="sm"
        icon={<Plus size={15} strokeWidth={2} />}
        onClick={onNewProfile}
      >
        Crear primer perfil
      </Button>
    </div>
  );
};
