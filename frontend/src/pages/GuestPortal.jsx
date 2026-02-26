import { useState, useRef } from "react";
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
  Settings
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
  const [view, setView] = useState("menu"); // menu, register, checkin, checkout
  const navigate = useNavigate();

  return (
    <div className="kiosk-container grid-bg min-h-screen relative">
      {/* Logo Header */}
      <div className="absolute top-6 left-6 flex items-center gap-3">
        <div className="w-10 h-10 bg-vault-gold rounded-lg flex items-center justify-center">
          <span className="font-outfit font-bold text-black text-xl">H</span>
        </div>
        <div>
          <h1 className="font-outfit font-bold text-vault-text text-xl tracking-tight">HODLER INN</h1>
          <p className="font-mono text-[10px] text-vault-gold uppercase tracking-widest">Immutable Comfort</p>
        </div>
      </div>

      {/* Admin Link */}
      <button 
        onClick={() => navigate("/admin")}
        className="absolute top-6 right-6 text-vault-text-secondary hover:text-vault-gold transition-colors"
        data-testid="admin-link"
      >
        <Settings className="w-5 h-5" />
      </button>

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
          <Button
            onClick={() => setView("register")}
            className="w-full vault-btn-primary h-14 text-lg flex items-center justify-center gap-3"
            data-testid="register-btn"
          >
            <UserPlus className="w-5 h-5" />
            Register
          </Button>
          <Button
            onClick={() => setView("checkin")}
            className="w-full vault-btn-primary h-14 text-lg flex items-center justify-center gap-3"
            data-testid="checkin-btn"
          >
            <LogIn className="w-5 h-5" />
            Check In
          </Button>
          <Button
            onClick={() => setView("checkout")}
            className="w-full vault-btn-primary h-14 text-lg flex items-center justify-center gap-3"
            data-testid="checkout-btn"
          >
            <LogOut className="w-5 h-5" />
            Check Out
          </Button>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function RegisterForm({ setView }) {
  const [employeeNumber, setEmployeeNumber] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const sigRef = useRef(null);

  const clearSignature = () => {
    sigRef.current?.clear();
  };

  const handleRegister = async () => {
    if (!employeeNumber || !name) {
      toast.error("Please fill in all fields");
      return;
    }
    if (sigRef.current?.isEmpty()) {
      toast.error("Please provide your signature");
      return;
    }

    setLoading(true);
    try {
      const signature = sigRef.current.toDataURL();
      await axios.post(`${API}/guests/register`, {
        employee_number: employeeNumber,
        name,
        signature
      });
      toast.success("Registration successful!");
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
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="vault-label mb-0">Signature</label>
              <button 
                onClick={clearSignature}
                className="text-vault-text-secondary hover:text-vault-gold text-xs flex items-center gap-1 transition-colors"
                data-testid="clear-signature-btn"
              >
                <Eraser className="w-3 h-3" />
                Clear
              </button>
            </div>
            <div className="signature-wrapper">
              <SignatureCanvas
                ref={sigRef}
                canvasProps={{
                  className: "signature-canvas w-full h-40 bg-transparent",
                  style: { width: "100%", height: "160px" }
                }}
                penColor="#fbbf24"
                backgroundColor="transparent"
                data-testid="signature-canvas"
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
  const [time, setTime] = useState(format(new Date(), "HH:mm"));
  const [loading, setLoading] = useState(false);

  const handleCheckIn = async () => {
    if (!employeeNumber || !roomNumber || !date || !time) {
      toast.error("Please fill in all fields");
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${API}/checkin`, {
        employee_number: employeeNumber,
        room_number: roomNumber,
        check_in_date: format(date, "yyyy-MM-dd"),
        check_in_time: time
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
            <label className="vault-label">Check-In Time</label>
            <div className="relative">
              <Clock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-vault-text-secondary" />
              <Input
                type="time"
                value={time}
                onChange={(e) => setTime(e.target.value)}
                className="vault-input pl-10"
                data-testid="checkin-time-input"
              />
            </div>
          </div>
          <Button
            onClick={handleCheckIn}
            disabled={loading}
            className="w-full vault-btn-primary h-12"
            data-testid="submit-checkin-btn"
          >
            {loading ? "Processing..." : "Complete Check-In"}
          </Button>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function CheckOutForm({ setView }) {
  const [roomNumber, setRoomNumber] = useState("");
  const [date, setDate] = useState(new Date());
  const [time, setTime] = useState(format(new Date(), "HH:mm"));
  const [loading, setLoading] = useState(false);

  const handleCheckOut = async () => {
    if (!roomNumber || !date || !time) {
      toast.error("Please fill in all fields");
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
            <label className="vault-label">Check-Out Time</label>
            <div className="relative">
              <Clock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-vault-text-secondary" />
              <Input
                type="time"
                value={time}
                onChange={(e) => setTime(e.target.value)}
                className="vault-input pl-10"
                data-testid="checkout-time-input"
              />
            </div>
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
