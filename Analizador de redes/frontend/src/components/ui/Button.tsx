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
    "inline-flex items-center justify-center font-medium transition-colors duration-150 rounded-lg select-none cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#E4E4E7]";

  const sizeStyles = {
    sm: "text-xs px-2.5 py-1.5 gap-1.5",
    md: "text-sm px-3.5 py-2 gap-2",
    lg: "text-sm px-4 py-2.5 gap-2",
  };

  const variantStyles = {
    primary:
      "bg-[#F4F4F5] text-[#09090B] font-semibold hover:bg-[#E4E4E7]",
    secondary:
      "bg-[#18181B] text-[#E4E5E9] border border-[#27272A] hover:border-[#3F3F46] hover:bg-[#27272A]/70",
    ghost:
      "bg-transparent text-[#A1A1AA] hover:text-[#F4F4F5] hover:bg-[#18181B]",
    danger:
      "bg-red-500/10 text-red-400 border border-red-500/25 hover:bg-red-500/15",
  };

  return (
    <button
      className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <span className="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin" />
      ) : (
        icon && <span className="flex-shrink-0">{icon}</span>
      )}
      <span>{children}</span>
    </button>
  );
};
