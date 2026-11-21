import React from "react";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  icon,
  className = "",
  id,
  ...props
}) => {
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);

  return (
    <div className="w-full flex flex-col gap-1.5">
      {label && (
        <label
          htmlFor={inputId}
          className="text-xs font-medium text-[#9499A6]"
        >
          {label}
        </label>
      )}
      <div className="relative flex items-center">
        {icon && (
          <div className="absolute left-3 text-[#646975] pointer-events-none flex items-center">
            {icon}
          </div>
        )}
        <input
          id={inputId}
          className={`w-full bg-[#09090B] border border-[#27272A] text-[#F4F4F5] text-sm rounded-lg px-3 py-2.5 placeholder:text-[#71717A] transition-colors duration-150 focus:outline-none focus:border-[#A1A1AA] disabled:opacity-50 disabled:cursor-not-allowed ${
            icon ? "pl-9" : ""
          } ${error ? "border-red-500/80 focus:border-red-500" : ""} ${className}`}
          {...props}
        />
      </div>
      {error && <span className="text-xs text-red-400 mt-0.5">{error}</span>}
    </div>
  );
};
