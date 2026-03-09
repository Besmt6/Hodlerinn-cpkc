import { Navigate, useLocation } from "react-router-dom";
import { useState, useEffect } from "react";
import { getAdminToken } from "@/lib/adminAuth";

export default function ProtectedRoute({ children }) {
  const location = useLocation();
  const [isChecking, setIsChecking] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    // Check token on mount and give localStorage time to be read
    const checkAuth = () => {
      const token = getAdminToken();
      setIsAuthenticated(!!token);
      setIsChecking(false);
    };
    
    // Small delay to ensure localStorage is fully available after page load
    const timer = setTimeout(checkAuth, 50);
    return () => clearTimeout(timer);
  }, []);

  // Show nothing while checking to prevent flash
  if (isChecking) {
    return (
      <div className="min-h-screen bg-vault-dark flex items-center justify-center">
        <div className="text-vault-gold">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/admin" replace state={{ from: location }} />;
  }

  return children;
}
