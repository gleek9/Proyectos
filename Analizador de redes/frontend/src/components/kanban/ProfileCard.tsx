import React from "react";
import { Users, Clock, ArrowUpRight } from "lucide-react";
import { ProfileListItem } from "../../api";
import { Badge } from "../ui/Badge";
import { InstagramIcon } from "../ui/InstagramIcon";
import { resolveClientColor } from "../../utils/clientColors";

interface ProfileCardProps {
  profile: ProfileListItem;
  onClick: () => void;
}

export const ProfileCard: React.FC<ProfileCardProps> = ({ profile, onClick }) => {
  const color = resolveClientColor(profile.representative_color);

  return (
    <div
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onClick();
        }
      }}
      style={{
        background: `linear-gradient(150deg, ${color}22 0%, #121316 55%)`,
        borderColor: `${color}38`,
      }}
      className="group relative flex flex-col justify-between min-h-[200px] bg-[#121316] border rounded-xl p-5 hover:brightness-110 transition-all duration-150 cursor-pointer overflow-hidden focus:outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#E4E4E7]"
    >
      <div
        className="absolute top-0 left-0 right-0 h-[3px]"
        style={{ backgroundColor: color }}
        aria-hidden="true"
      />

      <div>
        <div className="flex items-center justify-between gap-2 mb-4">
          <Badge variant="custom" colorHex={color}>
            {profile.category}
          </Badge>

          <span
            className="text-[#9499A6] group-hover:text-[#F4F4F5] transition-colors"
            aria-hidden="true"
          >
            <ArrowUpRight size={15} strokeWidth={1.5} />
          </span>
        </div>

        <div className="flex items-center gap-2.5 mb-1.5">
          <span
            className="w-2.5 h-2.5 rounded-full flex-shrink-0"
            style={{ backgroundColor: color }}
            aria-hidden="true"
          />
          <h3 className="text-base font-semibold text-[#F4F4F5] tracking-tight line-clamp-1">
            {profile.client_name}
          </h3>
        </div>

        <div className="flex items-center gap-1.5 text-xs text-[#9499A6] font-mono truncate">
          <InstagramIcon size={12} className="flex-shrink-0" />
          <span className="truncate">
            {profile.client_instagram_url.replace(/https?:\/\/(www\.)?instagram\.com\//, "@").replace(/\/$/, "")}
          </span>
        </div>
      </div>

      <div className="pt-3.5 mt-5 border-t border-[#27272A]/80 flex flex-col gap-1.5">
        <div className="flex items-center gap-1.5 text-xs text-[#A1A1AA]">
          <Users size={13} strokeWidth={1.5} className="text-[#828794]" aria-hidden="true" />
          <span>
            {profile.competitor_count} {profile.competitor_count === 1 ? "referencia" : "referencias"}
          </span>
        </div>

        <div className="flex items-center gap-1.5 text-[11px] font-mono text-[#828794]">
          <Clock size={12} strokeWidth={1.5} aria-hidden="true" />
          <span className="truncate">{profile.time_elapsed_label}</span>
        </div>
      </div>
    </div>
  );
};
