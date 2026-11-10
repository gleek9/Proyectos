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
          className="text-xs font-medium text-[#94A3B8] tracking-wide"
        >
          {label}
        </label>
      )}
      <div className="relative flex items-center">
        {icon && (
          <div className="absolute left-3 text-[#64748B] pointer-events-none flex items-center">
            {icon}
          </div>
        )}
        <input
          id={inputId}
          className={`w-full bg-[#111318] border border-[#1E222B] text-[#F8FAFC] text-sm rounded-lg px-3 py-2.5 placeholder:text-[#64748B] transition-all duration-150 focus:outline-none focus:border-[#58FF9C] focus:ring-1 focus:ring-[#58FF9C] disabled:opacity-50 disabled:cursor-not-allowed ${
            icon ? "pl-9" : ""
          } ${error ? "border-red-500 focus:border-red-500 focus:ring-red-500" : ""} ${className}`}
          {...props}
        />
      </div>
      {error && <span className="text-xs text-red-400 mt-0.5">{error}</span>}
    </div>
  );
};
