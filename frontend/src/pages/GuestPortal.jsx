import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import SignatureCanvas from "react-signature-canvas";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { 
  UserPlus, 
  LogIn, 
  LogOut, 
  ArrowLeft, 
  Eraser, 
  CalendarIcon,
  Clock,
  DoorOpen,
  User,
  Hash,
  Settings,
  ClipboardList,
  Maximize,
  Minimize,
  HelpCircle
} from "lucide-react";
import { format } from "date-fns";
import { cn } from "@/lib/utils";
import { useNavigate } from "react-router-dom";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const pageVariants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 }
};

export default function GuestPortal() {
  const [view, setView] = useState("menu"); // menu, register, checkin, checkout, signin
  const [isFullscreen, setIsFullscreen] = useState(false);
  const navigate = useNavigate();

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().then(() => {
        setIsFullscreen(true);
      }).catch((err) => {
        console.log("Fullscreen error:", err);
      });
    } else {
      document.exitFullscreen().then(() => {
        setIsFullscreen(false);
      });
    }
  };

  // Listen for fullscreen changes (e.g., user presses Escape)
  React.useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

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
          <p className="font-mono text-[10px] text-vault-gold uppercase tracking-widest">Be Responsible to Be Free</p>
        </div>
      </div>

      {/* Top Right Buttons */}
      <div className="absolute top-6 right-6 flex items-center gap-2">
        {/* Fullscreen/Kiosk Mode Button */}
        <button 
          onClick={toggleFullscreen}
          className="flex items-center gap-2 text-vault-text-secondary hover:text-vault-gold transition-colors bg-vault-surface/50 px-3 py-2 rounded-lg border border-vault-border"
          data-testid="fullscreen-btn"
          title={isFullscreen ? "Exit Kiosk Mode" : "Enter Kiosk Mode"}
        >
          {isFullscreen ? <Minimize className="w-4 h-4" /> : <Maximize className="w-4 h-4" />}
          <span className="text-sm font-mono hidden sm:inline">{isFullscreen ? "Exit Kiosk" : "Kiosk Mode"}</span>
        </button>
        
        {/* Admin Link */}
        <button 
          onClick={() => navigate("/admin")}
          className="flex items-center gap-2 text-vault-text-secondary hover:text-vault-gold transition-colors bg-vault-surface/50 px-3 py-2 rounded-lg border border-vault-border"
          data-testid="admin-link"
        >
          <Settings className="w-4 h-4" />
          <span className="text-sm font-mono hidden sm:inline">Admin</span>
        </button>
      </div>

      <AnimatePresence mode="wait">
        {view === "menu" && (
          <MainMenu key="menu" setView={setView} />
        )}
        {view === "register" && (
          <RegisterForm key="register" setView={setView} />
        )}
        {view === "checkin" && (
          <CheckInForm key="checkin" setView={setView} />
        )}
        {view === "checkout" && (
          <CheckOutForm key="checkout" setView={setView} />
        )}
        {view === "signin" && (
          <SignInSheetView key="signin" setView={setView} />
        )}
      </AnimatePresence>
    </div>
  );
}

