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
import { DatePicker } from "@/components/ui/date-picker";
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
  HelpCircle,
  Filter,
  Globe
} from "lucide-react";
import { format } from "date-fns";
import { cn } from "@/lib/utils";
import { useNavigate } from "react-router-dom";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Language translations for Bitsy UI text
const translations = {
  en: {
    // Main Menu
    welcomeTitle: "Welcome to Hodler Inn",
    railroadCrew: "Railroad Crew Check In Here",
    selectOption: "Select an option below to continue",
    checkIn: "Check In",
    checkOut: "Check Out",
    viewSignInSheet: "View Sign-In Sheet",
    howToUseHelp: "How to Use / Help",
    // Check-in form
    guestCheckIn: "Guest Check-In",
    employeeNumber: "Employee Number",
    tapToEnterNumber: "⬇️ TAP HERE to enter number",
    name: "Name",
    nameAutoAppear: "Name will appear automatically",
    welcome: "Welcome!",
    roomNumber: "Room Number",
    tapToEnterRoom: "⬇️ TAP HERE to enter room",
    date: "Date",
    time: "Time",
    signature: "Signature (sign below)",
    clear: "Clear",
    completeCheckIn: "Complete Check-In",
    processing: "Processing...",
    // Employee not found
    employeeIdNotFound: "Employee ID Not Found",
    notInSystem: "Your employee number is not in our system.",
    didYouMean: "Did you mean one of these?",
    tapCorrectNumber: "Tap the correct number above to use it",
    pleaseUseYellowCard: "Please Use Yellow Card",
    yellowCardInstructions: "Write your Employee Number and Name on the Yellow Card.",
    adminWillAdd: "Admin will add you to the system.",
    ifError: "If you believe this is an error, please contact the front desk or call the Help Phone.",
    // Check-out
    guestCheckOut: "Guest Check-Out",
    findMyBooking: "Find My Booking",
    findingBooking: "Finding booking...",
    bookingFound: "Booking Found",
    employeeId: "Employee ID",
    room: "Room",
    checkedIn: "Checked in",
    notYourBooking: "Not your booking? Try again",
    checkOutDate: "Check-Out Date",
    onDutyTime: "On Duty Time",
    completeCheckOut: "Complete Check-Out",
    // Success
    haveGoodRest: "Have a good rest 🌙",
    welcomeToHodlerInn: "Welcome to Hodler Inn",
    thankYouForStaying: "Thank you for staying at Hodler Inn",
    haveSafeJourney: "Have a safe journey! 🚂",
    keyReminder: "Please drop your room key in the Key Drop Box in the Lounge",
    returnToMenu: "Return to Menu",
    autoReturning: "Auto-returning in a few seconds...",
    // Greetings
    goodMorning: "Good morning",
    goodAfternoon: "Good afternoon",
    goodEvening: "Good evening",
    goodNight: "Good night",
    // Language
    language: "EN",
    back: "Back",
    backToMenu: "Back to Menu",
  },
  es: {
    // Main Menu
    welcomeTitle: "Bienvenido a Hodler Inn",
    railroadCrew: "Registro de Tripulación Ferroviaria Aquí",
    selectOption: "Seleccione una opción para continuar",
    checkIn: "Registrarse",
    checkOut: "Salir",
    viewSignInSheet: "Ver Hoja de Registro",
    howToUseHelp: "Cómo Usar / Ayuda",
    // Check-in form
    guestCheckIn: "Registro de Huésped",
    employeeNumber: "Número de Empleado",
    tapToEnterNumber: "⬇️ TOQUE AQUÍ para ingresar número",
    name: "Nombre",
    nameAutoAppear: "El nombre aparecerá automáticamente",
    welcome: "¡Bienvenido!",
    roomNumber: "Número de Habitación",
    tapToEnterRoom: "⬇️ TOQUE AQUÍ para ingresar habitación",
    date: "Fecha",
    time: "Hora",
    signature: "Firma (firme abajo)",
    clear: "Borrar",
    completeCheckIn: "Completar Registro",
    processing: "Procesando...",
    // Employee not found
    employeeIdNotFound: "ID de Empleado No Encontrado",
    notInSystem: "Su número de empleado no está en nuestro sistema.",
    didYouMean: "¿Quiso decir uno de estos?",
    tapCorrectNumber: "Toque el número correcto arriba para usarlo",
    pleaseUseYellowCard: "Por Favor Use la Tarjeta Amarilla",
    yellowCardInstructions: "Escriba su Número de Empleado y Nombre en la Tarjeta Amarilla.",
    adminWillAdd: "El administrador lo agregará al sistema.",
    ifError: "Si cree que esto es un error, por favor contacte a la recepción o llame al Teléfono de Ayuda.",
    // Check-out
    guestCheckOut: "Salida de Huésped",
    findMyBooking: "Buscar Mi Reserva",
    findingBooking: "Buscando reserva...",
    bookingFound: "Reserva Encontrada",
    employeeId: "ID de Empleado",
    room: "Habitación",
    checkedIn: "Registrado",
    notYourBooking: "¿No es su reserva? Intente de nuevo",
    checkOutDate: "Fecha de Salida",
    onDutyTime: "Hora de Servicio",
    completeCheckOut: "Completar Salida",
    // Success
    haveGoodRest: "Que descanse bien 🌙",
    welcomeToHodlerInn: "Bienvenido a Hodler Inn",
    thankYouForStaying: "Gracias por hospedarse en Hodler Inn",
    haveSafeJourney: "¡Buen viaje! 🚂",
    keyReminder: "Por favor deje su llave en la Caja de Llaves en el Salón",
    returnToMenu: "Volver al Menú",
    autoReturning: "Regresando automáticamente en unos segundos...",
    // Greetings
    goodMorning: "Buenos días",
    goodAfternoon: "Buenas tardes",
    goodEvening: "Buenas tardes",
    goodNight: "Buenas noches",
    // Language
    language: "ES",
    back: "Volver",
    backToMenu: "Volver al Menú",
  }
};

// Get browser language preference
const getBrowserLanguage = () => {
  const browserLang = navigator.language || navigator.userLanguage;
  return browserLang.startsWith('es') ? 'es' : 'en';
};

// Get stored language or detect from browser
const getInitialLanguage = () => {
  const stored = localStorage.getItem('bitsy_language');
  if (stored) return stored;
  return getBrowserLanguage();
};

// Current language state (module level for voice functions)
let currentLanguage = getInitialLanguage();

