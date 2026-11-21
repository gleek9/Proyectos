import React, { useState, useEffect, useMemo } from "react";
import { Search, Filter, RefreshCw } from "lucide-react";
import { Navbar } from "../layout/Navbar";
import { ProfileCard } from "../kanban/ProfileCard";
import { EmptyState } from "../kanban/EmptyState";
import { CreateProfileModal } from "../modals/CreateProfileModal";
import { ProfileDetailModal } from "../modals/ProfileDetailModal";
import {
  api,
  ProfileListItem,
  ProfileDetail,
  ProfileCreateInput,
  HealthStatus,
} from "../../api";

interface DashboardViewProps {
  user: string;
  onLogout: () => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ user, onLogout }) => {
  const [profiles, setProfiles] = useState<ProfileListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [health, setHealth] = useState<HealthStatus | null>(null);

  // Filtros
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");

  // Modales
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedProfileId, setSelectedProfileId] = useState<number | null>(null);
  const [selectedProfileDetail, setSelectedProfileDetail] = useState<ProfileDetail | null>(null);
  const [analyzing, setAnalyzing] = useState(false);

  // Carga inicial
  const loadData = async () => {
    try {
      const [profilesData, healthData] = await Promise.all([
        api.getProfiles(),
        api.getHealth().catch(() => null),
      ]);
      setProfiles(profilesData);
      setHealth(healthData);
    } catch (err) {
      console.error("Error cargando perfiles:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // Polling cada 30 segundos
    return () => clearInterval(interval);
  }, []);

  // Extraer categorías únicas para filtro
  const categories = useMemo(() => {
    const set = new Set<string>();
    profiles.forEach((p) => {
      if (p.category) set.add(p.category);
    });
    return Array.from(set);
  }, [profiles]);

  // Perfiles filtrados
  const filteredProfiles = useMemo(() => {
    return profiles.filter((p) => {
      const matchesSearch =
        p.client_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.client_instagram_url.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesCategory =
        selectedCategory === "all" || p.category === selectedCategory;
      return matchesSearch && matchesCategory;
    });
  }, [profiles, searchQuery, selectedCategory]);

  // Abrir detalle de perfil
  const handleOpenDetail = async (id: number) => {
    setSelectedProfileId(id);
    try {
      const detail = await api.getProfileDetail(id);
      setSelectedProfileDetail(detail);
    } catch (err) {
      console.error("Error abriendo detalle:", err);
    }
  };

  // Crear perfil
  const handleCreateProfile = async (data: ProfileCreateInput) => {
    await api.createProfile(data);
    await loadData();
  };

  // Disparar análisis
  const handleAnalyze = async (id: number) => {
    setAnalyzing(true);
    try {
      await api.analyzeProfile(id);
      // Recargar detalle y lista
      const updatedDetail = await api.getProfileDetail(id);
      setSelectedProfileDetail(updatedDetail);
      await loadData();
    } catch (err: any) {
      alert(`Error en el análisis: ${err.message}`);
    } finally {
      setAnalyzing(false);
    }
  };

  // Actualizar referencias y color del perfil
  const handleUpdateProfile = async (id: number, references: string[], color: string) => {
    const updated = await api.updateProfile(id, {
      competitor_urls: references,
      representative_color: color,
    });
    setSelectedProfileDetail(updated);
    await loadData();
  };

  // Eliminar perfil
  const handleDeleteProfile = async (id: number) => {
    await api.deleteProfile(id);
    setSelectedProfileDetail(null);
    setSelectedProfileId(null);
    await loadData();
  };

  return (
    <div className="min-h-screen bg-[#0B0C0E] text-[#E4E5E9] flex flex-col">
      {/* Topbar */}
      <Navbar
        health={health}
        onNewProfile={() => setIsCreateOpen(true)}
        onLogout={onLogout}
        user={user}
      />

      {/* Contenido Principal */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-6">
        {/* Barra de Filtros y Búsqueda */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 pb-4 border-b border-[#22242B]">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-semibold tracking-tight text-[#E4E5E9]">
              Clientes
            </h2>
            <span className="text-[11px] font-mono bg-[#121316] border border-[#22242B] text-[#9499A6] px-2 py-0.5 rounded-md">
              {profiles.length}
            </span>
          </div>

          <div className="flex items-center gap-2.5 flex-wrap">
            <div className="relative flex-1 sm:w-64">
              <Search
                size={14}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-[#646975]"
              />
              <input
                type="text"
                placeholder="Buscar cliente..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-[#121316] border border-[#27272A] text-xs text-[#F4F4F5] rounded-lg pl-8 pr-3 py-2 placeholder:text-[#71717A] focus:outline-none focus:border-[#A1A1AA]"
              />
            </div>

            {categories.length > 0 && (
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="bg-[#121316] border border-[#27272A] text-xs text-[#A1A1AA] rounded-lg px-3 py-2 focus:outline-none focus:border-[#A1A1AA] font-mono cursor-pointer"
              >
                <option value="all">Todas las categorías</option>
                {categories.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            )}

            <button
              onClick={loadData}
              className="p-2 text-[#646975] hover:text-[#E4E5E9] rounded-lg hover:bg-[#191B20] border border-[#22242B] transition-colors cursor-pointer"
              title="Actualizar datos"
              aria-label="Actualizar datos"
            >
              <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            </button>
          </div>
        </div>

        {/* Grid Modular Kanban de Perfiles */}
        {loading ? (
          <div className="flex items-center justify-center py-20 text-[#646975] font-mono text-sm">
            <RefreshCw className="animate-spin mr-2" size={16} />
            Cargando tablero...
          </div>
        ) : profiles.length === 0 ? (
          <EmptyState onNewProfile={() => setIsCreateOpen(true)} />
        ) : filteredProfiles.length === 0 ? (
          <div className="py-16 text-center text-[#9499A6] font-mono text-sm border border-[#22242A] rounded-xl bg-[#121316]/50">
            No se encontraron clientes que coincidan con la búsqueda.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
            {filteredProfiles.map((p) => (
              <ProfileCard
                key={p.id}
                profile={p}
                onClick={() => handleOpenDetail(p.id)}
              />
            ))}
          </div>
        )}
      </main>

      {/* Modal de Creación de Perfil */}
      <CreateProfileModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onSubmit={handleCreateProfile}
      />

      {/* Mini-Ventana Modal de Detalle y Guiones */}
      <ProfileDetailModal
        isOpen={Boolean(selectedProfileDetail)}
        onClose={() => {
          setSelectedProfileDetail(null);
          setSelectedProfileId(null);
        }}
        profile={selectedProfileDetail}
        onAnalyze={handleAnalyze}
        onUpdateProfile={handleUpdateProfile}
        onDelete={handleDeleteProfile}
        analyzing={analyzing}
      />
    </div>
  );
};