function MainMenu({ setView }) {
  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
      className="w-full max-w-md"
    >
      <Card className="glass-card p-8" data-testid="main-menu-card">
        <CardHeader className="text-center pb-8">
          <CardTitle className="font-outfit text-3xl font-bold text-vault-text tracking-tight">
            Welcome to Hodler Inn
          </CardTitle>
          <p className="text-vault-text-secondary font-manrope mt-2">
            Select an option below to continue
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="bg-vault-surface-highlight/50 border border-vault-border rounded-lg p-3 mb-2">
            <p className="text-vault-text-secondary text-sm text-center">
              <span className="text-vault-gold font-medium">Note:</span> Register only if this is your <span className="text-vault-gold">first time</span>. 
              Already registered? Go directly to <span className="text-vault-gold">Check In</span>.
            </p>
          </div>
          <Button
            onClick={() => setView("register")}
            className="w-full h-14 text-lg flex items-center justify-center gap-3 bg-amber-500 hover:bg-amber-600 text-black font-bold uppercase tracking-wide"
            data-testid="register-btn"
          >
            <UserPlus className="w-5 h-5" />
            Register (First Time Only)
          </Button>
          <Button
            onClick={() => setView("checkin")}
            className="w-full h-14 text-lg flex items-center justify-center gap-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold uppercase tracking-wide"
            data-testid="checkin-btn"
          >
            <LogIn className="w-5 h-5" />
            Check In
          </Button>
          <Button
            onClick={() => setView("checkout")}
            className="w-full h-14 text-lg flex items-center justify-center gap-3 bg-red-600 hover:bg-red-700 text-white font-bold uppercase tracking-wide"
            data-testid="checkout-btn"
          >
            <LogOut className="w-5 h-5" />
            Check Out
          </Button>
          <div className="pt-4 border-t border-vault-border">
            <Button
              onClick={() => setView("signin")}
              className="w-full vault-btn-secondary h-12 flex items-center justify-center gap-3"
              data-testid="signin-sheet-btn"
            >
              <ClipboardList className="w-5 h-5" />
              View Sign-In Sheet
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function RegisterForm({ setView }) {
  const [employeeNumber, setEmployeeNumber] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);

  const handleRegister = async () => {
    if (!employeeNumber || !name) {
      toast.error("Please fill in all fields");
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${API}/guests/register`, {
        employee_number: employeeNumber,
        name
      });
      toast.success("Registration successful! You can now check in.");
      setView("menu");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
      className="w-full max-w-md"
    >
      <Card className="glass-card p-8" data-testid="register-form-card">
        <CardHeader className="pb-6">
          <button 
            onClick={() => setView("menu")} 
            className="text-vault-text-secondary hover:text-vault-gold transition-colors mb-4 flex items-center gap-2"
            data-testid="back-btn"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
          <CardTitle className="font-outfit text-2xl font-bold text-vault-text tracking-tight flex items-center gap-3">
            <UserPlus className="w-6 h-6 text-vault-gold" />
            Guest Registration
          </CardTitle>
          <p className="text-vault-text-secondary text-sm mt-2">
            Register with your employee details. Signature will be captured at check-in.
          </p>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <label className="vault-label">Employee Number</label>
            <div className="relative">
              <Hash className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-vault-text-secondary" />
              <Input
                value={employeeNumber}
                onChange={(e) => setEmployeeNumber(e.target.value)}
                placeholder="Enter employee number"
                className="vault-input pl-10"
                data-testid="employee-number-input"
              />
            </div>
          </div>
          <div>
            <label className="vault-label">Full Name</label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-vault-text-secondary" />
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Enter your full name"
                className="vault-input pl-10"
                data-testid="name-input"
              />
            </div>
          </div>
          <Button
            onClick={handleRegister}
            disabled={loading}
            className="w-full vault-btn-primary h-12"
            data-testid="submit-register-btn"
          >
            {loading ? "Registering..." : "Complete Registration"}
          </Button>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function CheckInForm({ setView }) {
  const [employeeNumber, setEmployeeNumber] = useState("");
  const [roomNumber, setRoomNumber] = useState("");
  const [date, setDate] = useState(new Date());
  const [time, setTime] = useState("");
  const [loading, setLoading] = useState(false);
  const [verifiedEmployee, setVerifiedEmployee] = useState(null);
  const [verifying, setVerifying] = useState(false);
  const sigRef = useRef(null);

  const clearSignature = () => {
    sigRef.current?.clear();
  };

  const handleVerifyEmployee = async () => {
    if (!employeeNumber) {
      toast.error("Please enter employee number");
      return;
    }

    setVerifying(true);
    try {
      const response = await axios.get(`${API}/guests/${employeeNumber}`);
      setVerifiedEmployee(response.data);
      toast.success(`Employee found: ${response.data.name}`);
    } catch (error) {
      toast.error("Employee not found. Please register first.");
      setVerifiedEmployee(null);
    } finally {
      setVerifying(false);
    }
  };

  const handleClearVerification = () => {
    setVerifiedEmployee(null);
    setEmployeeNumber("");
  };

  const handleCheckIn = async () => {
    if (!verifiedEmployee) {
      toast.error("Please verify employee number first");
      return;
    }
    if (!roomNumber) {
      toast.error("Please enter room number");
      return;
    }
    if (!date) {
      toast.error("Please select check-in date");
      return;
    }
    if (!time) {
      toast.error("Please select check-in time");
      return;
    }
    if (sigRef.current?.isEmpty()) {
      toast.error("Please provide your signature");
      return;
    }

    setLoading(true);
    try {
      const signature = sigRef.current.toDataURL();
      await axios.post(`${API}/checkin`, {
        employee_number: employeeNumber,
        room_number: roomNumber,
        check_in_date: format(date, "yyyy-MM-dd"),
        check_in_time: time,
        signature
      });
      toast.success("Check-in successful! Welcome to Hodler Inn.");
      setView("menu");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Check-in failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
      className="w-full max-w-md"
    >
      <Card className="glass-card p-8" data-testid="checkin-form-card">
        <CardHeader className="pb-6">
          <button 
            onClick={() => setView("menu")} 
            className="text-vault-text-secondary hover:text-vault-gold transition-colors mb-4 flex items-center gap-2"
            data-testid="back-btn"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
          <CardTitle className="font-outfit text-2xl font-bold text-vault-text tracking-tight flex items-center gap-3">
            <LogIn className="w-6 h-6 text-vault-gold" />
            Guest Check-In
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Employee Verification Section */}
          {!verifiedEmployee ? (
            <div className="space-y-4">
              <div>
                <label className="vault-label">Employee Number</label>
                <div className="relative">
                  <Hash className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-vault-text-secondary" />
                  <Input
                    value={employeeNumber}
                    onChange={(e) => setEmployeeNumber(e.target.value)}
                    placeholder="Enter employee number"
                    className="vault-input pl-10"
                    data-testid="checkin-employee-input"
                  />
                </div>
              </div>
              <Button
                onClick={handleVerifyEmployee}
                disabled={verifying}
                className="w-full vault-btn-primary h-12"
                data-testid="verify-employee-btn"
              >
                {verifying ? "Verifying..." : "Verify Employee"}
              </Button>
            </div>
          ) : (
            <>
              {/* Verified Employee Info */}
              <div className="bg-vault-success/10 border border-vault-success/30 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-vault-success text-xs uppercase tracking-wider mb-1">Verified Employee</p>
                    <p className="text-vault-text font-bold text-lg">{verifiedEmployee.name}</p>
                    <p className="text-vault-text-secondary font-mono text-sm">ID: {verifiedEmployee.employee_number}</p>
                  </div>
                  <button 
                    onClick={handleClearVerification}
                    className="text-vault-text-secondary hover:text-vault-gold text-xs underline"
                  >
                    Change
                  </button>
                </div>
              </div>

              <div>
                <label className="vault-label">Room Number</label>
                <div className="relative">
                  <DoorOpen className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-vault-text-secondary" />
                  <Input
                    value={roomNumber}
                    onChange={(e) => setRoomNumber(e.target.value)}
                    placeholder="Enter room number"
                    className="vault-input pl-10"
                    data-testid="checkin-room-input"
                  />
                </div>
              </div>
              <div>
                <label className="vault-label">Check-In Date</label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      className={cn(
                        "w-full vault-input justify-start text-left font-normal",
                        !date && "text-muted-foreground"
                      )}
                      data-testid="checkin-date-btn"
                    >
                      <CalendarIcon className="mr-2 h-4 w-4 text-vault-text-secondary" />
                      {date ? format(date, "dd MMM yyyy") : "Select date"}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0 bg-vault-surface border-vault-border" align="start">
                    <Calendar
                      mode="single"
                      selected={date}
                      onSelect={setDate}
                      initialFocus
                      className="bg-vault-surface text-vault-text"
                      data-testid="checkin-calendar"
                    />
                  </PopoverContent>
                </Popover>
              </div>
              <div>
                <label className="vault-label">Check-In Time (24hr)</label>
                <div className="relative">
                  <Clock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-vault-text-secondary" />
                  <Input
                    type="time"
                    value={time}
                    onChange={(e) => setTime(e.target.value)}
                    className="vault-input pl-10"
                    placeholder="HH:MM"
                    data-testid="checkin-time-input"
                  />
                </div>
                <p className="text-vault-text-secondary text-xs mt-1">Use 24-hour format (e.g., 14:00 for 2:00 PM)</p>
              </div>
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="vault-label mb-0">Signature</label>
                  <button 
                    onClick={clearSignature}
                    className="text-vault-text-secondary hover:text-vault-gold text-xs flex items-center gap-1 transition-colors"
                    data-testid="clear-checkin-signature-btn"
                  >
                    <Eraser className="w-3 h-3" />
                    Clear
                  </button>
                </div>
                <div className="signature-wrapper">
                  <SignatureCanvas
                    ref={sigRef}
                    canvasProps={{
                      className: "signature-canvas w-full h-32 bg-transparent",
                      style: { width: "100%", height: "128px" }
                    }}
                    penColor="#fbbf24"
                    backgroundColor="transparent"
                    data-testid="checkin-signature-canvas"
                  />
                </div>
                <p className="text-vault-text-secondary text-xs mt-1">
                  This signature will be used for both check-in and check-out.
                </p>
              </div>
              <Button
                onClick={handleCheckIn}
                disabled={loading}
                className="w-full vault-btn-primary h-12"
                data-testid="submit-checkin-btn"
              >
                {loading ? "Processing..." : "Complete Check-In"}
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

function CheckOutForm({ setView }) {
  const [roomNumber, setRoomNumber] = useState("");
  const [date, setDate] = useState(new Date());
  const [time, setTime] = useState("");
  const [loading, setLoading] = useState(false);

  const handleCheckOut = async () => {
    if (!roomNumber) {
      toast.error("Please enter room number");
      return;
    }
    if (!date) {
      toast.error("Please select check-out date");
      return;
    }
    if (!time) {
      toast.error("Please select check-out time");
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${API}/checkout`, {
        room_number: roomNumber,
        check_out_date: format(date, "yyyy-MM-dd"),
        check_out_time: time
      });
      toast.success("Check-out successful! Thank you for staying at Hodler Inn.");
      setView("menu");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Check-out failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
      className="w-full max-w-md"
    >
      <Card className="glass-card p-8" data-testid="checkout-form-card">
        <CardHeader className="pb-6">
          <button 
            onClick={() => setView("menu")} 
            className="text-vault-text-secondary hover:text-vault-gold transition-colors mb-4 flex items-center gap-2"
            data-testid="back-btn"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
          <CardTitle className="font-outfit text-2xl font-bold text-vault-text tracking-tight flex items-center gap-3">
            <LogOut className="w-6 h-6 text-vault-gold" />
            Guest Check-Out
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <label className="vault-label">Room Number</label>
            <div className="relative">
              <DoorOpen className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-vault-text-secondary" />
              <Input
                value={roomNumber}
                onChange={(e) => setRoomNumber(e.target.value)}
                placeholder="Enter room number"
                className="vault-input pl-10"
                data-testid="checkout-room-input"
              />
            </div>
          </div>
          <div>
            <label className="vault-label">Check-Out Date</label>
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  className={cn(
                    "w-full vault-input justify-start text-left font-normal",
                    !date && "text-muted-foreground"
                  )}
                  data-testid="checkout-date-btn"
                >
                  <CalendarIcon className="mr-2 h-4 w-4 text-vault-text-secondary" />
                  {date ? format(date, "dd MMM yyyy") : "Select date"}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0 bg-vault-surface border-vault-border" align="start">
                <Calendar
                  mode="single"
                  selected={date}
                  onSelect={setDate}
                  initialFocus
                  className="bg-vault-surface text-vault-text"
                  data-testid="checkout-calendar"
                />
              </PopoverContent>
            </Popover>
          </div>
          <div>
            <label className="vault-label">Check-Out Time (24hr)</label>
            <div className="relative">
              <Clock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-vault-text-secondary" />
              <Input
                type="time"
                value={time}
                onChange={(e) => setTime(e.target.value)}
                className="vault-input pl-10"
                placeholder="HH:MM"
                data-testid="checkout-time-input"
              />
            </div>
            <p className="text-vault-text-secondary text-xs mt-1">Use 24-hour format (e.g., 14:00 for 2:00 PM)</p>
          </div>
          <Button
            onClick={handleCheckOut}
            disabled={loading}
            className="w-full vault-btn-primary h-12"
            data-testid="submit-checkout-btn"
          >
            {loading ? "Processing..." : "Complete Check-Out"}
          </Button>
        </CardContent>
      </Card>
    </motion.div>
  );
}