// Clean employee name - remove railroad job codes like "E", "BH", "HBW", "BMR", etc.
const cleanEmployeeName = (name) => {
  if (!name) return name;
  
  // Pattern: Name might be in format "LASTNAME,(FIRSTNAME)CODES" or "LASTNAME,(FIRSTNAME) CODES"
  // Common codes: E, BH, HBW, BMR, DT, ALL, RWBH, etc.
  
  let cleanName = name;
  
  // If name is in format "LASTNAME,(FIRSTNAME)CODES"
  // Extract just the name part
  const parenMatch = name.match(/^([A-Z]+),\(([A-Z]+)\)/i);
  if (parenMatch) {
    // Format: LASTNAME,(FIRSTNAME) - take first name and last name
    const lastName = parenMatch[1];
    const firstName = parenMatch[2];
    // Capitalize properly
    cleanName = `${firstName.charAt(0).toUpperCase()}${firstName.slice(1).toLowerCase()} ${lastName.charAt(0).toUpperCase()}${lastName.slice(1).toLowerCase()}`;
  } else {
    // Remove common railroad job codes at the end of names
    // These are typically uppercase letters/numbers after the actual name
    cleanName = name
      .replace(/\s*\*?[A-Z0-9/]+\s*E\s*$/i, '')  // Remove codes ending with E
      .replace(/\s*\*?BH\s*E?\s*$/i, '')          // Remove BH codes
      .replace(/\s*\*?HBW?\s*$/i, '')             // Remove HBW codes
      .replace(/\s*\*?BMR\s*[A-Z]*\s*$/i, '')     // Remove BMR codes
      .replace(/\s*\*?DT\s*[0-9/]*\s*$/i, '')     // Remove DT codes
      .replace(/\s*\*?ALL\s*$/i, '')              // Remove ALL code
      .replace(/\s*\*?RWBH?\s*$/i, '')            // Remove RWBH codes
      .replace(/\s+[A-Z]{1,4}\s*$/i, '')          // Remove trailing 1-4 letter codes
      .replace(/\)[\s\*]*[A-Z0-9\s/]+$/i, ')')    // Remove anything after closing paren
      .trim();
    
    // If still in LASTNAME,(FIRSTNAME) format, convert it
    const stillParenMatch = cleanName.match(/^([A-Z]+),\(([A-Z]+)\)$/i);
    if (stillParenMatch) {
      const lastName = stillParenMatch[1];
      const firstName = stillParenMatch[2];
      cleanName = `${firstName.charAt(0).toUpperCase()}${firstName.slice(1).toLowerCase()} ${lastName.charAt(0).toUpperCase()}${lastName.slice(1).toLowerCase()}`;
    }
  }
  
  return cleanName.trim();
};

// Voice settings cache
let voiceSettings = { enabled: true, volume: 1.0, speed: 0.85 };

// Fetch voice settings from server
const fetchVoiceSettings = async () => {
  try {
    const response = await axios.get(`${API}/voice-settings`);
    voiceSettings = {
      enabled: response.data.voice_enabled,
      volume: response.data.voice_volume,
      speed: response.data.voice_speed || 0.85
    };
  } catch (error) {
    console.error("Failed to fetch voice settings:", error);
  }
};

// Initialize voice settings on load
fetchVoiceSettings();

// Get time period for voice message selection
const getTimePeriod = () => {
  const hour = new Date().getHours();
  if (hour >= 5 && hour < 12) return "morning";
  if (hour >= 12 && hour < 17) return "afternoon";
  if (hour >= 17 && hour < 21) return "evening";
  return "night";
};

// Track current playing audio to prevent overlap
let currentAudio = null;
let audioPlaying = false;

// Stop all audio immediately
const stopAllAudio = () => {
  if (currentAudio) {
    currentAudio.pause();
    currentAudio.currentTime = 0;
    currentAudio.src = '';
    currentAudio = null;
  }
  audioPlaying = false;
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
};

// Audio player for voice messages (works on Fully Kiosk)
const playVoiceMessage = (messageId, onEnd = null) => {
  if (!voiceSettings.enabled) {
    console.log("Voice is disabled");
    if (onEnd) onEnd();
    return;
  }
  
  // Stop any currently playing audio first
  stopAllAudio();
  
  // Small delay to ensure previous audio is fully stopped
  setTimeout(() => {
    const audio = new Audio(`${API}/voice/${messageId}?lang=${currentLanguage}`);
    audio.volume = voiceSettings.volume;
    currentAudio = audio;
    audioPlaying = true;
    
    audio.onended = () => {
      audioPlaying = false;
      currentAudio = null;
      if (onEnd) onEnd();
    };
    
    audio.onerror = () => {
      audioPlaying = false;
      currentAudio = null;
      // Fallback to Web Speech API if audio fails
      if ('speechSynthesis' in window) {
        const messages = currentLanguage === 'es' ? {
          "register_welcome": "Bienvenido a Hodler Inn. Si es su primera vez aquí, por favor registre su número de empleado y nombre.",
          "checkin_welcome_morning": "Buenos días. Bienvenido de nuevo a Hodler Inn.",
          "checkin_welcome_afternoon": "Buenas tardes. Bienvenido de nuevo a Hodler Inn.",
          "checkin_welcome_evening": "Buenas tardes. Bienvenido de nuevo a Hodler Inn.",
          "checkin_welcome_night": "Buenas noches. Bienvenido de nuevo a Hodler Inn.",
          "checkin_complete": "Que descanse bien.",
          "checkout_morning": "Buenos días! Gracias por hospedarse en Hodler Inn. Buen viaje.",
          "checkout_afternoon": "Buenas tardes! Gracias por hospedarse en Hodler Inn. Buen viaje.",
          "checkout_evening": "Buenas tardes! Gracias por hospedarse en Hodler Inn. Buen viaje.",
          "checkout_night": "Buenas noches! Gracias por hospedarse en Hodler Inn. Buen viaje.",
          "signature_reminder": "Por favor firme su nombre completo de forma legible.",
          "room_reminder": "Por favor seleccione el número de habitación de la llave en el escritorio.",
          "checkout_found": "Reserva encontrada. Por favor ingrese su hora de servicio y presione Completar salida."
        } : {
          "register_welcome": "Welcome to Hodler Inn. If you are first time here, please register your employee number and name, then go to check in.",
          "checkin_welcome_morning": "Good morning. Welcome back to Hodler Inn.",
          "checkin_welcome_afternoon": "Good afternoon. Welcome back to Hodler Inn.",
          "checkin_welcome_evening": "Good evening. Welcome back to Hodler Inn.",
          "checkin_welcome_night": "Good night. Welcome back to Hodler Inn.",
          "checkin_complete": "Have a good rest.",
          "checkout_morning": "Good morning! Thank you for staying at Hodler Inn. Have a safe journey.",
          "checkout_afternoon": "Good afternoon! Thank you for staying at Hodler Inn. Have a safe journey.",
          "checkout_evening": "Good evening! Thank you for staying at Hodler Inn. Have a safe journey.",
          "checkout_night": "Good night! Thank you for staying at Hodler Inn. Have a safe journey.",
          "signature_reminder": "Please sign your full name legibly.",
          "room_reminder": "Please select the room number from key on desk.",
          "checkout_found": "Booking found. Please enter your on duty time and press Complete check out."
        };
        const text = messages[messageId];
        if (text) {
          const utterance = new SpeechSynthesisUtterance(text);
          utterance.volume = voiceSettings.volume;
          utterance.rate = voiceSettings.speed || 0.9;
          utterance.lang = currentLanguage === 'es' ? 'es-MX' : 'en-US';
          if (onEnd) utterance.onend = onEnd;
          window.speechSynthesis.speak(utterance);
        }
      }
    };
    
    audio.play().catch(err => {
      console.log("Audio play failed:", err);
      audio.onerror();
    });
  }, 100);
};

