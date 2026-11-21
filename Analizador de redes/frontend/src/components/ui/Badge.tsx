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
          backgroundColor: `${colorHex}20`,
          color: colorHex,
          borderColor: `${colorHex}55`,
        }}
        className={`inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-mono font-medium tracking-wide border ${className}`}
      >
        {children}
      </span>
    );
  }

  const variantStyles: Record<string, string> = {
    accent: "bg-[#27272A] text-[#F4F4F5] border border-[#3F3F46]",
    neutral: "bg-[#18181B] text-[#A1A1AA] border border-[#27272A]",
    custom: "border",
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-mono tracking-wide ${
        variantStyles[variant] || variantStyles.neutral
      } ${className}`}
    >
      {children}
    </span>
  );
};
