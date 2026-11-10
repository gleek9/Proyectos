import React, { useState } from "react";
import {
  ExternalLink,
  Sparkles,
  Copy,
  Check,
  Trash2,
  TrendingUp,
  Clock,
  Layers,
  FileText,
  Video,
  ChevronRight,
  RefreshCw,
} from "lucide-react";
import { Modal } from "../ui/Modal";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";
import { ProfileDetail, ScriptProposal } from "../../api";

interface ProfileDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  profile: ProfileDetail | null;
  onAnalyze: (id: number) => Promise<void>;
  onDelete: (id: number) => Promise<void>;
  analyzing: boolean;
}

const ANALYSIS_STEPS = [
  "1. Radiografía de la voz del cliente",
  "2. Caza de virales de competidores vía Apify",
  "3. Extracción de audio y transcripción multimodal",
  "4. Adaptación de 3 guiones con Gemini 3.0",
];

export const ProfileDetailModal: React.FC<ProfileDetailModalProps> = ({
  isOpen,
  onClose,
  profile,
  onAnalyze,
  onDelete,
  analyzing,
}) => {
  const [selectedProposalIdx, setSelectedProposalIdx] = useState(0);
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const [deleting, setDeleting] = useState(false);

  if (!profile) return null;

  const color = profile.representative_color || "#58FF9C";
  const proposals = profile.proposals || [];
  const selectedProposal: ScriptProposal | undefined = proposals[selectedProposalIdx];

  const handleCopyScript = (scriptText: string, id: number) => {
    navigator.clipboard.writeText(scriptText);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2500);
  };

  const handleDelete = async () => {
    if (confirm(`¿Estás seguro de que deseas eliminar el perfil de "${profile.client_name}"?`)) {
      setDeleting(true);
      try {
        await onDelete(profile.id);
        onClose();
      } finally {
        setDeleting(false);
      }
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      maxWidth="6xl"
      title={
        <div className="flex flex-wrap items-center gap-2.5">
          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
          <span className="text-xl font-bold text-[#F8FAFC] tracking-tight">
            {profile.client_name}
          </span>
          <Badge variant="custom" colorHex={color}>
            {profile.category}
          </Badge>
        </div>
      }
      subtitle={
        <div className="flex flex-wrap items-center gap-3 text-xs text-[#94A3B8] font-mono mt-1">
          <a
            href={profile.client_instagram_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 hover:text-[#58FF9C] transition-colors"
          >
            <span>Instagram Cliente</span>
            <ExternalLink size={12} strokeWidth={1.5} />
          </a>
          <span>•</span>
          <span>{profile.competitor_urls.length} competidores vinculados</span>
          <span>•</span>
          <span className="text-[#64748B]">{profile.time_elapsed_label}</span>
        </div>
      }
    >
      <div className="flex flex-col gap-6">
        {/* Cabecera Técnica: Competidores y Botón de Acción Principal */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-xl bg-[#111318] border border-[#1E222B]">
          {/* Etiquetas de Competidores */}
          <div className="flex flex-col gap-1.5">
            <span className="text-[11px] font-mono uppercase tracking-wider text-[#64748B]">
              Competidores directos rastreados:
            </span>
            <div className="flex flex-wrap items-center gap-2">
              {profile.competitor_urls.map((u, i) => {
                const handle = u.replace(/https?:\/\/(www\.)?instagram\.com\//, "@").replace(/\/$/, "");
                return (
                  <a
                    key={i}
                    href={u}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-[#171A21] border border-[#1E222B] text-xs font-mono text-[#94A3B8] hover:text-[#F8FAFC] hover:border-[#58FF9C]/40 transition-colors"
                  >
                    <span>{handle}</span>
                    <ExternalLink size={11} strokeWidth={1.5} />
                  </a>
                );
              })}
            </div>
          </div>

          {/* Botón Primario de Análisis y Borrado */}
          <div className="flex items-center gap-2.5 flex-shrink-0">
            <Button
              variant="primary"
              size="md"
              icon={analyzing ? <RefreshCw className="animate-spin" size={16} /> : <Sparkles size={16} strokeWidth={2} />}
              onClick={() => onAnalyze(profile.id)}
              loading={analyzing}
            >
              {proposals.length > 0 ? "Actualizar Análisis" : "Analizar Competencia y Generar Guiones"}
            </Button>

            <button
              onClick={handleDelete}
              disabled={deleting || analyzing}
              className="p-2 text-[#64748B] hover:text-red-400 rounded-lg hover:bg-[#171A21] border border-transparent hover:border-red-500/20 transition-all"
              title="Eliminar perfil"
            >
              <Trash2 size={16} strokeWidth={1.5} />
            </button>
          </div>
        </div>

        {/* Stepper de Progreso cuando el análisis está en ejecución */}
        {analyzing && (
          <div className="p-5 rounded-xl bg-[#111318] border border-[#58FF9C]/30 flex flex-col gap-3 shadow-[0_0_20px_rgba(88,255,156,0.1)]">
            <div className="flex items-center gap-2 text-sm font-semibold text-[#58FF9C]">
              <RefreshCw className="animate-spin text-[#58FF9C]" size={16} />
              <span>Ejecutando Inteligencia de Guiones Virales...</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2 text-xs font-mono">
              {ANALYSIS_STEPS.map((step, idx) => (
                <div
                  key={idx}
                  className="px-3 py-2 rounded bg-[#171A21] border border-[#1E222B] text-[#94A3B8] flex items-center gap-2"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-[#58FF9C] animate-pulse" />
                  <span className="truncate">{step}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Área de Resultados: Los 3 Recuadros de Oportunidades Virales */}
        {proposals.length > 0 ? (
          <div className="flex flex-col gap-4">
            {/* Selector de Pestañas / Tarjetas para las 3 Propuestas */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {proposals.map((prop, idx) => {
                const isSelected = selectedProposalIdx === idx;
                return (
                  <button
                    key={prop.id || idx}
                    onClick={() => setSelectedProposalIdx(idx)}
                    className={`text-left p-4 rounded-xl border transition-all duration-150 flex flex-col justify-between gap-3 ${
                      isSelected
                        ? "bg-[#171A21] border-[#58FF9C] shadow-[0_0_16px_rgba(88,255,156,0.15)] ring-1 ring-[#58FF9C]"
                        : "bg-[#111318] border-[#1E222B] hover:border-[#1E222B] hover:bg-[#14171E] opacity-75 hover:opacity-100"
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[11px] font-mono text-[#58FF9C] uppercase tracking-wider font-semibold">
                          Oportunidad 0{idx + 1}
                        </span>
                        {prop.virality_badge && (
                          <span className="text-[10px] font-mono bg-[#090A0D] text-[#94A3B8] border border-[#1E222B] px-1.5 py-0.5 rounded">
                            {prop.virality_badge}
                          </span>
                        )}
                      </div>
                      <h4 className="text-sm font-bold text-[#F8FAFC] tracking-tight line-clamp-2">
                        {prop.title}
                      </h4>
                    </div>

                    <div className="text-[11px] font-mono text-[#64748B] flex items-center justify-between pt-2 border-t border-[#1E222B]/60">
                      <span className="truncate">{prop.competitor_source_info}</span>
                      <ChevronRight size={14} className={isSelected ? "text-[#58FF9C]" : "text-[#64748B]"} />
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Panel de Detalle de la Propuesta Seleccionada (Escaleta y Guion) */}
            {selectedProposal && (
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 mt-2">
                {/* Columna Izquierda: Escaleta Técnica (40% de ancho) */}
                <div className="lg:col-span-5 flex flex-col gap-3 p-5 rounded-xl bg-[#111318] border border-[#1E222B]">
                  <div className="flex items-center gap-2 pb-3 border-b border-[#1E222B]">
                    <Layers size={16} strokeWidth={1.5} className="text-[#58FF9C]" />
                    <h5 className="text-xs font-mono font-bold uppercase tracking-wider text-[#F8FAFC]">
                      Escaleta Estructurada por Bloques
                    </h5>
                  </div>

                  <div className="flex flex-col gap-3">
                    {selectedProposal.escalation_timeline.map((block, bIdx) => (
                      <div
                        key={bIdx}
                        className="p-3.5 rounded-lg bg-[#171A21] border border-[#1E222B] flex flex-col gap-1.5"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-mono font-semibold text-[#58FF9C] bg-[#58FF9C]/10 border border-[#58FF9C]/20 px-2 py-0.5 rounded">
                            {block.time_range}
                          </span>
                          <span className="text-[11px] font-mono text-[#94A3B8] uppercase">
                            {block.phase}
                          </span>
                        </div>
                        <p className="text-xs text-[#F8FAFC] leading-relaxed pt-1">
                          {block.description}
                        </p>
                      </div>
                    ))}
                  </div>

                  {/* Contexto del Reel original si está disponible */}
                  {selectedProposal.original_transcript && (
                    <div className="mt-2 pt-3 border-t border-[#1E222B] text-xs text-[#64748B]">
                      <span className="font-mono text-[10px] uppercase text-[#94A3B8] block mb-1">
                        Inspiración de la competencia:
                      </span>
                      <p className="italic line-clamp-3">
                        "{selectedProposal.original_transcript}"
                      </p>
                    </div>
                  )}
                </div>

                {/* Columna Derecha: Guion Completo Adaptado (60% de ancho) */}
                <div className="lg:col-span-7 flex flex-col gap-3 p-5 rounded-xl bg-[#111318] border border-[#1E222B]">
                  <div className="flex items-center justify-between pb-3 border-b border-[#1E222B]">
                    <div className="flex items-center gap-2">
                      <FileText size={16} strokeWidth={1.5} className="text-[#58FF9C]" />
                      <h5 className="text-xs font-mono font-bold uppercase tracking-wider text-[#F8FAFC]">
                        Guion Completo Adaptado (Listo para Grabar)
                      </h5>
                    </div>

                    {/* Botón de Copiar Guion con Feedback Interactivo */}
                    <Button
                      variant={copiedId === selectedProposal.id ? "primary" : "secondary"}
                      size="sm"
                      icon={
                        copiedId === selectedProposal.id ? (
                          <Check size={14} strokeWidth={2.5} />
                        ) : (
                          <Copy size={14} strokeWidth={1.5} />
                        )
                      }
                      onClick={() => handleCopyScript(selectedProposal.full_script, selectedProposal.id)}
                    >
                      {copiedId === selectedProposal.id ? "¡Guion Copiado!" : "Copiar Guion"}
                    </Button>
                  </div>

                  {/* Texto literal del guion */}
                  <div className="p-4 rounded-lg bg-[#090A0D] border border-[#1E222B] max-h-[380px] overflow-y-auto">
                    <pre className="text-sm text-[#F8FAFC] leading-relaxed font-sans whitespace-pre-wrap font-normal selection:bg-[#58FF9C]/30">
                      {selectedProposal.full_script}
                    </pre>
                  </div>

                  <div className="flex items-center justify-between text-[11px] font-mono text-[#64748B] pt-1">
                    <span>Voz adaptada: {profile.client_name}</span>
                    <span>Modelo: Gemini 3.0 Flash</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        ) : (
          /* Estado sin análisis previo */
          !analyzing && (
            <div className="p-10 text-center rounded-xl bg-[#111318] border border-[#1E222B] flex flex-col items-center justify-center">
              <div className="w-12 h-12 rounded-xl bg-[#171A21] border border-[#1E222B] flex items-center justify-center text-[#58FF9C] mb-3">
                <Sparkles size={22} strokeWidth={1.5} />
              </div>
              <h4 className="text-base font-bold text-[#F8FAFC] mb-1">
                Aún no has generado guiones para este cliente
              </h4>
              <p className="text-xs text-[#94A3B8] max-w-md mb-5 leading-relaxed">
                Presiona el botón para que Apify y Gemini 3.0 extraigan los mejores Reels de sus competidores y redacten 3 propuestas de alto impacto adaptadas a su voz.
              </p>
              <Button
                variant="primary"
                icon={<Sparkles size={16} strokeWidth={2} />}
                onClick={() => onAnalyze(profile.id)}
              >
                Analizar Competencia y Generar Guiones
              </Button>
            </div>
          )
        )}
      </div>
    </Modal>
  );
};
