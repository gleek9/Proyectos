export interface TimelineBlock {
  time_range: string;
  phase: string;
  description: string;
}

export interface ScriptProposal {
  id: number;
  report_id: number;
  title: string;
  competitor_source_info?: string;
  virality_badge?: string;
  escalation_timeline: TimelineBlock[];
  full_script: string;
  original_reel_url?: string;
  original_transcript?: string;
  created_at: string;
}

export interface AnalysisReport {
  id: number;
  profile_id: number;
  summary?: string;
  created_at: string;
  proposals: ScriptProposal[];
}

export interface ProfileListItem {
  id: number;
  client_name: string;
  category: string;
  representative_color: string;
  client_instagram_url: string;
  competitor_count: number;
  created_at: string;
  last_analyzed_at?: string;
  time_elapsed_label: string;
}

export interface ProfileDetail {
  id: number;
  client_name: string;
  category: string;
  representative_color: string;
  client_instagram_url: string;
  competitor_urls: string[];
  brand_voice_summary?: string;
  created_at: string;
  last_analyzed_at?: string;
  time_elapsed_label: string;
  latest_report?: AnalysisReport;
  proposals: ScriptProposal[];
}

export interface ProfileCreateInput {
  client_name: string;
  category: string;
  representative_color: string;
  client_instagram_url: string;
  competitor_urls: string[];
}

export interface HealthStatus {
  status: string;
  apify_connected: boolean;
  gemini_connected: boolean;
  gemini_model: string;
  database_connected: boolean;
}

const API_BASE = ""; // Vite proxy redirige /api a http://localhost:8000

export const api = {
  // Autenticación
  async login(username: string, password: string):Promise<{ access_token: string; username: string }> {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Credenciales incorrectas");
    }
    return res.json();
  },

  // Estado del Motor
  async getHealth(): Promise<HealthStatus> {
    const res = await fetch(`${API_BASE}/api/health`);
    if (!res.ok) throw new Error("Fallo al consultar health check");
    return res.json();
  },

  // Perfiles
  async getProfiles(): Promise<ProfileListItem[]> {
    const res = await fetch(`${API_BASE}/api/profiles`);
    if (!res.ok) throw new Error("Error al obtener lista de perfiles");
    return res.json();
  },

  async getProfileDetail(id: number): Promise<ProfileDetail> {
    const res = await fetch(`${API_BASE}/api/profiles/${id}`);
    if (!res.ok) throw new Error("Error al obtener detalle de perfil");
    return res.json();
  },

  async createProfile(data: ProfileCreateInput): Promise<ProfileDetail> {
    const res = await fetch(`${API_BASE}/api/profiles`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Error al crear perfil");
    }
    return res.json();
  },

  async deleteProfile(id: number): Promise<void> {
    const res = await fetch(`${API_BASE}/api/profiles/${id}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error("Error al eliminar perfil");
  },

  async analyzeProfile(id: number): Promise<{ report: AnalysisReport }> {
    const res = await fetch(`${API_BASE}/api/profiles/${id}/analyze`, {
      method: "POST",
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Error al ejecutar análisis");
    }
    return res.json();
  },
};
