import React from "react";
import { Users, Clock, ArrowUpRight } from "lucide-react";
import { ProfileListItem } from "../../api";
import { Badge } from "../ui/Badge";
import { InstagramIcon } from "../ui/InstagramIcon";

interface ProfileCardProps {
  profile: ProfileListItem;
  onClick: () => void;
}

export const ProfileCard: React.FC<ProfileCardProps> = ({ profile, onClick }) => {
  const color = profile.representative_color || "#58FF9C";

  return (
    <div
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") onClick();
      }}
      className="group relative flex flex-col justify-between bg-[#111318] border border-[#1E222B] rounded-xl p-5 hover:border-[#58FF9C]/50 hover:bg-[#14171E] transition-all duration-200 cursor-pointer overflow-hidden shadow-[0_4px_20px_rgba(0,0,0,0.35)] hover:shadow-[0_8px_30px_rgba(0,0,0,0.5)] aspect-square"
    >
      {/* Barra superior de 3px con el color representativo del cliente */}
      <div
        className="absolute top-0 left-0 right-0 h-[3px] transition-opacity duration-200"
        style={{ backgroundColor: color }}
      />

      {/* Cabecera de la Tarjeta Kanban */}
      <div>
        <div className="flex items-center justify-between gap-2 mb-3">
          {/* Badge de Categoría */}
          <Badge variant="custom" colorHex={color}>
            {profile.category}
          </Badge>

          {/* Flecha indicadora de apertura en hover */}
          <span className="text-[#64748B] group-hover:text-[#58FF9C] transition-colors">
            <ArrowUpRight size={16} strokeWidth={1.5} />
          </span>
        </div>

        {/* Nombre del Cliente con Dot Indicador de 8px */}
        <div className="flex items-center gap-2.5 mb-2">
          <span
            className="w-2 h-2 rounded-full flex-shrink-0"
            style={{ backgroundColor: color }}
          />
          <h3 className="text-base font-bold text-[#F8FAFC] tracking-tight group-hover:text-white line-clamp-1">
            {profile.client_name}
          </h3>
        </div>

        {/* URL / Handle de Instagram del Cliente */}
        <div className="flex items-center gap-1.5 text-xs text-[#94A3B8] font-mono truncate">
          <InstagramIcon size={13} className="flex-shrink-0 text-[#64748B]" />
          <span className="truncate">
            {profile.client_instagram_url.replace(/https?:\/\/(www\.)?instagram\.com\//, "@").replace(/\/$/, "")}
          </span>
        </div>
      </div>

      {/* Pie de la Tarjeta: Competidores y Leyenda Dinámica de Tiempo */}
      <div className="pt-4 border-t border-[#1E222B]/80 flex flex-col gap-2">
        {/* Contador de Competidores */}
        <div className="flex items-center justify-between text-xs text-[#94A3B8]">
          <span className="flex items-center gap-1.5">
            <Users size={13} strokeWidth={1.5} className="text-[#64748B]" />
            <span>{profile.competitor_count} {profile.competitor_count === 1 ? "competidor" : "competidores"}</span>
          </span>
        </div>

        {/* Leyenda Dinámica de Tiempo */}
        <div className="flex items-center gap-1.5 text-[11px] font-mono text-[#64748B]">
          <Clock size={12} strokeWidth={1.5} className="text-[#64748B]" />
          <span className="truncate">{profile.time_elapsed_label}</span>
        </div>
      </div>
    </div>
  );
};
