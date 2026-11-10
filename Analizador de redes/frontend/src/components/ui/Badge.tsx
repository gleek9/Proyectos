import React from "react";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "accent" | "neutral" | "custom";
  colorHex?: string;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = "neutral",
  colorHex,
  className = "",
}) => {
  if (variant === "custom" && colorHex) {
    return (
      <span
        style={{
          backgroundColor: `${colorHex}18`, // 10-12% opacidad
          color: colorHex,
          borderColor: `${colorHex}30`,
        }}
        className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono uppercase tracking-wider border ${className}`}
      >
        {children}
      </span>
    );
  }

  const variantStyles: Record<string, string> = {
    accent:
      "bg-[#58FF9C]/10 text-[#58FF9C] border border-[#58FF9C]/25 shadow-[0_0_8px_rgba(88,255,156,0.08)]",
    neutral: "bg-[#171A21] text-[#94A3B8] border border-[#1E222B]",
    custom: "border",
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono uppercase tracking-wider ${
        variantStyles[variant] || variantStyles.neutral
      } ${className}`}
    >
      {children}
    </span>
  );
};