function SignInSheetView({ setView }) {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [accessCode, setAccessCode] = useState("");
  const [isVerified, setIsVerified] = useState(false);
  const [verifying, setVerifying] = useState(false);

  const handleVerifyAccess = async () => {
    if (!accessCode) {
      toast.error("Please enter company name or employee ID");
      return;
    }

    setVerifying(true);
    
    // Check if it's the company code "cpkc" (case insensitive)
    if (accessCode.toLowerCase() === "cpkc") {
      setIsVerified(true);
      fetchRecords();
      toast.success("Access granted");
      setVerifying(false);
      return;
    }

    // Check if it's a valid employee number
    try {
      await axios.get(`${API}/guests/${accessCode}`);
      setIsVerified(true);
      fetchRecords();
      toast.success("Access granted");
    } catch (error) {
      toast.error("Invalid company name or employee ID");
    } finally {
      setVerifying(false);
    }
  };

  const fetchRecords = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/admin/records`);
      setRecords(response.data);
    } catch (error) {
      toast.error("Failed to load records");
    } finally {
      setLoading(false);
    }
  };

  // Access verification screen
  if (!isVerified) {
    return (
      <motion.div
        variants={pageVariants}
        initial="initial"
        animate="animate"
        exit="exit"
        transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
        className="w-full max-w-md"
      >
        <Card className="glass-card p-8" data-testid="signin-access-card">
          <CardHeader className="pb-6">
            <button 
              onClick={() => setView("menu")} 
              className="text-vault-text-secondary hover:text-vault-gold transition-colors mb-4 flex items-center gap-2"
              data-testid="back-btn"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </button>
            <CardTitle className="font-outfit text-2xl font-bold text-vault-text tracking-tight flex items-center gap-3">
              <ClipboardList className="w-6 h-6 text-vault-gold" />
              View Sign-In Sheet
            </CardTitle>
            <p className="text-vault-text-secondary font-manrope mt-2 text-sm">
              Enter your company name or employee ID to view records
            </p>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <label className="vault-label">Company Name or Employee ID</label>
              <div className="relative">
                <Hash className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-vault-text-secondary" />
                <Input
                  value={accessCode}
                  onChange={(e) => setAccessCode(e.target.value)}
                  placeholder="Enter company name or employee ID"
                  className="vault-input pl-10"
                  data-testid="access-code-input"
                  onKeyDown={(e) => e.key === 'Enter' && handleVerifyAccess()}
                />
              </div>
            </div>
            <Button
              onClick={handleVerifyAccess}
              disabled={verifying}
              className="w-full vault-btn-primary h-12"
              data-testid="verify-access-btn"
            >
              {verifying ? "Verifying..." : "View Sign-In Sheet"}
            </Button>
          </CardContent>
        </Card>
      </motion.div>
    );
  }

  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
      className="w-full max-w-6xl px-4"
    >
      <Card className="glass-card" data-testid="signin-sheet-view-card">
        <CardHeader className="pb-4">
          <button 
            onClick={() => setView("menu")} 
            className="text-vault-text-secondary hover:text-vault-gold transition-colors mb-4 flex items-center gap-2"
            data-testid="back-btn"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Menu
          </button>
          <div className="text-center">
            <CardTitle className="font-outfit text-2xl font-bold text-vault-gold tracking-tight">
              Hodler Inn
            </CardTitle>
            <p className="text-vault-text-secondary text-sm mt-1">820 Hwy 59 N Heavener, OK, 74937</p>
            <p className="text-vault-text-secondary text-sm">Phone: 918-653-7801</p>
          </div>
        </CardHeader>
        <CardContent className="p-0 overflow-x-auto">
          {loading ? (
            <div className="text-center py-8 text-vault-text-secondary">Loading...</div>
          ) : (
            <div className="min-w-[1000px]">
              <Table>
                <TableHeader>
                  <TableRow className="table-header border-vault-border hover:bg-transparent">
                    <TableHead className="text-vault-gold w-12">#</TableHead>
                    <TableHead className="text-vault-gold">Stay Type</TableHead>
                    <TableHead className="text-vault-gold">Name</TableHead>
                    <TableHead className="text-vault-gold">Employee ID</TableHead>
                    <TableHead className="text-vault-gold">Signature In</TableHead>
                    <TableHead className="text-vault-gold">Signature Out</TableHead>
                    <TableHead className="text-vault-gold">Date In</TableHead>
                    <TableHead className="text-vault-gold">Time In</TableHead>
                    <TableHead className="text-vault-gold">Date Out</TableHead>
                    <TableHead className="text-vault-gold">Time Out</TableHead>
                    <TableHead className="text-vault-gold">Room #</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {records.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={11} className="text-center text-vault-text-secondary py-8">
                        No records found
                      </TableCell>
                    </TableRow>
                  ) : (
                    records.map((record, index) => (
                      <TableRow key={record.id} className="table-row border-vault-border">
                        <TableCell className="font-mono text-vault-text">{index + 1}</TableCell>
                        <TableCell className="text-vault-text">Single Stay</TableCell>
                        <TableCell className="text-vault-text font-medium">{record.employee_name}</TableCell>
                        <TableCell className="font-mono text-vault-text">{record.employee_number}</TableCell>
                        <TableCell className="text-vault-success font-medium">
                          {record.signature ? "Signed" : "—"}
                        </TableCell>
                        <TableCell className="text-vault-success font-medium">
                          {record.is_checked_out && record.signature ? "Signed" : "—"}
                        </TableCell>
                        <TableCell className="text-vault-text">{record.check_in_date}</TableCell>
                        <TableCell className="font-mono text-vault-text">{record.check_in_time}</TableCell>
                        <TableCell className="text-vault-text">{record.check_out_date || "—"}</TableCell>
                        <TableCell className="font-mono text-vault-text">{record.check_out_time || "—"}</TableCell>
                        <TableCell className="font-mono text-vault-gold font-bold">{record.room_number}</TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          )}
          <p className="text-vault-text-secondary text-xs text-center py-4 md:hidden">
            ← Swipe table horizontally to see all columns →
          </p>
        </CardContent>
      </Card>
    </motion.div>
  );
}
