import React, { useEffect } from "react";
import { X } from "lucide-react";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  children: React.ReactNode;
  maxWidth?: "sm" | "md" | "lg" | "xl" | "2xl" | "4xl" | "6xl";
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  subtitle,
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
      {/* Backdrop con desenfoque técnico */}
      <div
        className="fixed inset-0 bg-[#090A0D]/85 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Ventana Modal Elevada */}
      <div
        className={`relative w-full ${maxWidthStyles[maxWidth]} bg-[#171A21] border border-[#1E222B] rounded-xl shadow-[0_24px_50px_-12px_rgba(0,0,0,0.85)] z-10 flex flex-col max-h-[90vh] overflow-hidden`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Cabecera del Modal */}
        {(title || subtitle) && (
          <div className="flex items-start justify-between p-5 border-b border-[#1E222B] bg-[#111318]/50">
            <div>
              {typeof title === "string" ? (
                <h3 className="text-lg font-bold text-[#F8FAFC] tracking-tight">{title}</h3>
              ) : (
                title
              )}
              {subtitle && (
                <div className="text-xs text-[#94A3B8] mt-1">{subtitle}</div>
              )}
            </div>
            <button
              onClick={onClose}
              className="text-[#64748B] hover:text-[#F8FAFC] p-1.5 rounded-lg hover:bg-[#1E222B] transition-colors"
              aria-label="Cerrar modal"
            >
              <X size={18} strokeWidth={1.5} />
            </button>
          </div>
        )}

        {/* Contenido scrolleable */}
        <div className="p-5 sm:p-6 overflow-y-auto flex-1">{children}</div>
      </div>
    </div>
  );
};
