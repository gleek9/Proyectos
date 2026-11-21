export interface ClientColorOption {
  hex: string;
  label: string;
}

export const DEFAULT_CLIENT_COLOR = "#38BDF8";

export const CLIENT_COLOR_PALETTE: ClientColorOption[] = [
  { hex: "#38BDF8", label: "Azul Cielo" },
  { hex: "#34D399", label: "Esmeralda" },
  { hex: "#F59E0B", label: "Ámbar" },
  { hex: "#A78BFA", label: "Violeta" },
  { hex: "#F472B6", label: "Rosa Coral" },
  { hex: "#FB7185", label: "Carmesí" },
  { hex: "#94A3B8", label: "Pizarra" },
];

const LEGACY_NEON_SET = new Set(["#58FF9C", "#42E686", "#00FF00", "#39FF14"]);

/**
 * Remapea únicamente colores verde neón heredados; conserva colores reales de cada cliente.
 */
export function resolveClientColor(hex?: string | null): string {
  if (!hex) return DEFAULT_CLIENT_COLOR;
  const upper = hex.trim().toUpperCase();
  if (LEGACY_NEON_SET.has(upper)) {
    return DEFAULT_CLIENT_COLOR;
  }
  return hex;
}
