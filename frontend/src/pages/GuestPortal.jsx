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

  // Auto-refresh every 5 minutes to keep screen active and reset to menu
  React.useEffect(() => {
    let idleTimer;
    let refreshInterval;
    
    const resetToMenu = () => {
      if (view !== "menu") {
        setView("menu");
      }
    };

    const resetIdleTimer = () => {
      clearTimeout(idleTimer);
      // Reset to menu after 2 minutes of inactivity
      idleTimer = setTimeout(resetToMenu, 2 * 60 * 1000);
    };

    // Auto-refresh page every 10 minutes to prevent any caching issues
    refreshInterval = setInterval(() => {
      if (view === "menu") {
        window.location.reload();
      }
    }, 10 * 60 * 1000);

    // Keep screen awake using Wake Lock API if available
    let wakeLock = null;
    const requestWakeLock = async () => {
      try {
        if ('wakeLock' in navigator) {
          wakeLock = await navigator.wakeLock.request('screen');
        }
      } catch (err) {
        console.log('Wake Lock not supported');
      }
    };
    requestWakeLock();

    // Listen for user activity
    const events = ['mousedown', 'mousemove', 'keydown', 'touchstart', 'scroll'];
    events.forEach(event => document.addEventListener(event, resetIdleTimer));
    resetIdleTimer();

    return () => {
      clearTimeout(idleTimer);
      clearInterval(refreshInterval);
      events.forEach(event => document.removeEventListener(event, resetIdleTimer));
      if (wakeLock) wakeLock.release();
    };
  }, [view]);

  return (
    <div className="min-h-screen relative bg-gray-100">
      {/* Logo Header */}
      <div className="absolute top-6 left-6 flex items-center gap-3">
        <img 
          src="https://customer-assets.emergentagent.com/job_guest-hotel-mgmt/artifacts/56yphta2_17721406444867042425090808501904.jpg" 
          alt="Hodler Inn Logo" 
          className="w-12 h-12 rounded-lg object-cover"
        />
        <div>
          <h1 className="font-outfit font-bold text-gray-800 text-xl tracking-tight">HODLER INN</h1>
          <p className="font-mono text-[10px] text-amber-600 uppercase tracking-widest">Be Responsible to Be Free</p>
        </div>
      </div>

      {/* Top Right Buttons */}
      <div className="absolute top-6 right-6 flex items-center gap-2">
        {/* Fullscreen/Kiosk Mode Button */}
        <button 
          onClick={toggleFullscreen}
          className="flex items-center gap-2 text-gray-600 hover:text-amber-600 transition-colors bg-white px-3 py-2 rounded-lg border border-gray-300 shadow-sm"
          data-testid="fullscreen-btn"
          title={isFullscreen ? "Exit Kiosk Mode" : "Enter Kiosk Mode"}
        >
          {isFullscreen ? <Minimize className="w-4 h-4" /> : <Maximize className="w-4 h-4" />}
          <span className="text-sm font-mono hidden sm:inline">{isFullscreen ? "Exit Kiosk" : "Kiosk Mode"}</span>
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
        {view === "help" && (
          <HelpView key="help" setView={setView} />
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
      <Card className="bg-white border border-gray-200 shadow-xl p-8 rounded-2xl" data-testid="main-menu-card">
        <CardHeader className="text-center pb-8">
          <CardTitle className="font-outfit text-3xl font-bold text-gray-800 tracking-tight">
            Welcome to Hodler Inn
          </CardTitle>
          <p className="text-red-600 font-bold text-lg mt-3">
            Railroad Crew Check In Here
          </p>
          <p className="text-gray-600 font-manrope mt-2">
            Select an option below to continue
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-2">
            <p className="text-gray-600 text-sm text-center">
              <span className="text-amber-600 font-medium">Note:</span> Register only if this is your <span className="text-amber-600 font-medium">first time</span>. 
              Already registered? Go directly to <span className="text-amber-600 font-medium">Check In</span>.
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
          <div className="pt-4 border-t border-gray-200 space-y-3">
            <Button
              onClick={() => setView("signin")}
              className="w-full h-12 flex items-center justify-center gap-3 bg-gray-100 hover:bg-gray-200 text-gray-700 border border-gray-300"
              data-testid="signin-sheet-btn"
            >
              <ClipboardList className="w-5 h-5" />
              View Sign-In Sheet
            </Button>
            <Button
              onClick={() => setView("help")}
              className="w-full h-12 flex items-center justify-center gap-3 bg-blue-600 hover:bg-blue-700 text-white font-bold uppercase tracking-wide"
              data-testid="help-btn"
            >
              <HelpCircle className="w-5 h-5" />
              How to Use / Help
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
      <Card className="bg-white border border-gray-200 shadow-xl p-8 rounded-2xl" data-testid="register-form-card">
        <CardHeader className="pb-6">
          <button 
            onClick={() => setView("menu")} 
            className="text-gray-500 hover:text-amber-600 transition-colors mb-4 flex items-center gap-2"
            data-testid="back-btn"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
          <CardTitle className="font-outfit text-2xl font-bold text-gray-800 tracking-tight flex items-center gap-3">
            <UserPlus className="w-6 h-6 text-amber-500" />
            Guest Registration
          </CardTitle>
          <p className="text-gray-600 text-sm mt-2">
            Register with your employee details. Signature will be captured at check-in.
          </p>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <label className="text-xs text-amber-600 uppercase tracking-wider mb-1 block font-medium">Employee Number</label>
            <div className="relative">
              <Hash className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                value={employeeNumber}
                onChange={(e) => setEmployeeNumber(e.target.value)}
                placeholder="Enter employee number"
                className="pl-10 bg-gray-50 border-gray-300 text-gray-800 focus:border-amber-500"
                data-testid="employee-number-input"
              />
            </div>
          </div>
          <div>
            <label className="text-xs text-amber-600 uppercase tracking-wider mb-1 block font-medium">Full Name</label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Enter your full name"
                className="pl-10 bg-gray-50 border-gray-300 text-gray-800 focus:border-amber-500"
                data-testid="name-input"
              />
            </div>
          </div>
          <Button
            onClick={handleRegister}
            disabled={loading}
            className="w-full bg-amber-500 hover:bg-amber-600 text-black font-bold h-12"
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
      <Card className="bg-white border border-gray-200 shadow-xl rounded-2xl p-8" data-testid="checkin-form-card">
        <CardHeader className="pb-6">
          <button 
            onClick={() => setView("menu")} 
            className="text-gray-600 hover:text-amber-600 transition-colors mb-4 flex items-center gap-2"
            data-testid="back-btn"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
          <CardTitle className="font-outfit text-2xl font-bold text-gray-800 tracking-tight flex items-center gap-3">
            <LogIn className="w-6 h-6 text-amber-600" />
            Guest Check-In
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Employee Verification Section */}
          {!verifiedEmployee ? (
            <div className="space-y-4">
              <div>
                <label className="text-xs text-amber-600 uppercase tracking-wider mb-1 block font-medium">Employee Number</label>
                <div className="relative">
                  <Hash className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-600" />
                  <Input
                    value={employeeNumber}
                    onChange={(e) => setEmployeeNumber(e.target.value)}
                    placeholder="Enter employee number"
                    className="bg-gray-50 border-gray-300 text-gray-800 pl-10"
                    data-testid="checkin-employee-input"
                  />
                </div>
              </div>
              <Button
                onClick={handleVerifyEmployee}
                disabled={verifying}
                className="w-full bg-amber-500 hover:bg-amber-600 text-black font-bold h-12"
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
                    <p className="text-gray-800 font-bold text-lg">{verifiedEmployee.name}</p>
                    <p className="text-gray-600 font-mono text-sm">ID: {verifiedEmployee.employee_number}</p>
                  </div>
                  <button 
                    onClick={handleClearVerification}
                    className="text-gray-600 hover:text-amber-600 text-xs underline"
                  >
                    Change
                  </button>
                </div>
              </div>

              <div>
                <label className="text-xs text-amber-600 uppercase tracking-wider mb-1 block font-medium">Room Number</label>
                <div className="relative">
                  <DoorOpen className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-600" />
                  <Input
                    value={roomNumber}
                    onChange={(e) => setRoomNumber(e.target.value)}
                    placeholder="Enter room number"
                    className="bg-gray-50 border-gray-300 text-gray-800 pl-10"
                    data-testid="checkin-room-input"
                  />
                </div>
              </div>
              <div>
                <label className="text-xs text-amber-600 uppercase tracking-wider mb-1 block font-medium">Check-In Date</label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      className={cn(
                        "w-full bg-gray-50 border-gray-300 text-gray-800 justify-start text-left font-normal",
                        !date && "text-muted-foreground"
                      )}
                      data-testid="checkin-date-btn"
                    >
                      <CalendarIcon className="mr-2 h-4 w-4 text-gray-600" />
                      {date ? format(date, "dd MMM yyyy") : "Select date"}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0 bg-vault-surface border-gray-200" align="start">
                    <Calendar
                      mode="single"
                      selected={date}
                      onSelect={setDate}
                      initialFocus
                      className="bg-vault-surface text-gray-800"
                      data-testid="checkin-calendar"
                    />
                  </PopoverContent>
                </Popover>
              </div>
              <div>
                <label className="text-xs text-amber-600 uppercase tracking-wider mb-1 block font-medium">Check-In Time (24hr)</label>
                <div className="relative">
                  <Clock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-600" />
                  <Input
                    type="time"
                    value={time}
                    onChange={(e) => setTime(e.target.value)}
                    className="bg-gray-50 border-gray-300 text-gray-800 pl-10"
                    placeholder="HH:MM"
                    data-testid="checkin-time-input"
                  />
                </div>
                <p className="text-gray-600 text-xs mt-1">Use 24-hour format (e.g., 14:00 for 2:00 PM)</p>
              </div>
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="text-xs text-amber-600 uppercase tracking-wider mb-1 block font-medium mb-0">Signature</label>
                  <button 
                    onClick={clearSignature}
                    className="text-gray-600 hover:text-amber-600 text-xs flex items-center gap-1 transition-colors"
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
                <p className="text-gray-600 text-xs mt-1">
                  This signature will be used for both check-in and check-out.
                </p>
              </div>
              <Button
                onClick={handleCheckIn}
                disabled={loading}
                className="w-full bg-amber-500 hover:bg-amber-600 text-black font-bold h-12"
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
      <Card className="bg-white border border-gray-200 shadow-xl rounded-2xl p-8" data-testid="checkout-form-card">
        <CardHeader className="pb-6">
          <button 
            onClick={() => setView("menu")} 
            className="text-gray-600 hover:text-amber-600 transition-colors mb-4 flex items-center gap-2"
            data-testid="back-btn"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
          <CardTitle className="font-outfit text-2xl font-bold text-gray-800 tracking-tight flex items-center gap-3">
            <LogOut className="w-6 h-6 text-amber-600" />
            Guest Check-Out
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <label className="text-xs text-amber-600 uppercase tracking-wider mb-1 block font-medium">Room Number</label>
            <div className="relative">
              <DoorOpen className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-600" />
              <Input
                value={roomNumber}
                onChange={(e) => setRoomNumber(e.target.value)}
                placeholder="Enter room number"
                className="bg-gray-50 border-gray-300 text-gray-800 pl-10"
                data-testid="checkout-room-input"
              />
            </div>
          </div>
          <div>
            <label className="text-xs text-amber-600 uppercase tracking-wider mb-1 block font-medium">Check-Out Date</label>
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  className={cn(
                    "w-full bg-gray-50 border-gray-300 text-gray-800 justify-start text-left font-normal",
                    !date && "text-muted-foreground"
                  )}
                  data-testid="checkout-date-btn"
                >
                  <CalendarIcon className="mr-2 h-4 w-4 text-gray-600" />
                  {date ? format(date, "dd MMM yyyy") : "Select date"}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0 bg-vault-surface border-gray-200" align="start">
                <Calendar
                  mode="single"
                  selected={date}
                  onSelect={setDate}
                  initialFocus
                  className="bg-vault-surface text-gray-800"
                  data-testid="checkout-calendar"
                />
              </PopoverContent>
            </Popover>
          </div>
          <div>
            <label className="text-xs text-amber-600 uppercase tracking-wider mb-1 block font-medium">Check-Out Time (24hr)</label>
            <div className="relative">
              <Clock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-600" />
              <Input
                type="time"
                value={time}
                onChange={(e) => setTime(e.target.value)}
                className="bg-gray-50 border-gray-300 text-gray-800 pl-10"
                placeholder="HH:MM"
                data-testid="checkout-time-input"
              />
            </div>
            <p className="text-gray-600 text-xs mt-1">Use 24-hour format (e.g., 14:00 for 2:00 PM)</p>
          </div>
          <Button
            onClick={handleCheckOut}
            disabled={loading}
            className="w-full bg-amber-500 hover:bg-amber-600 text-black font-bold h-12"
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
        <Card className="bg-white border border-gray-200 shadow-xl rounded-2xl p-8" data-testid="signin-access-card">
          <CardHeader className="pb-6">
            <button 
              onClick={() => setView("menu")} 
              className="text-gray-600 hover:text-amber-600 transition-colors mb-4 flex items-center gap-2"
              data-testid="back-btn"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </button>
            <CardTitle className="font-outfit text-2xl font-bold text-gray-800 tracking-tight flex items-center gap-3">
              <ClipboardList className="w-6 h-6 text-amber-600" />
              View Sign-In Sheet
            </CardTitle>
            <p className="text-gray-600 font-manrope mt-2 text-sm">
              Enter your company name or employee ID to view records
            </p>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <label className="text-xs text-amber-600 uppercase tracking-wider mb-1 block font-medium">Company Name or Employee ID</label>
              <div className="relative">
                <Hash className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-600" />
                <Input
                  value={accessCode}
                  onChange={(e) => setAccessCode(e.target.value)}
                  placeholder="Enter company name or employee ID"
                  className="bg-gray-50 border-gray-300 text-gray-800 pl-10"
                  data-testid="access-code-input"
                  onKeyDown={(e) => e.key === 'Enter' && handleVerifyAccess()}
                />
              </div>
            </div>
            <Button
              onClick={handleVerifyAccess}
              disabled={verifying}
              className="w-full bg-amber-500 hover:bg-amber-600 text-black font-bold h-12"
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
      <Card className="bg-white border border-gray-200 shadow-xl rounded-2xl" data-testid="signin-sheet-view-card">
        <CardHeader className="pb-4">
          <button 
            onClick={() => setView("menu")} 
            className="text-gray-600 hover:text-amber-600 transition-colors mb-4 flex items-center gap-2"
            data-testid="back-btn"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Menu
          </button>
          <div className="text-center">
            <CardTitle className="font-outfit text-2xl font-bold text-amber-600 tracking-tight">
              Hodler Inn
            </CardTitle>
            <p className="text-gray-600 text-sm mt-1">820 Hwy 59 N Heavener, OK, 74937</p>
            <p className="text-gray-600 text-sm">Phone: 918-653-7801</p>
          </div>
        </CardHeader>
        <CardContent className="p-0 overflow-x-auto">
          {loading ? (
            <div className="text-center py-8 text-gray-600">Loading...</div>
          ) : (
            <div className="min-w-[1000px]">
              <Table>
                <TableHeader>
                  <TableRow className="table-header border-gray-200 hover:bg-transparent">
                    <TableHead className="text-amber-600 w-12">#</TableHead>
                    <TableHead className="text-amber-600">Stay Type</TableHead>
                    <TableHead className="text-amber-600">Name</TableHead>
                    <TableHead className="text-amber-600">Employee ID</TableHead>
                    <TableHead className="text-amber-600">Signature In</TableHead>
                    <TableHead className="text-amber-600">Signature Out</TableHead>
                    <TableHead className="text-amber-600">Date In</TableHead>
                    <TableHead className="text-amber-600">Time In</TableHead>
                    <TableHead className="text-amber-600">Date Out</TableHead>
                    <TableHead className="text-amber-600">Time Out</TableHead>
                    <TableHead className="text-amber-600">Room #</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {records.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={11} className="text-center text-gray-600 py-8">
                        No records found
                      </TableCell>
                    </TableRow>
                  ) : (
                    records.map((record, index) => (
                      <TableRow key={record.id} className="table-row border-gray-200">
                        <TableCell className="font-mono text-gray-800">{index + 1}</TableCell>
                        <TableCell className="text-gray-800">Single Stay</TableCell>
                        <TableCell className="text-gray-800 font-medium">{record.employee_name}</TableCell>
                        <TableCell className="font-mono text-gray-800">{record.employee_number}</TableCell>
                        <TableCell className="text-vault-success font-medium">
                          {record.signature ? "Signed" : "—"}
                        </TableCell>
                        <TableCell className="text-vault-success font-medium">
                          {record.is_checked_out && record.signature ? "Signed" : "—"}
                        </TableCell>
                        <TableCell className="text-gray-800">{record.check_in_date}</TableCell>
                        <TableCell className="font-mono text-gray-800">{record.check_in_time}</TableCell>
                        <TableCell className="text-gray-800">{record.check_out_date || "—"}</TableCell>
                        <TableCell className="font-mono text-gray-800">{record.check_out_time || "—"}</TableCell>
                        <TableCell className="font-mono text-amber-600 font-bold">{record.room_number}</TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          )}
          <p className="text-gray-600 text-xs text-center py-4 md:hidden">
            ← Swipe table horizontally to see all columns →
          </p>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function HelpView({ setView }) {
  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
      className="w-full max-w-2xl"
    >
      <Card className="bg-white border border-gray-200 shadow-xl rounded-2xl p-6 md:p-8" data-testid="help-view-card">
        <CardHeader className="pb-4">
          <button 
            onClick={() => setView("menu")} 
            className="text-gray-600 hover:text-amber-600 transition-colors mb-4 flex items-center gap-2"
            data-testid="back-btn"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Menu
          </button>
          <CardTitle className="font-outfit text-2xl font-bold text-gray-800 tracking-tight flex items-center gap-3">
            <HelpCircle className="w-6 h-6 text-amber-600" />
            How to Use Guest Portal
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Step 1: Register */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-full bg-amber-500 flex items-center justify-center flex-shrink-0">
                <span className="text-black font-bold text-lg">1</span>
              </div>
              <div>
                <h3 className="font-outfit text-lg font-bold text-amber-600 mb-1">REGISTER (First-Time Only)</h3>
                <ul className="text-gray-600 text-sm space-y-1">
                  <li>• Tap the <span className="text-amber-400 font-medium">GOLD "Register"</span> button</li>
                  <li>• Enter your <span className="text-gray-800">Employee Number</span></li>
                  <li>• Enter your <span className="text-gray-800">Full Name</span></li>
                  <li>• Tap "Complete Registration"</li>
                </ul>
                <p className="text-amber-600 text-xs mt-2 italic">You only need to register once!</p>
              </div>
            </div>
          </div>

          {/* Step 2: Check In */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-full bg-emerald-500 flex items-center justify-center flex-shrink-0">
                <span className="text-black font-bold text-lg">2</span>
              </div>
              <div>
                <h3 className="font-outfit text-lg font-bold text-emerald-400 mb-1">CHECK IN</h3>
                <ul className="text-gray-600 text-sm space-y-1">
                  <li>• Tap the <span className="text-emerald-400 font-medium">GREEN "Check In"</span> button</li>
                  <li>• Enter your <span className="text-gray-800">Employee Number</span> → Tap "Verify"</li>
                  <li>• Enter your assigned <span className="text-gray-800">Room Number</span></li>
                  <li>• Select <span className="text-gray-800">Check-In Date</span> from calendar</li>
                  <li>• Enter <span className="text-gray-800">Check-In Time</span> (24hr format: 14:00 = 2PM)</li>
                  <li>• Sign your name in the <span className="text-gray-800">Signature Box</span></li>
                  <li>• Tap "Complete Check-In"</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Step 3: Check Out */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-full bg-red-500 flex items-center justify-center flex-shrink-0">
                <span className="text-white font-bold text-lg">3</span>
              </div>
              <div>
                <h3 className="font-outfit text-lg font-bold text-red-400 mb-1">CHECK OUT</h3>
                <ul className="text-gray-600 text-sm space-y-1">
                  <li>• Tap the <span className="text-red-400 font-medium">RED "Check Out"</span> button</li>
                  <li>• Enter your <span className="text-gray-800">Room Number</span></li>
                  <li>• Select <span className="text-gray-800">Check-Out Date</span></li>
                  <li>• Enter <span className="text-gray-800">Check-Out Time</span> (24hr format)</li>
                  <li>• Tap "Complete Check-Out"</li>
                </ul>
                <p className="text-amber-600 text-xs mt-2 italic">No signature needed - your check-in signature is used automatically.</p>
              </div>
            </div>
          </div>

          {/* Time Reference */}
          <div className="bg-black/50 border border-vault-gold/30 rounded-lg p-4">
            <h3 className="font-outfit text-sm font-bold text-amber-600 mb-3 text-center">24-HOUR TIME REFERENCE</h3>
            <div className="grid grid-cols-3 gap-2 text-center text-sm">
              <div className="text-gray-600">6 AM = <span className="text-gray-800">06:00</span></div>
              <div className="text-gray-600">12 PM = <span className="text-gray-800">12:00</span></div>
              <div className="text-gray-600">6 PM = <span className="text-gray-800">18:00</span></div>
              <div className="text-gray-600">8 AM = <span className="text-gray-800">08:00</span></div>
              <div className="text-gray-600">2 PM = <span className="text-gray-800">14:00</span></div>
              <div className="text-gray-600">10 PM = <span className="text-gray-800">22:00</span></div>
            </div>
          </div>

          {/* Help Footer */}
          <div className="text-center pt-2">
            <p className="text-gray-600 text-sm">
              Need assistance? Please contact front desk staff.
            </p>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
