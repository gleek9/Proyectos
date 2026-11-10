import React, { useState } from "react";
import { Plus, Trash2, Tag, Palette, Building } from "lucide-react";
import { Modal } from "../ui/Modal";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { InstagramIcon } from "../ui/InstagramIcon";
import { ProfileCreateInput } from "../../api";

interface CreateProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: ProfileCreateInput) => Promise<void>;
}

const PRESET_COLORS = [
  "#58FF9C", // Verde Eléctrico
  "#38BDF8", // Celeste Sky
  "#F59E0B", // Ámbar Oro
  "#A855F7", // Púrpura Editorial
  "#EC4899", // Rosa Intenso
  "#10B981", // Esmeralda
  "#F43F5E", // Carmesí
];

export const CreateProfileModal: React.FC<CreateProfileModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
}) => {
  const [clientName, setClientName] = useState("");
  const [category, setCategory] = useState("");
  const [representativeColor, setRepresentativeColor] = useState("#58FF9C");
  const [clientInstagramUrl, setClientInstagramUrl] = useState("");
  const [competitorUrls, setCompetitorUrls] = useState<string[]>([""]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAddCompetitor = () => {
    if (competitorUrls.length < 5) {
      setCompetitorUrls([...competitorUrls, ""]);
    }
  };

  const handleRemoveCompetitor = (index: number) => {
    setCompetitorUrls(competitorUrls.filter((_, i) => i !== index));
  };

  const handleCompetitorChange = (index: number, val: string) => {
    const updated = [...competitorUrls];
    updated[index] = val;
    setCompetitorUrls(updated);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!clientName.trim()) {
      setError("El nombre del cliente o marca es obligatorio.");
      return;
    }
    if (!category.trim()) {
      setError("La categoría de negocio es obligatoria.");
      return;
    }
    if (!clientInstagramUrl.trim()) {
      setError("La URL o cuenta de Instagram del cliente es obligatoria.");
      return;
    }

    const filteredCompetitors = competitorUrls.map((u) => u.trim()).filter(Boolean);
    if (filteredCompetitors.length === 0) {
      setError("Agrega al menos una URL de competidor a analizar.");
      return;
    }

    setError(null);
    setLoading(true);
    try {
      await onSubmit({
        client_name: clientName.trim(),
        category: category.trim(),
        representative_color: representativeColor,
        client_instagram_url: clientInstagramUrl.trim(),
        competitor_urls: filteredCompetitors,
      });
      // Limpiar formulario y cerrar
      setClientName("");
      setCategory("");
      setClientInstagramUrl("");
      setCompetitorUrls([""]);
      onClose();
    } catch (err: any) {
      setError(err.message || "Error al registrar el perfil.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Nuevo Perfil de Cliente"
      subtitle="Configura el cliente y sus competidores para la inteligencia de guiones virales."
      maxWidth="xl"
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        {error && (
          <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/25 text-xs text-red-400">
            {error}
          </div>
        )}

        {/* 1. Nombre del Cliente y Categoría */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input
            label="Nombre del Cliente / Marca"
            placeholder="ej. Inmobiliaria Domus"
            icon={<Building size={16} strokeWidth={1.5} />}
            value={clientName}
            onChange={(e) => setClientName(e.target.value)}
            required
          />

          <Input
            label="Categoría de Negocio"
            placeholder="ej. Bienes Raíces, Gastronomía"
            icon={<Tag size={16} strokeWidth={1.5} />}
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            required
          />
        </div>

        {/* 2. Color Representativo del Cliente */}
        <div className="flex flex-col gap-2">
          <label className="text-xs font-medium text-[#94A3B8] tracking-wide flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <Palette size={14} strokeWidth={1.5} />
              Color Representativo
            </span>
            <span className="font-mono text-[11px] text-[#58FF9C]">{representativeColor}</span>
          </label>
          <div className="flex items-center gap-2.5 flex-wrap">
            {PRESET_COLORS.map((col) => (
              <button
                key={col}
                type="button"
                onClick={() => setRepresentativeColor(col)}
                className={`w-7 h-7 rounded-full border-2 transition-all ${
                  representativeColor === col
                    ? "border-white scale-110 shadow-[0_0_10px_rgba(255,255,255,0.4)]"
                    : "border-transparent opacity-75 hover:opacity-100"
                }`}
                style={{ backgroundColor: col }}
                title={col}
              />
            ))}
            <input
              type="color"
              value={representativeColor}
              onChange={(e) => setRepresentativeColor(e.target.value)}
              className="w-7 h-7 rounded-full bg-transparent border-0 cursor-pointer p-0"
              title="Color personalizado"
            />
          </div>
        </div>

        {/* 3. URL de Instagram del Cliente */}
        <Input
          label="URL o Usuario de Instagram del Cliente"
          placeholder="https://www.instagram.com/cliente/ o @cliente"
          icon={<InstagramIcon size={16} />}
          value={clientInstagramUrl}
          onChange={(e) => setClientInstagramUrl(e.target.value)}
          required
        />

        {/* 4. URLs Dinámicas de Competidores */}
        <div className="flex flex-col gap-2.5">
          <div className="flex items-center justify-between">
            <label className="text-xs font-medium text-[#94A3B8] tracking-wide">
              URLs de Competidores a Analizar ({competitorUrls.length}/5)
            </label>
            {competitorUrls.length < 5 && (
              <button
                type="button"
                onClick={handleAddCompetitor}
                className="text-xs text-[#58FF9C] hover:text-[#42E686] flex items-center gap-1 font-mono transition-colors"
              >
                <Plus size={13} strokeWidth={2} />
                Agregar otro
              </button>
            )}
          </div>

          <div className="flex flex-col gap-2 max-h-48 overflow-y-auto pr-1">
            {competitorUrls.map((url, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <input
                  type="text"
                  placeholder={`ej. https://www.instagram.com/competidor_${idx + 1}/`}
                  value={url}
                  onChange={(e) => handleCompetitorChange(idx, e.target.value)}
                  className="flex-1 bg-[#111318] border border-[#1E222B] text-[#F8FAFC] text-sm rounded-lg px-3 py-2 placeholder:text-[#64748B] focus:outline-none focus:border-[#58FF9C] font-mono text-xs"
                  required={idx === 0}
                />
                {competitorUrls.length > 1 && (
                  <button
                    type="button"
                    onClick={() => handleRemoveCompetitor(idx)}
                    className="p-2 text-[#64748B] hover:text-red-400 rounded-lg hover:bg-[#111318] transition-colors"
                    title="Eliminar competidor"
                  >
                    <Trash2 size={15} strokeWidth={1.5} />
                  </button>
                )}
              </div>
            ))}
          </div>
          <p className="text-[11px] text-[#64748B]">
            La IA rastreará los Reels con mayor viralidad de estos competidores y adaptará su gancho al cliente.
          </p>
        </div>

        {/* Botones de Acción */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-[#1E222B] mt-2">
          <Button variant="ghost" type="button" onClick={onClose} disabled={loading}>
            Cancelar
          </Button>
          <Button variant="primary" type="submit" loading={loading}>
            Guardar Perfil
          </Button>
        </div>
      </form>
    </Modal>
  );
};
