import React from "react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  icon?: React.ReactNode;
  loading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = "primary",
  size = "md",
  icon,
  loading = false,
  className = "",
  disabled,
  ...props
}) => {
  const baseStyles =
    "inline-flex items-center justify-center font-medium transition-all duration-150 rounded-lg select-none disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-[#58FF9C]/40";

  const sizeStyles = {
    sm: "text-xs px-2.5 py-1.5 gap-1.5",
    md: "text-sm px-3.5 py-2 gap-2",
    lg: "text-base px-4 py-2.5 gap-2.5",
  };

  const variantStyles = {
    primary:
      "bg-[#58FF9C] text-[#090A0D] font-semibold hover:bg-[#42E686] active:scale-[0.98] shadow-[0_0_12px_rgba(88,255,156,0.18)] hover:shadow-[0_0_18px_rgba(88,255,156,0.28)]",
    secondary:
      "bg-[#171A21] text-[#F8FAFC] border border-[#1E222B] hover:border-[#58FF9C]/40 hover:bg-[#1E222B] active:scale-[0.98]",
    ghost:
      "bg-transparent text-[#94A3B8] hover:text-[#F8FAFC] hover:bg-[#171A21] active:scale-[0.98]",
    danger:
      "bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 active:scale-[0.98]",
  };

  return (
    <button
      className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
      ) : (
        icon && <span className="flex-shrink-0">{icon}</span>
      )}
      <span>{children}</span>
    </button>
  );
};
