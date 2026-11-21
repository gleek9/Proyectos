import React, { useState, useEffect } from "react";
import {
  ExternalLink,
  Sparkles,
  Copy,
  Check,
  Trash2,
  FileText,
  ChevronRight,
  RefreshCw,
  Plus,
  Pencil,
  Save,
  X,
} from "lucide-react";
import { Modal } from "../ui/Modal";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";
import { ProfileDetail, ScriptProposal, TimelineBlock } from "../../api";
import { CLIENT_COLOR_PALETTE, resolveClientColor } from "../../utils/clientColors";

interface ProfileDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  profile: ProfileDetail | null;
  onAnalyze: (id: number) => Promise<void>;
  onUpdateProfile: (id: number, references: string[], color: string) => Promise<void>;
  onDelete: (id: number) => Promise<void>;
  analyzing: boolean;
}

const MAX_REFERENCES = 10;

const ANALYSIS_STEPS = [
  "1. Voz del cliente",
  "2. Hasta 10 referencias",
  "3. Transcripción",
  "4. Guiones 60–90s",
];

function getUnifiedSections(proposal: ScriptProposal): TimelineBlock[] {
  const blocks = proposal.escalation_timeline || [];
  if (blocks.length === 0) {
    return [
      {
        time_range: "00:00 - 01:15",
        phase: "Guion completo",
        description: "Lectura directa a cámara con cortes dinámicos cada 3-4 segundos.",
        spoken_text: proposal.full_script,
      },
    ];
  }

  const allHaveSpoken = blocks.every((b) => Boolean(b.spoken_text && b.spoken_text.trim()));
  if (allHaveSpoken) {
    return blocks;
  }

  const raw = (proposal.full_script || "").trim();
  const paragraphs = raw.split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean);
  const chunks =
    paragraphs.length >= blocks.length
      ? paragraphs
      : raw
          .split(/(?<=[.!?])\s+/)
          .reduce<string[]>((acc, sentence, idx, arr) => {
            const bucket = Math.min(blocks.length - 1, Math.floor((idx * blocks.length) / Math.max(1, arr.length)));
            acc[bucket] = acc[bucket] ? `${acc[bucket]} ${sentence}` : sentence;
            return acc;
          }, []);

  return blocks.map((block, idx) => ({
    ...block,
    spoken_text: block.spoken_text?.trim() || chunks[idx] || "",
  }));
}

function extractSpokenOnly(proposal: ScriptProposal): string {
  return getUnifiedSections(proposal)
    .map((b) => b.spoken_text?.trim())
    .filter(Boolean)
    .join("\n\n");
}

function buildUnifiedClipboardText(proposal: ScriptProposal): string {
  return getUnifiedSections(proposal)
    .map((b) => {
      const screen = b.on_screen_text ? ` · Texto en pantalla: "${b.on_screen_text}"` : "";
      return `[${b.time_range} · ${b.phase}]\nVisual: ${b.description}${screen}\nQué decir: ${b.spoken_text || ""}`;
    })
    .join("\n\n");
}

function estimateWordCount(sections: TimelineBlock[]): number {
  return sections.reduce((sum, s) => sum + ((s.spoken_text || "").trim().split(/\s+/).filter(Boolean).length), 0);
}

