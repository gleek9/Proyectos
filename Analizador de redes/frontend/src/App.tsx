import React, { useState, useEffect } from "react";
import { LoginView } from "./components/views/LoginView";
import { DashboardView } from "./components/views/DashboardView";

export const App: React.FC = () => {
  const [user, setUser] = useState<string | null>(null);
  const [checkingAuth, setCheckingAuth] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("citi_auth_token");
    const storedUser = localStorage.getItem("citi_auth_user");
    if (token && storedUser) {
      setUser(storedUser);
    }
    setCheckingAuth(false);
  }, []);

  const handleLoginSuccess = (username: string) => {
    setUser(username);
  };

  const handleLogout = () => {
    localStorage.removeItem("citi_auth_token");
    localStorage.removeItem("citi_auth_user");
    setUser(null);
  };

  if (checkingAuth) {
    return (
      <div className="min-h-screen bg-[#090A0D] flex items-center justify-center font-mono text-xs text-[#64748B]">
        Iniciando Citi Analyzer...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#090A0D] font-sans">
      {!user ? (
        <LoginView onSuccess={handleLoginSuccess} />
      ) : (
        <DashboardView user={user} onLogout={handleLogout} />
      )}
    </div>
  );
};

export default App;
