import React from "react";
import { Plus, Users } from "lucide-react";
import { Button } from "../ui/Button";

interface EmptyStateProps {
  onNewProfile: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ onNewProfile }) => {
  return (
    <div className="w-full max-w-2xl mx-auto my-16 border-2 border-dashed border-[#1E222B] rounded-2xl p-10 sm:p-14 text-center bg-[#111318]/40 flex flex-col items-center justify-center">
      <div className="w-12 h-12 rounded-xl bg-[#171A21] border border-[#1E222B] flex items-center justify-center text-[#58FF9C] mb-4 shadow-[0_0_16px_rgba(88,255,156,0.1)]">
        <Users size={22} strokeWidth={1.5} />
      </div>

      <h3 className="text-lg font-bold text-[#F8FAFC] tracking-tight mb-2">
        Sin perfiles registrados todavía
      </h3>

      <p className="text-sm text-[#94A3B8] max-w-md mb-6 leading-relaxed">
        Agrega la cuenta de Instagram de tu cliente y las URLs de sus competidores principales para comenzar a cazar virales y generar guiones adaptados.
      </p>

      <Button
        variant="primary"
        icon={<Plus size={16} strokeWidth={2} />}
        onClick={onNewProfile}
      >
        Crear Primer Perfil
      </Button>
    </div>
  );
};