export const ProfileDetailModal: React.FC<ProfileDetailModalProps> = ({
  isOpen,
  onClose,
  profile,
  onAnalyze,
  onUpdateProfile,
  onDelete,
  analyzing,
}) => {
  const [selectedProposalIdx, setSelectedProposalIdx] = useState(0);
  const [copiedMode, setCopiedMode] = useState<"unified" | "spoken" | null>(null);
  const [deleting, setDeleting] = useState(false);

  const [editingRefs, setEditingRefs] = useState(false);
  const [draftRefs, setDraftRefs] = useState<string[]>([]);
  const [draftColor, setDraftColor] = useState("");
  const [savingRefs, setSavingRefs] = useState(false);

  useEffect(() => {
    if (profile) {
      setDraftRefs(profile.competitor_urls.length > 0 ? profile.competitor_urls : [""]);
      setDraftColor(resolveClientColor(profile.representative_color));
      setEditingRefs(false);
      setSelectedProposalIdx(0);
    }
  }, [profile?.id]);

  if (!profile) return null;

  const color = editingRefs ? draftColor : resolveClientColor(profile.representative_color);
  const proposals = profile.proposals || [];
  const selectedProposal: ScriptProposal | undefined = proposals[selectedProposalIdx];
  const unifiedSections = selectedProposal ? getUnifiedSections(selectedProposal) : [];
  const wordCount = estimateWordCount(unifiedSections);

  const handleCopy = (text: string, mode: "unified" | "spoken") => {
    navigator.clipboard.writeText(text);
    setCopiedMode(mode);
    setTimeout(() => setCopiedMode(null), 2200);
  };

  const handleDelete = async () => {
    if (confirm(`¿Eliminar el perfil de "${profile.client_name}"?`)) {
      setDeleting(true);
      try {
        await onDelete(profile.id);
        onClose();
      } finally {
        setDeleting(false);
      }
    }
  };

  const handleSaveSettings = async () => {
    const cleaned = draftRefs.map((u) => u.trim()).filter(Boolean).slice(0, MAX_REFERENCES);
    if (cleaned.length === 0) return;
    setSavingRefs(true);
    try {
      await onUpdateProfile(profile.id, cleaned, draftColor);
      setEditingRefs(false);
    } finally {
      setSavingRefs(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      maxWidth="6xl"
      accentColor={color}
      title={
        <div className="flex flex-wrap items-center gap-2.5">
          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} aria-hidden="true" />
          <span className="text-lg font-semibold text-[#E4E5E9] tracking-tight">
            {profile.client_name}
          </span>
          <Badge variant="custom" colorHex={color}>
            {profile.category}
          </Badge>
        </div>
      }
      subtitle={
        <div className="flex flex-wrap items-center gap-3 text-xs text-[#9499A6] font-mono mt-1">
          <a
            href={profile.client_instagram_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 hover:text-[#E4E5E9] transition-colors"
          >
            <span>Instagram</span>
            <ExternalLink size={11} strokeWidth={1.5} aria-hidden="true" />
          </a>
          <span className="text-[#2F323B]">/</span>
          <span>{profile.competitor_urls.length}/{MAX_REFERENCES} referencias</span>
          <span className="text-[#2F323B]">/</span>
          <span className="text-[#828794]">{profile.time_elapsed_label}</span>
        </div>
      }
    >
      <div className="flex flex-col gap-5">
        {/* Cabecera de referencias y acción principal */}
        <div className="flex flex-col gap-3 p-4 rounded-xl bg-[#0B0C0E] border border-[#22242B]">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-[#828794]">
                Referencias ({profile.competitor_urls.length}/{MAX_REFERENCES})
              </span>
              {!editingRefs && (
                <button
                  type="button"
                  onClick={() => {
                    setDraftRefs(profile.competitor_urls.length > 0 ? [...profile.competitor_urls] : [""]);
                    setDraftColor(resolveClientColor(profile.representative_color));
                    setEditingRefs(true);
                  }}
                  className="inline-flex items-center gap-1 text-[11px] font-mono text-[#9499A6] hover:text-[#E4E5E9] px-2 py-0.5 rounded border border-[#22242B] hover:border-[#2F323B] transition-colors cursor-pointer"
                >
                  <Pencil size={11} strokeWidth={1.5} aria-hidden="true" />
                  <span>Editar</span>
                </button>
              )}
            </div>

            <div className="flex items-center gap-2 flex-shrink-0">
              <Button
                variant="primary"
                size="sm"
                icon={analyzing ? <RefreshCw className="animate-spin" size={14} /> : <Sparkles size={14} strokeWidth={1.5} />}
                onClick={() => onAnalyze(profile.id)}
                loading={analyzing}
              >
                {proposals.length > 0 ? "Actualizar análisis" : "Analizar y generar guiones"}
              </Button>

              <button
                onClick={handleDelete}
                disabled={deleting || analyzing}
                className="p-2 text-[#828794] hover:text-red-400 rounded-lg hover:bg-[#191B20] border border-[#22242B] transition-colors cursor-pointer"
                title="Eliminar perfil"
                aria-label="Eliminar perfil"
              >
                <Trash2 size={15} strokeWidth={1.5} />
              </button>
            </div>
          </div>

          {!editingRefs ? (
            <div className="flex flex-wrap items-center gap-2">
              {profile.competitor_urls.map((u, i) => {
                const handle = u
                  .replace(/https?:\/\/(www\.)?instagram\.com\//, "@")
                  .replace(/\/$/, "");
                const href = u.startsWith("http") ? u : `https://www.instagram.com/${u.replace(/^@/, "")}/`;
                return (
                  <a
                    key={i}
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#121316] border border-[#22242B] text-xs font-mono text-[#9499A6] hover:text-[#E4E5E9] hover:border-[#2F323B] transition-colors"
                  >
                    <span className="truncate max-w-[200px]">{handle}</span>
                    <ExternalLink size={10} strokeWidth={1.5} aria-hidden="true" />
                  </a>
                );
              })}
            </div>
          ) : (
            <div className="flex flex-col gap-3 pt-1">
              <div className="flex items-center gap-2.5 flex-wrap pb-2 border-b border-[#22242B]">
                <span className="text-[11px] font-mono text-[#828794]">Color:</span>
                {CLIENT_COLOR_PALETTE.map((col) => (
                  <button
                    key={col.hex}
                    type="button"
                    onClick={() => setDraftColor(col.hex)}
                    className={`w-5 h-5 rounded-full border-2 transition-transform cursor-pointer ${
                      draftColor === col.hex ? "border-[#E4E5E9] scale-110" : "border-transparent opacity-70 hover:opacity-100"
                    }`}
                    style={{ backgroundColor: col.hex }}
                    title={col.label}
                    aria-label={col.label}
                  />
                ))}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-48 overflow-y-auto pr-1">
                {draftRefs.map((url, idx) => (
                  <div key={idx} className="flex items-center gap-1.5">
                    <span className="text-[11px] font-mono text-[#828794] w-5 text-right">{idx + 1}.</span>
                    <input
                      type="text"
                      value={url}
                      placeholder="@cuenta o URL de Reel"
                      onChange={(e) => {
                        const next = [...draftRefs];
                        next[idx] = e.target.value;
                        setDraftRefs(next);
                      }}
                      className="flex-1 bg-[#121316] border border-[#27272A] text-[#F4F4F5] rounded-md px-2.5 py-1.5 font-mono text-xs focus:outline-none focus:border-[#A1A1AA]"
                    />
                    {draftRefs.length > 1 && (
                      <button
                        type="button"
                        onClick={() => setDraftRefs(draftRefs.filter((_, i) => i !== idx))}
                        className="p-1.5 text-[#828794] hover:text-red-400 cursor-pointer"
                        aria-label="Quitar referencia"
                      >
                        <Trash2 size={13} />
                      </button>
                    )}
                  </div>
                ))}
              </div>
              <div className="flex items-center justify-between pt-2 border-t border-[#22242B]">
                {draftRefs.length < MAX_REFERENCES ? (
                  <button
                    type="button"
                    onClick={() => setDraftRefs([...draftRefs, ""])}
                    className="inline-flex items-center gap-1 text-xs font-mono text-[#9499A6] hover:text-[#E4E5E9] cursor-pointer"
                  >
                    <Plus size={13} aria-hidden="true" />
                    Agregar ({draftRefs.length}/{MAX_REFERENCES})
                  </button>
                ) : (
                  <span className="text-[11px] font-mono text-[#828794]">Máximo 10 referencias</span>
                )}
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="sm" icon={<X size={13} />} onClick={() => setEditingRefs(false)}>
                    Cancelar
                  </Button>
                  <Button variant="primary" size="sm" icon={<Save size={13} />} loading={savingRefs} onClick={handleSaveSettings}>
                    Guardar
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Progreso en ejecución */}
        {analyzing && (
          <div className="p-4 rounded-xl bg-[#0B0C0E] border border-[#2F323B] flex flex-col gap-3">
            <div className="flex items-center gap-2 text-xs font-medium text-[#E4E5E9]">
              <RefreshCw className="animate-spin text-[#9499A6]" size={14} aria-hidden="true" />
              <span>Generando guiones de 60–90 segundos...</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2 text-xs font-mono">
              {ANALYSIS_STEPS.map((step, idx) => (
                <div
                  key={idx}
                  className="px-3 py-2 rounded-lg bg-[#121316] border border-[#22242B] text-[#9499A6] flex items-center gap-2"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-[#828794]" aria-hidden="true" />
                  <span className="truncate">{step}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Resultados: 3 Propuestas + Escaleta y Guion Unificados por Sección */}
        {proposals.length > 0 ? (
          <div className="flex flex-col gap-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {proposals.map((prop, idx) => {
                const isSelected = selectedProposalIdx === idx;
                return (
                  <button
                    key={prop.id || idx}
                    onClick={() => setSelectedProposalIdx(idx)}
                    style={
                      isSelected
                        ? {
                            borderColor: color,
                            background: `linear-gradient(155deg, ${color}24 0%, #191B20 65%)`,
                          }
                        : undefined
                    }
                    className={`text-left p-4 rounded-xl border transition-colors duration-150 flex flex-col justify-between gap-2.5 cursor-pointer ${
                      isSelected
                        ? "bg-[#191B20]"
                        : "bg-[#0B0C0E] border-[#27272A] hover:border-[#3F3F46]"
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between gap-2 mb-1.5">
                        <span
                          className="text-[11px] font-mono font-medium"
                          style={{ color: isSelected ? color : "#9499A6" }}
                        >
                          Guion 0{idx + 1}
                        </span>
                        {prop.virality_badge && (
                          <span className="text-[10px] font-mono text-[#9499A6] bg-[#121316] border border-[#22242B] px-1.5 py-0.5 rounded">
                            {prop.virality_badge}
                          </span>
                        )}
                      </div>
                      <h4 className="text-sm font-semibold text-[#E4E5E9] tracking-tight line-clamp-2">
                        {prop.title}
                      </h4>
                    </div>

                    <div className="text-[11px] font-mono text-[#828794] flex items-center justify-between pt-2 border-t border-[#22242B]">
                      <span className="truncate">{prop.competitor_source_info}</span>
                      <ChevronRight size={13} style={{ color: isSelected ? color : "#828794" }} aria-hidden="true" />
                    </div>
                  </button>
                );
              })}
            </div>

            {selectedProposal && (
              <div className="flex flex-col gap-4 p-5 rounded-xl bg-[#0B0C0E] border border-[#22242B]">
                {/* Header del guion unificado + acciones de copiado */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-[#22242B]">
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2">
                      <FileText size={15} strokeWidth={1.5} style={{ color }} aria-hidden="true" />
                      <h5 className="text-sm font-semibold text-[#E4E5E9]">
                        Escaleta y Guion por Sección (60–90s)
                      </h5>
                    </div>
                    <p className="text-xs text-[#828794] font-mono">
                      {wordCount > 0 ? `${wordCount} palabras · ` : ""}
                      {selectedProposal.competitor_source_info}
                    </p>
                  </div>

                  <div className="flex flex-wrap items-center gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      icon={copiedMode === "spoken" ? <Check size={13} strokeWidth={2} /> : <Copy size={13} strokeWidth={1.5} />}
                      onClick={() => handleCopy(extractSpokenOnly(selectedProposal), "spoken")}
                    >
                      {copiedMode === "spoken" ? "Locución copiada" : "Copiar solo locución"}
                    </Button>

                    <Button
                      variant="primary"
                      size="sm"
                      icon={copiedMode === "unified" ? <Check size={13} strokeWidth={2} /> : <Copy size={13} strokeWidth={1.5} />}
                      onClick={() => handleCopy(buildUnifiedClipboardText(selectedProposal), "unified")}
                    >
                      {copiedMode === "unified" ? "Copiado" : "Copiar escaleta + guion"}
                    </Button>
                  </div>
                </div>

                {/* Análisis de la referencia original */}
                {(selectedProposal.original_transcript || selectedProposal.original_reel_url) && (
                  <div className="p-3.5 rounded-lg bg-[#121316] border border-[#22242B] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="text-xs text-[#9499A6] leading-relaxed max-w-[75ch]">
                      <span className="font-mono text-[11px] mr-2" style={{ color }}>Referencia:</span>
                      <span>{selectedProposal.original_transcript}</span>
                    </div>
                    {selectedProposal.original_reel_url && (
                      <a
                        href={selectedProposal.original_reel_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-[11px] font-mono text-[#9499A6] hover:text-[#E4E5E9] whitespace-nowrap flex-shrink-0"
                      >
                        <span>Ver Reel</span>
                        <ExternalLink size={11} aria-hidden="true" />
                      </a>
                    )}
                  </div>
                )}

                {/* Secciones unificadas: cada bloque muestra qué hacer + qué decir exactamente */}
                <div className="flex flex-col gap-3">
                  {unifiedSections.map((block, bIdx) => (
                    <div
                      key={bIdx}
                      className="p-4 rounded-lg bg-[#121316] border border-[#22242B] flex flex-col gap-3"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex items-center gap-2.5">
                          <span
                            style={{
                              backgroundColor: `${color}22`,
                              color,
                              borderColor: `${color}55`,
                            }}
                            className="text-xs font-mono font-medium border px-2 py-0.5 rounded"
                          >
                            {block.time_range}
                          </span>
                          <span className="text-xs font-semibold text-[#E4E5E9]">
                            {block.phase}
                          </span>
                        </div>

                        {block.on_screen_text && (
                          <span className="text-[11px] font-mono text-[#9499A6] bg-[#191B20] border border-[#22242B] px-2 py-0.5 rounded">
                            En pantalla: "{block.on_screen_text}"
                          </span>
                        )}
                      </div>

                      <p className="text-xs text-[#9499A6] leading-relaxed">
                        <span className="font-mono text-[#828794] mr-1.5">Escena:</span>
                        {block.description}
                      </p>

                      <div className="pt-2.5 border-t border-[#22242B] flex flex-col gap-1">
                        <span className="text-[11px] font-mono text-[#828794]">
                          Qué decir en esta sección:
                        </span>
                        <p className="text-sm text-[#E4E5E9] leading-relaxed whitespace-pre-wrap max-w-[70ch]">
                          {block.spoken_text}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="flex items-center justify-between text-[11px] font-mono text-[#828794] pt-1">
                  <span>{profile.client_name}</span>
                  <span>Gemini 3.0 Flash</span>
                </div>
              </div>
            )}
          </div>
        ) : (
          !analyzing && (
            <div className="p-10 text-center rounded-xl bg-[#0B0C0E] border border-dashed border-[#22242B] flex flex-col items-center justify-center">
              <div className="w-10 h-10 rounded-lg bg-[#191B20] border border-[#22242B] flex items-center justify-center text-[#9499A6] mb-3">
                <Sparkles size={18} strokeWidth={1.5} aria-hidden="true" />
              </div>
              <h4 className="text-sm font-semibold text-[#E4E5E9] mb-1">
                Sin análisis generado
              </h4>
              <p className="text-xs text-[#9499A6] max-w-md mb-5 leading-relaxed">
                Analiza las referencias para generar 3 guiones de 60 a 90 segundos con cada sección de escaleta unida a su locución.
              </p>
              <Button
                variant="primary"
                size="sm"
                icon={<Sparkles size={15} strokeWidth={1.5} />}
                onClick={() => onAnalyze(profile.id)}
              >
                Analizar y generar guiones
              </Button>
            </div>
          )
        )}
      </div>
    </Modal>
  );
};
