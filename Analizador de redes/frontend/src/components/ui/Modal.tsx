import React, { useEffect } from "react";
import { X } from "lucide-react";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  accentColor?: string;
  children: React.ReactNode;
  maxWidth?: "sm" | "md" | "lg" | "xl" | "2xl" | "4xl" | "6xl";
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  subtitle,
  accentColor,
  children,
  maxWidth = "xl",
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      document.body.style.overflow = "hidden";
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => {
      document.body.style.overflow = "unset";
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const maxWidthStyles = {
    sm: "max-w-sm",
    md: "max-w-md",
    lg: "max-w-lg",
    xl: "max-w-xl",
    "2xl": "max-w-2xl",
    "4xl": "max-w-4xl",
    "6xl": "max-w-6xl",
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
      <div
        className="fixed inset-0 bg-[#0B0C0E]/82 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      <div
        className={`relative w-full ${maxWidthStyles[maxWidth]} bg-[#121316] border border-[#22242B] rounded-xl z-10 flex flex-col max-h-[90vh] overflow-hidden`}
        onClick={(e) => e.stopPropagation()}
      >
        {accentColor && (
          <div
            className="h-[3px] w-full flex-shrink-0"
            style={{ backgroundColor: accentColor }}
          />
        )}

        {(title || subtitle) && (
          <div
            className="flex items-start justify-between px-6 py-4 border-b border-[#27272A]"
            style={
              accentColor
                ? { background: `linear-gradient(180deg, ${accentColor}16 0%, transparent 100%)` }
                : undefined
            }
          >
            <div className="min-w-0">
              {typeof title === "string" ? (
                <h3 className="text-base font-semibold text-[#E4E5E9] tracking-tight">{title}</h3>
              ) : (
                title
              )}
              {subtitle && (
                <div className="text-xs text-[#9499A6] mt-1">{subtitle}</div>
              )}
            </div>
            <button
              onClick={onClose}
              className="text-[#646975] hover:text-[#E4E5E9] p-1.5 rounded-lg hover:bg-[#191B20] transition-colors cursor-pointer"
              aria-label="Cerrar modal"
            >
              <X size={18} strokeWidth={1.5} />
            </button>
          </div>
        )}

        <div className="p-6 overflow-y-auto flex-1">{children}</div>
      </div>
    </div>
  );
};