// Play personalized welcome with name (using dynamic audio generation)
const playWelcomeWithName = (name, isNewEmployee = false) => {
  if (!voiceSettings.enabled) return;
  
  // Prevent playing if audio is already playing
  if (audioPlaying) {
    console.log("Audio already playing, skipping...");
    return;
  }
  
  // Stop any currently playing audio first
  stopAllAudio();
  
  // Small delay to ensure previous audio is fully stopped
  setTimeout(() => {
    const messageType = isNewEmployee ? "checkin_new" : "checkin";
    const encodedName = encodeURIComponent(name);
    const greeting = encodeURIComponent(getTimeBasedGreeting());
    const audio = new Audio(`${API}/voice-dynamic/${messageType}/${encodedName}?greeting=${greeting}&lang=${currentLanguage}`);
    audio.volume = voiceSettings.volume;
    currentAudio = audio;
    audioPlaying = true;
    
    audio.onended = () => {
      audioPlaying = false;
      currentAudio = null;
    };
    
    audio.onerror = () => {
      audioPlaying = false;
      currentAudio = null;
      // Fallback to Web Speech API
      if ('speechSynthesis' in window) {
        const greetingText = getTimeBasedGreeting();
        const message = currentLanguage === 'es' 
          ? `${greetingText}, ${name}. Bienvenido a Hodler Inn. Por favor ingrese el número de habitación, la hora, firme su nombre y haga clic en Completar Registro.`
          : `${greetingText}, ${name}. Welcome back to Hodler Inn. Please enter room number, time, sign your name, and click Complete Check-In.`;
        const utterance = new SpeechSynthesisUtterance(message);
        utterance.volume = voiceSettings.volume;
        utterance.rate = voiceSettings.speed || 0.85;
        utterance.lang = currentLanguage === 'es' ? 'es-MX' : 'en-US';
        window.speechSynthesis.speak(utterance);
      }
    };
    
    audio.play().catch(err => {
      console.log("Dynamic audio failed, falling back to speech:", err);
      audio.onerror();
    });
  }, 100);
};

// Play checkout found with employee name (using dynamic audio generation)
const playCheckoutFoundWithName = (name) => {
  if (!voiceSettings.enabled) return;
  
  // Prevent playing if audio is already playing
  if (audioPlaying) {
    console.log("Audio already playing, skipping checkout message...");
    return;
  }
  
  // Stop any currently playing audio first
  stopAllAudio();
  
  // Small delay to ensure previous audio is fully stopped
  setTimeout(() => {
    const encodedName = encodeURIComponent(name);
    const audio = new Audio(`${API}/voice-dynamic/checkout_found/${encodedName}?lang=${currentLanguage}`);
    audio.volume = voiceSettings.volume;
    currentAudio = audio;
    audioPlaying = true;
    
    audio.onended = () => {
      audioPlaying = false;
      currentAudio = null;
    };
    
    audio.onerror = () => {
      audioPlaying = false;
      currentAudio = null;
      // Fallback to Web Speech API
      if ('speechSynthesis' in window) {
        const message = currentLanguage === 'es'
          ? `Reserva encontrada para ${name}. Por favor ingrese su hora de servicio y presione Completar salida.`
          : `Booking found for ${name}. Please enter your on duty time and press Complete check out.`;
        const utterance = new SpeechSynthesisUtterance(message);
        utterance.volume = voiceSettings.volume;
        utterance.rate = voiceSettings.speed || 0.85;
        utterance.lang = currentLanguage === 'es' ? 'es-MX' : 'en-US';
        window.speechSynthesis.speak(utterance);
      }
    };
    
    audio.play().catch(err => {
      console.log("Dynamic audio failed, falling back to speech:", err);
      audio.onerror();
    });
  }, 100);
};

// Legacy speakMessage function (now uses audio files)
const speakMessage = (message, rate = null) => {
  // Use speed from settings if rate not explicitly provided
  const speechRate = rate !== null ? rate : voiceSettings.speed;
  
  // Map common messages to pre-generated audio
  const messageMap = {
    "Please sign your full name legibly": "signature_reminder",
    "Please select the room number from key on desk": "room_reminder",
    "Booking found": "checkout_found"
  };
  
  // Check if we have a pre-generated audio for this message
  for (const [key, id] of Object.entries(messageMap)) {
    if (message.includes(key)) {
      playVoiceMessage(id);
      return;
    }
  }
  
  // Fallback to Web Speech API for custom messages
  if (!voiceSettings.enabled) return;
  
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(message);
    utterance.rate = speechRate;
    utterance.volume = voiceSettings.volume;
    utterance.lang = currentLanguage === 'es' ? 'es-MX' : 'en-US';
    window.speechSynthesis.speak(utterance);
  }
};

// Get greeting based on time of day (with language support)
const getTimeBasedGreeting = () => {
  const hour = new Date().getHours();
  if (currentLanguage === 'es') {
    if (hour >= 5 && hour < 12) {
      return "Buenos días";
    } else if (hour >= 12 && hour < 17) {
      return "Buenas tardes";
    } else if (hour >= 17 && hour < 21) {
      return "Buenas tardes";
    } else {
      return "Buenas noches";
    }
  } else {
    if (hour >= 5 && hour < 12) {
      return "Good morning";
    } else if (hour >= 12 && hour < 17) {
      return "Good afternoon";
    } else if (hour >= 17 && hour < 21) {
      return "Good evening";
    } else {
      return "Good night";
    }
  }
};

const pageVariants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 }
};

export default function GuestPortal() {
  const [view, setView] = useState("menu"); // menu, register, checkin, checkout, signin, checkin-success, checkout-success
  const [successMessage, setSuccessMessage] = useState({ title: "", message: "", subMessage: "" });
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [language, setLanguage] = useState(getInitialLanguage());
  const navigate = useNavigate();

  // Get translations for current language
  const t = translations[language];

  // Update module-level language when state changes
  useEffect(() => {
    currentLanguage = language;
    localStorage.setItem('bitsy_language', language);
  }, [language]);

  const toggleLanguage = () => {
    const newLang = language === 'en' ? 'es' : 'en';
    setLanguage(newLang);
  };

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
    <div className="kiosk-container grid-bg min-h-screen relative overflow-y-auto">
      {/* Logo Header - smaller on mobile */}
      <div className="absolute top-3 sm:top-6 left-3 sm:left-6 flex items-center gap-2 sm:gap-3 z-10">
        <img 
          src="https://customer-assets.emergentagent.com/job_guest-hotel-mgmt/artifacts/56yphta2_17721406444867042425090808501904.jpg" 
          alt="Hodler Inn Logo" 
          className="w-8 h-8 sm:w-12 sm:h-12 rounded-lg object-cover"
        />
        <div>
          <h1 className="font-outfit font-bold text-vault-text text-base sm:text-xl tracking-tight">HODLER INN</h1>
          <p className="font-mono text-[8px] sm:text-[10px] text-vault-gold uppercase tracking-widest">Be Responsible to Be Free</p>
        </div>
      </div>

      {/* Top Right Buttons */}
      <div className="absolute top-3 sm:top-6 right-3 sm:right-6 flex items-center gap-2 z-10">
        {/* Language Toggle Button */}
        <button 
          onClick={toggleLanguage}
          className="flex items-center gap-1 sm:gap-2 text-vault-text-secondary hover:text-vault-gold transition-colors bg-vault-surface px-2 sm:px-3 py-1.5 sm:py-2 rounded-lg border border-gray-300 shadow-sm"
          data-testid="language-toggle-btn"
          title={language === 'en' ? 'Cambiar a Español' : 'Switch to English'}
        >
          <Globe className="w-4 h-4" />
          <span className="text-xs sm:text-sm font-mono font-bold">{language === 'en' ? 'EN' : 'ES'}</span>
        </button>
        {/* Fullscreen/Kiosk Mode Button */}
        <button 
          onClick={toggleFullscreen}
          className="flex items-center gap-1 sm:gap-2 text-vault-text-secondary hover:text-vault-gold transition-colors bg-vault-surface px-2 sm:px-3 py-1.5 sm:py-2 rounded-lg border border-gray-300 shadow-sm"
          data-testid="fullscreen-btn"
          title={isFullscreen ? "Exit Kiosk Mode" : "Enter Kiosk Mode"}
        >
          {isFullscreen ? <Minimize className="w-4 h-4" /> : <Maximize className="w-4 h-4" />}
          <span className="text-xs sm:text-sm font-mono hidden sm:inline">{isFullscreen ? "Exit Kiosk" : "Kiosk Mode"}</span>
        </button>
      </div>

      <AnimatePresence mode="wait">
        {view === "menu" && (
          <MainMenu key="menu" setView={setView} t={t} language={language} />
        )}
        {view === "register" && (
          <RegisterForm key="register" setView={setView} t={t} />
        )}
        {view === "checkin" && (
          <CheckInForm key="checkin" setView={setView} setSuccessMessage={setSuccessMessage} t={t} language={language} />
        )}
        {view === "checkout" && (
          <CheckOutForm key="checkout" setView={setView} setSuccessMessage={setSuccessMessage} t={t} language={language} />
        )}
        {view === "signin" && (
          <SignInSheetView key="signin" setView={setView} t={t} />
        )}
        {view === "help" && (
          <HelpView key="help" setView={setView} t={t} />
        )}
        {view === "checkin-success" && (
          <SuccessScreen key="checkin-success" setView={setView} successMessage={successMessage} t={t} />
        )}
        {view === "checkout-success" && (
          <SuccessScreen key="checkout-success" setView={setView} successMessage={successMessage} t={t} />
        )}
      </AnimatePresence>
    </div>
  );
}

