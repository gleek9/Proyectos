import React, { useState } from "react";
import { Plus, Trash2, Tag, Palette, Building } from "lucide-react";
import { Modal } from "../ui/Modal";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { InstagramIcon } from "../ui/InstagramIcon";
import { ProfileCreateInput } from "../../api";
import { CLIENT_COLOR_PALETTE, DEFAULT_CLIENT_COLOR } from "../../utils/clientColors";

interface CreateProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: ProfileCreateInput) => Promise<void>;
}

const MAX_REFERENCES = 10;

export const CreateProfileModal: React.FC<CreateProfileModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
}) => {
  const [clientName, setClientName] = useState("");
  const [category, setCategory] = useState("");
  const [representativeColor, setRepresentativeColor] = useState(DEFAULT_CLIENT_COLOR);
  const [clientInstagramUrl, setClientInstagramUrl] = useState("");
  const [competitorUrls, setCompetitorUrls] = useState<string[]>([""]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAddCompetitor = () => {
    if (competitorUrls.length < MAX_REFERENCES) {
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

    const filteredCompetitors = competitorUrls.map((u) => u.trim()).filter(Boolean).slice(0, MAX_REFERENCES);
    if (filteredCompetitors.length === 0) {
      setError("Agrega al menos una referencia o competidor para analizar.");
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
      setClientName("");
      setCategory("");
      setRepresentativeColor(DEFAULT_CLIENT_COLOR);
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
      title="Nuevo perfil"
      subtitle="Configura la marca y hasta 10 cuentas o Reels de referencia."
      accentColor={representativeColor}
      maxWidth="xl"
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        {error && (
          <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-400">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input
            label="Nombre del cliente"
            placeholder="ej. Inmobiliaria Domus"
            icon={<Building size={15} strokeWidth={1.5} />}
            value={clientName}
            onChange={(e) => setClientName(e.target.value)}
            required
          />

          <Input
            label="Categoría"
            placeholder="ej. Bienes Raíces, SaaS"
            icon={<Tag size={15} strokeWidth={1.5} />}
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            required
          />
        </div>

        <div className="flex flex-col gap-2">
          <label className="text-xs font-medium text-[#9499A6] flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <Palette size={13} strokeWidth={1.5} aria-hidden="true" />
              Color de cliente
            </span>
            <span className="font-mono text-[11px] text-[#828794]">
              {CLIENT_COLOR_PALETTE.find((c) => c.hex === representativeColor)?.label || representativeColor}
            </span>
          </label>
          <div className="flex items-center gap-2.5 flex-wrap">
            {CLIENT_COLOR_PALETTE.map((col) => (
              <button
                key={col.hex}
                type="button"
                onClick={() => setRepresentativeColor(col.hex)}
                className={`w-6 h-6 rounded-full border-2 transition-transform cursor-pointer focus:outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#E4E4E7] ${
                  representativeColor === col.hex
                    ? "border-[#F4F4F5] scale-110"
                    : "border-transparent opacity-75 hover:opacity-100"
                }`}
                style={{ backgroundColor: col.hex }}
                title={col.label}
                aria-label={col.label}
              />
            ))}
          </div>
        </div>

        <Input
          label="Instagram del cliente"
          placeholder="https://www.instagram.com/cliente/ o @cliente"
          icon={<InstagramIcon size={15} />}
          value={clientInstagramUrl}
          onChange={(e) => setClientInstagramUrl(e.target.value)}
          required
        />

        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <label className="text-xs font-medium text-[#9499A6]">
              Referencias ({competitorUrls.length}/{MAX_REFERENCES})
            </label>
            {competitorUrls.length < MAX_REFERENCES && (
              <button
                type="button"
                onClick={handleAddCompetitor}
                className="text-xs text-[#9499A6] hover:text-[#E4E5E9] flex items-center gap-1 font-mono transition-colors cursor-pointer"
              >
                <Plus size={13} strokeWidth={2} aria-hidden="true" />
                Agregar referencia
              </button>
            )}
          </div>

          <div className="flex flex-col gap-2 max-h-56 overflow-y-auto pr-1">
            {competitorUrls.map((url, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <span className="text-[11px] font-mono text-[#828794] w-5 text-right flex-shrink-0">
                  {idx + 1}.
                </span>
                <input
                  type="text"
                  placeholder="Cuenta (@usuario) o URL directa de Reel"
                  value={url}
                  onChange={(e) => handleCompetitorChange(idx, e.target.value)}
                  className="flex-1 bg-[#0B0C0E] border border-[#27272A] text-[#F4F4F5] rounded-lg px-3 py-2 placeholder:text-[#71717A] focus:outline-none focus:border-[#A1A1AA] font-mono text-xs"
                  required={idx === 0}
                />
                {competitorUrls.length > 1 && (
                  <button
                    type="button"
                    onClick={() => handleRemoveCompetitor(idx)}
                    className="p-2 text-[#828794] hover:text-red-400 rounded-lg hover:bg-[#191B20] transition-colors cursor-pointer"
                    title="Eliminar referencia"
                    aria-label="Eliminar referencia"
                  >
                    <Trash2 size={14} strokeWidth={1.5} />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="flex items-center justify-end gap-2.5 pt-4 border-t border-[#22242B] mt-1">
          <Button variant="ghost" type="button" onClick={onClose} disabled={loading}>
            Cancelar
          </Button>
          <Button variant="primary" type="submit" loading={loading}>
            Guardar perfil
          </Button>
        </div>
      </form>
    </Modal>
  );
};
