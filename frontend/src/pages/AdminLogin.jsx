import { useState } from "react";
import axios from "axios";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Lock, ArrowLeft } from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AdminLogin() {
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!password) {
      toast.error("Please enter password");
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/admin/login`, { password });
      // Store JWT token
      const token = response.data.token;
      sessionStorage.setItem("adminAuth", "true");
      sessionStorage.setItem("adminToken", token);
      toast.success("Login successful");
      navigate("/admin/dashboard");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Invalid password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="kiosk-container grid-bg min-h-screen relative">
      {/* Logo Header */}
      <div className="absolute top-6 left-6 flex items-center gap-3">
        <img 
          src="https://customer-assets.emergentagent.com/job_guest-hotel-mgmt/artifacts/56yphta2_17721406444867042425090808501904.jpg" 
          alt="Hodler Inn Logo" 
          className="w-12 h-12 rounded-lg object-cover"
        />
        <div>
          <h1 className="font-outfit font-bold text-vault-text text-xl tracking-tight">HODLER INN</h1>
          <p className="font-mono text-[10px] text-vault-gold uppercase tracking-widest">Admin Portal</p>
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
        className="w-full max-w-md"
      >
        <Card className="glass-card p-8" data-testid="admin-login-card">
          <CardHeader className="pb-6">
            <button 
              onClick={() => navigate("/")} 
              className="text-vault-text-secondary hover:text-vault-gold transition-colors mb-4 flex items-center gap-2"
              data-testid="back-to-guest-btn"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Guest Portal
            </button>
            <CardTitle className="font-outfit text-2xl font-bold text-vault-text tracking-tight flex items-center gap-3">
              <Lock className="w-6 h-6 text-vault-gold" />
              Admin Login
            </CardTitle>
            <p className="text-vault-text-secondary font-manrope mt-2 text-sm">
              Enter your password to access the dashboard
            </p>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-6">
              <div>
                <label className="vault-label">Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-vault-text-secondary" />
                  <Input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter admin password"
                    className="vault-input pl-10"
                    data-testid="admin-password-input"
                  />
                </div>
              </div>
              <Button
                type="submit"
                disabled={loading}
                className="w-full vault-btn-primary h-12"
                data-testid="admin-login-btn"
              >
                {loading ? "Authenticating..." : "Access Dashboard"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </motion.div>
      <div className="noise-overlay" />
    </div>
  );
}