function MainMenu({ setView, t, language }) {
  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
      className="w-full max-w-md"
    >
      <Card className="bg-vault-surface border border-vault-border shadow-xl p-8 rounded-2xl" data-testid="main-menu-card">
        <CardHeader className="text-center pb-8">
          <CardTitle className="font-outfit text-3xl font-bold text-vault-text tracking-tight">
            {t.welcomeTitle}
          </CardTitle>
          <p className="text-red-600 font-bold text-lg mt-3">
            {t.railroadCrew}
          </p>
          <p className="text-vault-text-secondary font-manrope mt-2">
            {t.selectOption}
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button
            onClick={() => {
              const timePeriod = getTimePeriod();
              playVoiceMessage(`checkin_welcome_${timePeriod}`);
              setView("checkin");
            }}
            className="w-full h-14 text-lg flex items-center justify-center gap-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold uppercase tracking-wide"
            data-testid="checkin-btn"
          >
            <LogIn className="w-5 h-5" />
            {t.checkIn}
          </Button>
          <Button
            onClick={() => setView("checkout")}
            className="w-full h-14 text-lg flex items-center justify-center gap-3 bg-red-600 hover:bg-red-700 text-white font-bold uppercase tracking-wide"
            data-testid="checkout-btn"
          >
            <LogOut className="w-5 h-5" />
            {t.checkOut}
          </Button>
          <div className="pt-4 border-t border-vault-border space-y-3">
            <Button
              onClick={() => setView("signin")}
              className="w-full h-12 flex items-center justify-center gap-3 bg-gray-100 hover:bg-gray-200 text-gray-700 border border-gray-300"
              data-testid="signin-sheet-btn"
            >
              <ClipboardList className="w-5 h-5" />
              {t.viewSignInSheet}
            </Button>
            <Button
              onClick={() => setView("help")}
              className="w-full h-12 flex items-center justify-center gap-3 bg-blue-600 hover:bg-blue-700 text-white font-bold uppercase tracking-wide"
              data-testid="help-btn"
            >
              <HelpCircle className="w-5 h-5" />
              {t.howToUseHelp}
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function RegisterForm({ setView, t }) {
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
      <Card className="bg-vault-surface border border-vault-border shadow-xl p-8 rounded-2xl" data-testid="register-form-card">
        <CardHeader className="pb-6">
          <button 
            onClick={() => setView("menu")} 
            className="text-gray-500 hover:text-vault-gold transition-colors mb-4 flex items-center gap-2"
            data-testid="back-btn"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
          <CardTitle className="font-outfit text-2xl font-bold text-vault-text tracking-tight flex items-center gap-3">
            <UserPlus className="w-6 h-6 text-amber-500" />
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
              <Hash className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-vault-gold" />
              <Input
                value={employeeNumber}
                onChange={(e) => setEmployeeNumber(e.target.value)}
                placeholder="⬇️ TAP HERE to enter number"
                className="pl-10 vault-input input-highlight text-lg"
                data-testid="employee-number-input"
                autoFocus
              />
            </div>
          </div>
          <div>
            <label className="vault-label">Full Name</label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-vault-gold" />
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="⬇️ TAP HERE to enter name"
                className="pl-10 vault-input text-lg"
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

function CheckInForm({ setView, setSuccessMessage, t, language }) {
  const [employeeNumber, setEmployeeNumber] = useState("");
  const [employeeName, setEmployeeName] = useState("");
  const [roomNumber, setRoomNumber] = useState("");
  const [date, setDate] = useState(new Date());
  const getCurrentTime = () => {
    const now = new Date();
    return `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
  };
  const [time, setTime] = useState(getCurrentTime());
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [employeeStatus, setEmployeeStatus] = useState(null); // 'found', 'not_found', 'new_guest', null
  const [similarNumbers, setSimilarNumbers] = useState([]); // Similar employee numbers when not found
  const [availableRooms, setAvailableRooms] = useState([]);
  const [signatureReminderSpoken, setSignatureReminderSpoken] = useState(false);
  const [requestingAccess, setRequestingAccess] = useState(false);
  const [companyName, setCompanyName] = useState("");
  const [wrongAttempts, setWrongAttempts] = useState(0);
  const sigRef = useRef(null);
  const roomInputRef = useRef(null);
  const signatureContainerRef = useRef(null);

  // Auto-update time every minute
  useEffect(() => {
    const interval = setInterval(() => setTime(getCurrentTime()), 60000);
    return () => clearInterval(interval);
  }, []);

  // Fetch available rooms on mount
  useEffect(() => {
    const fetchRooms = async () => {
      try {
        const response = await axios.get(`${API}/rooms`);
        setAvailableRooms(response.data || []);
      } catch (error) {
        console.error("Failed to fetch rooms:", error);
      }
    };
    fetchRooms();
  }, []);

  // Auto-verify employee when number changes (debounced)
  useEffect(() => {
    // Require at least 5 characters and stop typing for 800ms before verifying
    if (employeeNumber.length < 5) {
      setEmployeeStatus(null);
      setEmployeeName("");
      setSimilarNumbers([]);
      return;
    }

    const verifyEmployee = async () => {
      setVerifying(true);
      setSimilarNumbers([]);
      try {
        // First check if already registered as a guest
        const response = await axios.get(`${API}/guests/${employeeNumber}`);
        const cleanedName = cleanEmployeeName(response.data.name);
        setEmployeeName(cleanedName);  // Display cleaned name
        setEmployeeStatus('found');
        playWelcomeWithName(cleanedName, false);  // Speak cleaned name
        setTimeout(() => roomInputRef.current?.focus(), 300);
      } catch (error) {
        // Check if employee ID is in admin's approved list
        try {
          const empResponse = await axios.get(`${API}/employees/verify/${employeeNumber}`);
          const originalName = empResponse.data.name;  // Keep original for storage
          const cleanedName = cleanEmployeeName(originalName);  // Clean for display/voice
          setEmployeeName(cleanedName);  // Display cleaned name
          
          // Auto-register the employee - STORE ORIGINAL NAME for portal sync
          try {
            await axios.post(`${API}/guests/register`, {
              employee_number: employeeNumber,
              name: originalName  // Store ORIGINAL name to match portal
            });
            // Successfully registered - show full form
            setEmployeeStatus('found');
            playWelcomeWithName(cleanedName, false);  // Speak cleaned name
            setTimeout(() => roomInputRef.current?.focus(), 300);
          } catch (regError) {
            // Registration failed - maybe already registered, still show form
            setEmployeeStatus('found');
            playWelcomeWithName(cleanedName, false);  // Speak cleaned name
            setTimeout(() => roomInputRef.current?.focus(), 300);
          }
        } catch (empError) {
          // Employee not in admin list - BLOCK check-in, show Yellow Card message
          setEmployeeName("");
          setEmployeeStatus('not_found');
          
          // Check for similar numbers in the error response
          const errorDetail = empError.response?.data?.detail;
          if (errorDetail && typeof errorDetail === 'object' && errorDetail.similar_numbers) {
            setSimilarNumbers(errorDetail.similar_numbers);
          }
          
          // Play voice message for unregistered employee
          playVoiceMessage("yellow_card_instructions");
        }
      } finally {
        setVerifying(false);
      }
    };

    // Wait 0.8 seconds after user stops typing before verifying (faster response)
    const timer = setTimeout(verifyEmployee, 800);
    return () => clearTimeout(timer);
  }, [employeeNumber]);

  const handleRequestAccess = async () => {
    if (!employeeName.trim()) {
      toast.error("Please enter your name");
      return;
    }
    setRequestingAccess(true);
    try {
      await axios.post(`${API}/request-employee-access`, {
        employee_number: employeeNumber,
        name: employeeName.trim()
      });
      toast.success("Access request sent! Admin will approve shortly.");
      setEmployeeStatus(null);
      setEmployeeNumber("");
      setEmployeeName("");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to send request. Please contact admin.");
    } finally {
      setRequestingAccess(false);
    }
  };

  const handleContinueAsNewEmployee = async () => {
    if (!employeeName.trim()) {
      toast.error("Please enter your name");
      return;
    }
    if (companyName.trim().toUpperCase() !== "CPKC") {
      const newAttempts = wrongAttempts + 1;
      setWrongAttempts(newAttempts);
      
      if (newAttempts >= 2) {
        toast.error("Invalid company name. Please call Help Phone from outside office.");
        playVoiceMessage("help_phone_message");
      } else {
        toast.error("Invalid company name. Please try again.");
      }
      return;
    }
    setRequestingAccess(true);
    try {
      // Register as pending verification guest
      await axios.post(`${API}/guests/register-pending`, {
        employee_number: employeeNumber,
        name: employeeName.trim()
      });
      
      // Set status to allow check-in form to show
      setEmployeeStatus('found');
      setWrongAttempts(0); // Reset attempts on success
      playWelcomeWithName(employeeName.trim(), true);
      toast.success("Welcome! Please continue with check-in.");
      setTimeout(() => roomInputRef.current?.focus(), 300);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to register. Please try again.");
    } finally {
      setRequestingAccess(false);
    }
  };

  const speakSignatureReminder = () => {
    if (!signatureReminderSpoken) {
      speakMessage("Please sign your full name legibly.");
      setSignatureReminderSpoken(true);
    }
  };

  const clearSignature = () => {
    sigRef.current?.clear();
    setSignatureReminderSpoken(false);
  };

  const handleCheckIn = async () => {
    if (employeeStatus !== 'found') {
      toast.error("Please enter a valid employee number");
      return;
    }
    if (!roomNumber) {
      toast.error("Please enter room number");
      return;
    }
    const validRoom = availableRooms.find(r => r.room_number === roomNumber.trim());
    if (!validRoom) {
      toast.error(`Room ${roomNumber} is not valid. Please check the room number on your key.`);
      return;
    }
    if (!date || !time) {
      toast.error("Please select date and time");
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
      
      setTimeout(() => playVoiceMessage("checkin_complete"), 500);
      
      const greeting = getTimeBasedGreeting();
      setSuccessMessage({
        title: `${greeting}!`,
        message: t.welcomeToHodlerInn,
        subMessage: t.haveGoodRest,
        type: "checkin"
      });
      setView("checkin-success");
      setTimeout(() => setView("menu"), 8000);
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
      className="w-full max-w-md pb-64"
    >
      <Card className="glass-card p-4 sm:p-6" data-testid="checkin-form-card">
        <CardHeader className="pb-3 sm:pb-4">
          <button 
            onClick={() => setView("menu")} 
            className="text-vault-text-secondary hover:text-vault-gold transition-colors mb-2 flex items-center gap-2"
            data-testid="back-btn"
          >
            <ArrowLeft className="w-4 h-4" />
            {t.back}
          </button>
          <CardTitle className="font-outfit text-xl sm:text-2xl font-bold text-vault-text tracking-tight flex items-center gap-3">
            <LogIn className="w-5 h-5 sm:w-6 sm:h-6 text-vault-gold" />
            {t.guestCheckIn}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 sm:space-y-4">
          {/* Employee Number */}
          <div>
            <label className="vault-label text-xs sm:text-sm">{t.employeeNumber}</label>
            <div className="relative">
              <Hash className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 sm:w-5 sm:h-5 text-vault-gold" />
              <Input
                value={employeeNumber}
                onChange={(e) => {
                  // Only allow numeric characters
                  const numericValue = e.target.value.replace(/[^0-9]/g, '');
                  setEmployeeNumber(numericValue);
                }}
                onFocus={(e) => setTimeout(() => e.target.scrollIntoView({ behavior: 'smooth', block: 'center' }), 300)}
                placeholder={t.tapToEnterNumber}
                className="vault-input pl-10 input-highlight text-base sm:text-lg h-11 sm:h-12"
                data-testid="checkin-employee-input"
                autoFocus
                inputMode="numeric"
                pattern="[0-9]*"
                type="tel"
              />
              {verifying && (
                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                  <div className="w-5 h-5 border-2 border-vault-gold border-t-transparent rounded-full animate-spin"></div>
                </div>
              )}
            </div>
          </div>

          {/* Employee Name - Auto-filled when found */}
          <div>
            <label className="vault-label text-xs sm:text-sm">{t.name}</label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 sm:w-5 sm:h-5 text-vault-gold" />
              <Input
                value={employeeName}
                readOnly
                placeholder={t.nameAutoAppear}
                className={cn(
                  "vault-input pl-10 text-base sm:text-lg h-11 sm:h-12",
                  employeeStatus === 'found' && "border-emerald-500 bg-emerald-900/20",
                  employeeStatus === 'new_guest' && "border-amber-500 bg-amber-900/20",
                  employeeStatus === 'not_found' && "border-red-500 bg-red-900/20"
                )}
                data-testid="checkin-name-input"
              />
            </div>
            {/* Status Messages */}
            {employeeStatus === 'found' && (
              <p className="text-emerald-400 text-sm mt-1 flex items-center gap-1">
                <span>✓</span> {t.welcome}
              </p>
            )}
            {employeeStatus === 'not_found' && (
              <motion.div 
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className="mt-2 bg-amber-900/30 border border-amber-600/50 rounded-lg p-4 space-y-3"
              >
                <div className="text-center">
                  <p className="text-amber-400 text-lg font-bold mb-2">
                    ⚠️ {t.employeeIdNotFound}
                  </p>
                  <p className="text-amber-300 text-sm">
                    {t.notInSystem}
                  </p>
                </div>
                
                {/* Similar Numbers Suggestion */}
                {similarNumbers.length > 0 && (
                  <div className="bg-blue-900/40 border border-blue-500/50 rounded-lg p-3">
                    <p className="text-blue-400 text-sm font-medium mb-2">
                      {t.didYouMean}
                    </p>
                    <div className="space-y-2">
                      {similarNumbers.map((emp, idx) => (
                        <button
                          key={idx}
                          onClick={() => {
                            setEmployeeNumber(emp.employee_number);
                            setEmployeeStatus(null);
                            setSimilarNumbers([]);
                          }}
                          className="w-full text-left p-2 bg-blue-800/30 hover:bg-blue-700/40 rounded border border-blue-500/30 transition-colors"
                          data-testid={`similar-number-${idx}`}
                        >
                          <span className="text-blue-300 font-mono font-bold">{emp.employee_number}</span>
                          {emp.name && (
                            <span className="text-blue-400 text-sm ml-2">- {emp.name}</span>
                          )}
                        </button>
                      ))}
                    </div>
                    <p className="text-blue-300 text-xs mt-2">
                      {t.tapCorrectNumber}
                    </p>
                  </div>
                )}
                
                {/* Yellow Card Instructions */}
                <div className="bg-yellow-900/50 border-2 border-yellow-500 rounded-lg p-4">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="bg-yellow-500 w-8 h-8 rounded flex items-center justify-center">
                      <span className="text-black text-lg">📝</span>
                    </div>
                    <p className="text-yellow-400 font-bold text-base">
                      {t.pleaseUseYellowCard}
                    </p>
                  </div>
                  <p className="text-yellow-300 text-sm">
                    {t.yellowCardInstructions}
                  </p>
                  <p className="text-yellow-300 text-sm mt-1">
                    {t.adminWillAdd}
                  </p>
                </div>
                
                <p className="text-vault-text-secondary text-xs text-center">
                  {t.ifError}
                </p>
              </motion.div>
            )}
          </div>

          {/* Only show rest of form when employee is found/registered */}
          {employeeStatus === 'found' && (
            <>
              {/* Room Number */}
              <div>
                <label className="vault-label text-xs sm:text-sm">{t.roomNumber}</label>
                <div className="relative">
                  <DoorOpen className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 sm:w-5 sm:h-5 text-vault-gold" />
                  <Input
                    ref={roomInputRef}
                    value={roomNumber}
                    onChange={(e) => setRoomNumber(e.target.value)}
                    onFocus={(e) => setTimeout(() => e.target.scrollIntoView({ behavior: 'smooth', block: 'center' }), 300)}
                    placeholder={t.tapToEnterRoom}
                    className="vault-input pl-10 input-highlight text-base sm:text-lg h-11 sm:h-12"
                    data-testid="checkin-room-input"
                  />
                </div>
              </div>

              {/* Date and Time in row on tablet */}
              <div className="grid grid-cols-2 gap-3">
                {/* Date */}
                <div>
                  <label className="vault-label text-xs sm:text-sm">{t.date}</label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        className={cn(
                          "w-full vault-input justify-start text-left font-normal h-11 sm:h-12 text-sm sm:text-base",
                          !date && "text-muted-foreground"
                        )}
                        data-testid="checkin-date-btn"
                      >
                        <CalendarIcon className="mr-1 sm:mr-2 h-4 w-4 text-vault-text-secondary" />
                        {date ? format(date, "dd MMM") : t.date}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0 bg-vault-surface border-vault-border" align="start">
                      <Calendar
                        mode="single"
                        selected={date}
                        onSelect={setDate}
                        initialFocus
                        className="bg-vault-surface text-vault-text"
                      />
                    </PopoverContent>
                  </Popover>
                </div>

                {/* Time */}
                <div>
                  <label className="vault-label text-xs sm:text-sm">{t.time}</label>
                  <div className="relative">
                    <Clock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-vault-text-secondary" />
                    <Input
                      type="time"
                      value={time}
                      onChange={(e) => setTime(e.target.value)}
                      onFocus={(e) => setTimeout(() => e.target.scrollIntoView({ behavior: 'smooth', block: 'center' }), 300)}
                      className="vault-input pl-10 h-11 sm:h-12 text-sm sm:text-base"
                      data-testid="checkin-time-input"
                    />
                  </div>
                </div>
              </div>

              {/* Signature */}
              <div ref={signatureContainerRef}>
                <div className="flex justify-between items-center mb-2">
                  <label className="vault-label text-xs sm:text-sm mb-0">{t.signature}</label>
                  <button 
                    onClick={clearSignature}
                    className="text-vault-text-secondary hover:text-vault-gold text-xs flex items-center gap-1"
                    data-testid="clear-checkin-signature-btn"
                  >
                    <Eraser className="w-3 h-3" />
                    {t.clear}
                  </button>
                </div>
                <div 
                  className="bg-white border-2 border-amber-500 rounded-lg"
                  onClick={() => signatureContainerRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })}
                >
                  <SignatureCanvas
                    ref={sigRef}
                    onBegin={() => {
                      speakSignatureReminder();
                      setTimeout(() => signatureContainerRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' }), 100);
                    }}
                    canvasProps={{
                      className: "signature-canvas w-full",
                      style: { width: "100%", height: "150px", touchAction: "none", backgroundColor: "white" }
                    }}
                    penColor="#000000"
                    backgroundColor="white"
                    minWidth={3}
                    maxWidth={6}
                  />
                </div>
              </div>

              {/* Submit */}
              <Button
                onClick={handleCheckIn}
                disabled={loading}
                className="w-full vault-btn-primary h-12 sm:h-14 text-base sm:text-lg font-bold"
                data-testid="submit-checkin-btn"
              >
                {loading ? t.processing : t.completeCheckIn}
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

function CheckOutForm({ setView, setSuccessMessage, t, language }) {
  const [roomNumber, setRoomNumber] = useState("");
  const [employeeNumber, setEmployeeNumber] = useState("");
  const [date, setDate] = useState(new Date());
  const [time, setTime] = useState(""); // Manual entry for checkout time
  const [loading, setLoading] = useState(false);
  const [availableRooms, setAvailableRooms] = useState([]);
  const [loadingRooms, setLoadingRooms] = useState(true);
  const [verifiedBooking, setVerifiedBooking] = useState(null);
  const [verifying, setVerifying] = useState(false);

  // Fetch available rooms on component mount
  useEffect(() => {
    const fetchRooms = async () => {
      try {
        const response = await axios.get(`${API}/rooms`);
        setAvailableRooms(response.data || []);
      } catch (error) {
        console.error("Failed to fetch rooms:", error);
        toast.error("Failed to load room list");
      } finally {
        setLoadingRooms(false);
      }
    };
    fetchRooms();
  }, []);

  const handleVerifyCheckout = async () => {
    if (!roomNumber) {
      toast.error("Please enter room number");
      return;
    }

    setVerifying(true);
    try {
      // Lookup booking by room number - auto-fills employee info
      const response = await axios.get(`${API}/lookup-room/${roomNumber.trim()}`);
      setEmployeeNumber(response.data.employee_number);
      const cleanedName = cleanEmployeeName(response.data.employee_name);
      setVerifiedBooking({...response.data, employee_name: cleanedName});
      toast.success(`Found: ${cleanedName} in Room ${roomNumber}`);
      
      // Voice confirmation with name
      playCheckoutFoundWithName(cleanedName);
    } catch (error) {
      toast.error(error.response?.data?.detail || "No active booking found for this room.");
      setVerifiedBooking(null);
      setEmployeeNumber("");
    } finally {
      setVerifying(false);
    }
  };

  const handleClearVerification = () => {
    setVerifiedBooking(null);
    setRoomNumber("");
    setEmployeeNumber("");
  };

  const handleCheckOut = async () => {
    if (!verifiedBooking) {
      toast.error("Please verify your room and employee number first");
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
        room_number: roomNumber.trim(),
        employee_number: employeeNumber.trim(),
        check_out_date: format(date, "yyyy-MM-dd"),
        check_out_time: time
      });
      
      // Voice message for check-out (using audio files)
      const timePeriod = getTimePeriod();
      setTimeout(() => {
        playVoiceMessage(`checkout_${timePeriod}`);
      }, 500);
      
      // Show success screen
      const greeting = getTimeBasedGreeting();
      setSuccessMessage({
        title: `${greeting}!`,
        message: t.thankYouForStaying,
        subMessage: t.haveSafeJourney,
        keyReminder: t.keyReminder,
        type: "checkout"
      });
      setView("checkout-success");
      
      // Auto-return to menu after 10 seconds
      setTimeout(() => setView("menu"), 10000);
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
            {t.back}
          </button>
          <CardTitle className="font-outfit text-2xl font-bold text-vault-text tracking-tight flex items-center gap-3">
            <LogOut className="w-6 h-6 text-vault-gold" />
            {t.guestCheckOut}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {!verifiedBooking ? (
            <>
              <div>
                <label className="vault-label">{t.roomNumber}</label>
                <div className="relative">
                  <DoorOpen className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-vault-gold" />
                  <Input
                    value={roomNumber}
                    onChange={(e) => setRoomNumber(e.target.value)}
                    placeholder={t.tapToEnterRoom}
                    className="vault-input pl-10 input-highlight text-lg"
                    data-testid="checkout-room-input"
                    autoFocus
                  />
                </div>
              </div>
              <Button
                onClick={handleVerifyCheckout}
                disabled={verifying}
                className="w-full vault-btn-primary h-12"
                data-testid="verify-checkout-btn"
              >
                {verifying ? t.findingBooking : t.findMyBooking}
              </Button>
            </>
          ) : (
            <>
              <div className="bg-emerald-900/30 border border-emerald-600/50 rounded-lg p-4">
                <p className="text-emerald-400 text-xs uppercase tracking-wide mb-1">{t.bookingFound}</p>
                <p className="text-vault-text font-bold text-lg">{verifiedBooking.employee_name}</p>
                <p className="text-vault-text-secondary text-sm">{t.employeeId}: {verifiedBooking.employee_number}</p>
                <p className="text-vault-text-secondary text-sm">{t.room}: {verifiedBooking.room_number}</p>
                <p className="text-vault-text-secondary text-sm">{t.checkedIn}: {verifiedBooking.check_in_date} at {verifiedBooking.check_in_time}</p>
                <button
                  onClick={handleClearVerification}
                  className="text-vault-text-secondary hover:text-vault-gold text-xs underline mt-2"
                >
                  {t.notYourBooking}
                </button>
              </div>
              <div>
                <label className="vault-label">{t.checkOutDate}</label>
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
                      {date ? format(date, "dd MMM yyyy") : t.checkOutDate}
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
                <label className="vault-label">{t.onDutyTime}</label>
                <div className="relative">
                  <Clock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-vault-gold" />
                  <Input
                    type="time"
                    value={time}
                    onChange={(e) => setTime(e.target.value)}
                    className="vault-input pl-10 input-highlight text-lg"
                    placeholder="HH:MM"
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
                {loading ? t.processing : t.completeCheckOut}
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}


function SignInSheetView({ setView, t }) {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [accessCode, setAccessCode] = useState("");
  const [isVerified, setIsVerified] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [showActiveOnly, setShowActiveOnly] = useState(true);  // Default to showing only in-house guests
  const [filterDate, setFilterDate] = useState("");  // Date filter

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
          
          {/* Filter Controls */}
          <div className="mt-4 flex flex-wrap items-center justify-center gap-3 bg-black/30 p-3 rounded-lg border border-vault-border">
            <Filter className="w-4 h-4 text-vault-gold" />
            
            {/* In-House Only Toggle */}
            <label className="text-vault-text-secondary text-sm cursor-pointer flex items-center gap-2">
              <input
                type="checkbox"
                checked={showActiveOnly}
                onChange={(e) => setShowActiveOnly(e.target.checked)}
                className="w-4 h-4 accent-vault-gold cursor-pointer"
                data-testid="guest-show-active-only-toggle"
              />
              <span className={showActiveOnly ? "text-vault-gold font-medium" : ""}>
                In-House Only
              </span>
            </label>
            
            <div className="h-5 w-px bg-vault-border mx-1" />
            
            {/* Date Filter */}
            <DatePicker
              date={filterDate}
              onDateChange={setFilterDate}
              placeholder="Filter by date"
              className="h-8 text-sm"
            />
            {filterDate && (
              <button
                onClick={() => setFilterDate("")}
                className="text-vault-text-secondary hover:text-vault-gold text-sm"
              >
                Clear
              </button>
            )}
          </div>
          
          {/* Summary */}
          <div className="mt-2 text-center text-sm text-vault-text-secondary">
            {showActiveOnly ? (
              <span>Showing <span className="text-vault-gold font-medium">
                {records.filter(r => !r.is_checked_out && (!filterDate || r.check_in_date === filterDate)).length}
              </span> in-house guests</span>
            ) : (
              <span>Showing <span className="text-vault-gold font-medium">
                {records.filter(r => !filterDate || r.check_in_date === filterDate).length}
              </span> total records</span>
            )}
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
                  {(() => {
                    // Apply filters
                    let filteredRecords = records;
                    if (showActiveOnly) {
                      filteredRecords = filteredRecords.filter(r => !r.is_checked_out);
                    }
                    if (filterDate) {
                      filteredRecords = filteredRecords.filter(r => r.check_in_date === filterDate);
                    }
                    
                    if (filteredRecords.length === 0) {
                      return (
                        <TableRow>
                          <TableCell colSpan={11} className="text-center text-vault-text-secondary py-8">
                            {showActiveOnly ? "No in-house guests found" : "No records found"}
                          </TableCell>
                        </TableRow>
                      );
                    }
                    
                    return filteredRecords.map((record, index) => (
                      <TableRow key={record.id} className="table-row border-vault-border">
                        <TableCell className="font-mono text-vault-text">{index + 1}</TableCell>
                        <TableCell className="text-vault-text">Single Stay</TableCell>
                        <TableCell className="text-vault-text font-medium">{cleanEmployeeName(record.employee_name)}</TableCell>
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
                    ));
                  })()}
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

function HelpView({ setView, t }) {
  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
      className="w-full max-w-2xl"
    >
      <Card className="glass-card p-6 md:p-8" data-testid="help-view-card">
        <CardHeader className="pb-4">
          <button 
            onClick={() => setView("menu")} 
            className="text-vault-text-secondary hover:text-vault-gold transition-colors mb-4 flex items-center gap-2"
            data-testid="back-btn"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Menu
          </button>
          <CardTitle className="font-outfit text-2xl font-bold text-vault-text tracking-tight flex items-center gap-3">
            <HelpCircle className="w-6 h-6 text-vault-gold" />
            How to Use Guest Portal
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Video Tutorial */}
          <div className="bg-vault-surface-highlight/50 border-2 border-vault-gold rounded-lg p-4">
            <h3 className="font-outfit text-lg font-bold text-vault-gold mb-3 flex items-center gap-2">
              🎥 Video Tutorial
            </h3>
            <div className="relative w-full" style={{ paddingBottom: '56.25%', height: 0 }}>
              <iframe
                src="https://www.loom.com/embed/b0647a5a59e34f42826cd2a16a5ab233"
                frameBorder="0"
                allowFullScreen
                className="absolute top-0 left-0 w-full h-full rounded-lg"
                data-testid="help-video"
              />
            </div>
            <p className="text-vault-text-secondary text-xs mt-2 text-center">
              Watch how to Check-In and Check-Out
            </p>
          </div>

          {/* Step 1: Check In */}
          <div className="bg-vault-surface-highlight/50 border border-vault-border rounded-lg p-4">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-full bg-emerald-500 flex items-center justify-center flex-shrink-0">
                <span className="text-black font-bold text-lg">1</span>
              </div>
              <div>
                <h3 className="font-outfit text-lg font-bold text-emerald-400 mb-1">CHECK IN</h3>
                <ul className="text-vault-text-secondary text-sm space-y-1">
                  <li>• Tap the <span className="text-emerald-400 font-medium">GREEN "Check In"</span> button</li>
                  <li>• Enter your <span className="text-vault-text">Employee Number</span> — your name appears automatically</li>
                  <li>• <span className="text-amber-400">First time?</span> Tap the orange "Register" button</li>
                  <li>• Enter your assigned <span className="text-vault-text">Room Number</span></li>
                  <li>• Date and time are auto-filled</li>
                  <li>• Sign your name in the <span className="text-vault-text">Signature Box</span></li>
                  <li>• Tap "Complete Check-In"</li>
                </ul>
                <p className="text-vault-gold text-xs mt-2 italic">Everything is on one screen - no extra steps!</p>
              </div>
            </div>
          </div>

          {/* Step 2: Check Out */}
          <div className="bg-vault-surface-highlight/50 border border-vault-border rounded-lg p-4">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-full bg-red-500 flex items-center justify-center flex-shrink-0">
                <span className="text-white font-bold text-lg">2</span>
              </div>
              <div>
                <h3 className="font-outfit text-lg font-bold text-red-400 mb-1">CHECK OUT</h3>
                <ul className="text-vault-text-secondary text-sm space-y-1">
                  <li>• Tap the <span className="text-red-400 font-medium">RED "Check Out"</span> button</li>
                  <li>• Enter your <span className="text-vault-text">Room Number</span></li>
                  <li>• Select <span className="text-vault-text">Check-Out Date</span></li>
                  <li>• Enter <span className="text-vault-text">Check-Out Time</span> (24hr format)</li>
                  <li>• Tap "Complete Check-Out"</li>
                </ul>
                <p className="text-vault-gold text-xs mt-2 italic">No signature needed - your check-in signature is used automatically.</p>
              </div>
            </div>
          </div>

          {/* Not Found? */}
          <div className="bg-red-900/30 border border-red-600/50 rounded-lg p-4">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-full bg-red-600 flex items-center justify-center flex-shrink-0">
                <span className="text-white font-bold text-lg">?</span>
              </div>
              <div>
                <h3 className="font-outfit text-lg font-bold text-red-400 mb-1">EMPLOYEE ID NOT FOUND?</h3>
                <ul className="text-vault-text-secondary text-sm space-y-1">
                  <li>• If your ID is not in the system, tap <span className="text-red-400">"Request Access"</span></li>
                  <li>• Admin will be notified via Telegram</li>
                  <li>• Please wait for admin to add you to the system</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Time Reference */}
          <div className="bg-black/50 border border-vault-gold/30 rounded-lg p-4">
            <h3 className="font-outfit text-sm font-bold text-vault-gold mb-3 text-center">24-HOUR TIME REFERENCE</h3>
            <div className="grid grid-cols-3 gap-2 text-center text-sm">
              <div className="text-vault-text-secondary">6 AM = <span className="text-vault-text">06:00</span></div>
              <div className="text-vault-text-secondary">12 PM = <span className="text-vault-text">12:00</span></div>
              <div className="text-vault-text-secondary">6 PM = <span className="text-vault-text">18:00</span></div>
              <div className="text-vault-text-secondary">8 AM = <span className="text-vault-text">08:00</span></div>
              <div className="text-vault-text-secondary">2 PM = <span className="text-vault-text">14:00</span></div>
              <div className="text-vault-text-secondary">10 PM = <span className="text-vault-text">22:00</span></div>
            </div>
          </div>

          {/* Help Footer */}
          <div className="text-center pt-2">
            <p className="text-vault-text-secondary text-sm">
              Need assistance? Please contact front desk staff.
            </p>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function SuccessScreen({ setView, successMessage, t }) {
  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="w-full max-w-lg text-center"
    >
      <Card className="glass-card p-10" data-testid="success-screen-card">
        <CardContent className="space-y-6">
          {/* Success Icon */}
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
            className="w-24 h-24 mx-auto rounded-full bg-emerald-500/20 border-2 border-emerald-500 flex items-center justify-center"
          >
            <svg className="w-12 h-12 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <motion.path
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ delay: 0.4, duration: 0.5 }}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={3}
                d="M5 13l4 4L19 7"
              />
            </svg>
          </motion.div>

          {/* Title - Time-based greeting */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="font-outfit text-4xl font-bold text-vault-gold"
          >
            {successMessage.title}
          </motion.h1>

          {/* Main Message */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="text-vault-text text-2xl"
          >
            {successMessage.message}
          </motion.p>

          {/* Sub Message */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="text-vault-text-secondary text-xl"
          >
            {successMessage.subMessage}
          </motion.p>

          {/* Key Reminder for Checkout */}
          {successMessage.keyReminder && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7 }}
              className="bg-amber-500/20 border-2 border-amber-500 rounded-lg p-4 mt-6"
            >
              <div className="flex items-center justify-center gap-3">
                <svg className="w-8 h-8 text-amber-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                </svg>
                <p className="text-amber-400 text-lg font-semibold">
                  {successMessage.keyReminder}
                </p>
              </div>
            </motion.div>
          )}

          {/* Return to menu button */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1 }}
          >
            <Button
              onClick={() => setView("menu")}
              className="vault-btn-secondary mt-4"
              data-testid="return-to-menu-btn"
            >
              {t.returnToMenu}
            </Button>
            <p className="text-vault-text-secondary text-sm mt-2">
              {t.autoReturning}
            </p>
          </motion.div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
