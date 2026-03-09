import { useEffect, useState } from "react";
import axios from "axios";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Lock, ArrowLeft, Mail, KeyRound } from "lucide-react";
import { setAdminToken, clearAdminToken, getAdminToken } from "@/lib/adminAuth";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AdminLogin() {
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [resetStep, setResetStep] = useState(1); // 1: Request OTP, 2: Enter OTP & new password
  const [otp, setOtp] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [otpSending, setOtpSending] = useState(false);
  const [resetting, setResetting] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // If already logged in, redirect to dashboard instead of clearing token
    const token = getAdminToken();
    if (token) {
      navigate("/admin/dashboard");
    }
  }, [navigate]);

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!password) {
      toast.error("Please enter password");
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/admin/login`, { password });
      const token = response?.data?.token;
      const expiresAt = response?.data?.expires_at;
      if (!token) {
        throw new Error("Login response missing token");
      }

      setAdminToken(token, expiresAt);
      toast.success("Login successful");
      // Small delay to ensure token is persisted before navigation
      await new Promise(resolve => setTimeout(resolve, 100));
      navigate("/admin/dashboard");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Invalid password");
    } finally {
      setLoading(false);
    }
  };

  const handleRequestOTP = async () => {
    setOtpSending(true);
    try {
      const response = await axios.post(`${API}/admin/request-otp?purpose=password_reset`);
      toast.success(response.data.message);
      setResetStep(2);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to send OTP");
    } finally {
      setOtpSending(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    if (!otp || !newPassword) {
      toast.error("Please enter OTP and new password");
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error("Passwords don't match");
      return;
    }
    if (newPassword.length < 8) {
      toast.error("Password must be at least 8 characters");
      return;
    }

    setResetting(true);
    try {
      await axios.post(`${API}/admin/forgot-password`, {
        otp,
        new_password: newPassword
      });
      toast.success("Password reset successfully!");
      // Reset form and go back to login
      setShowForgotPassword(false);
      setResetStep(1);
      setOtp("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to reset password");
    } finally {
      setResetting(false);
    }
  };

  const resetForgotPassword = () => {
    setShowForgotPassword(false);
    setResetStep(1);
    setOtp("");
    setNewPassword("");
    setConfirmPassword("");
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
              onClick={showForgotPassword ? resetForgotPassword : () => navigate("/")} 
              className="text-vault-text-secondary hover:text-vault-gold transition-colors mb-4 flex items-center gap-2"
              data-testid="back-btn"
            >
              <ArrowLeft className="w-4 h-4" />
              {showForgotPassword ? "Back to Login" : "Back to Guest Portal"}
            </button>
            <CardTitle className="font-outfit text-2xl font-bold text-vault-text tracking-tight flex items-center gap-3">
              {showForgotPassword ? (
                <>
                  <KeyRound className="w-6 h-6 text-vault-gold" />
                  Reset Password
                </>
              ) : (
                <>
                  <Lock className="w-6 h-6 text-vault-gold" />
                  Admin Login
                </>
              )}
            </CardTitle>
            <p className="text-vault-text-secondary font-manrope mt-2 text-sm">
              {showForgotPassword 
                ? (resetStep === 1 ? "We'll send a verification code to your email" : "Enter the code and your new password")
                : "Enter your password to access the dashboard"
              }
            </p>
          </CardHeader>
          <CardContent>
            {!showForgotPassword ? (
              // Login Form
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
                <button
                  type="button"
                  onClick={() => setShowForgotPassword(true)}
                  className="w-full text-center text-sm text-vault-text-secondary hover:text-vault-gold transition-colors"
                  data-testid="forgot-password-link"
                >
                  Forgot Password?
                </button>
              </form>
            ) : resetStep === 1 ? (
              // Step 1: Request OTP
              <div className="space-y-6">
                <div className="bg-vault-dark/50 rounded-lg p-4 border border-vault-gold/20">
                  <div className="flex items-center gap-3 text-vault-text">
                    <Mail className="w-5 h-5 text-vault-gold" />
                    <span className="text-sm">OTP will be sent to your registered email</span>
                  </div>
                </div>
                <Button
                  onClick={handleRequestOTP}
                  disabled={otpSending}
                  className="w-full vault-btn-primary h-12"
                  data-testid="request-otp-btn"
                >
                  {otpSending ? "Sending OTP..." : "Send Verification Code"}
                </Button>
              </div>
            ) : (
              // Step 2: Enter OTP and new password
              <form onSubmit={handleResetPassword} className="space-y-4">
                <div>
                  <label className="vault-label">Verification Code (OTP)</label>
                  <Input
                    type="text"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    placeholder="Enter 6-digit code"
                    className="vault-input text-center text-2xl tracking-[0.5em] font-mono"
                    maxLength={6}
                    data-testid="otp-input"
                  />
                </div>
                <div>
                  <label className="vault-label">New Password</label>
                  <Input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Enter new password (min 8 chars)"
                    className="vault-input"
                    data-testid="new-password-input"
                  />
                </div>
                <div>
                  <label className="vault-label">Confirm Password</label>
                  <Input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Confirm new password"
                    className="vault-input"
                    data-testid="confirm-password-input"
                  />
                </div>
                <Button
                  type="submit"
                  disabled={resetting}
                  className="w-full vault-btn-primary h-12"
                  data-testid="reset-password-btn"
                >
                  {resetting ? "Resetting..." : "Reset Password"}
                </Button>
                <button
                  type="button"
                  onClick={handleRequestOTP}
                  disabled={otpSending}
                  className="w-full text-center text-sm text-vault-text-secondary hover:text-vault-gold transition-colors"
                  data-testid="resend-otp-btn"
                >
                  {otpSending ? "Sending..." : "Resend OTP"}
                </button>
              </form>
            )}
          </CardContent>
        </Card>
      </motion.div>
      <div className="noise-overlay" />
    </div>
  );
}
