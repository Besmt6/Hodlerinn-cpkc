import { useState, useRef, useEffect } from "react";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  Send, 
  MessageCircle, 
  User, 
  Bot, 
  CheckCircle, 
  Phone, 
  MapPin, 
  Clock,
  Loader2,
  Home,
  Calendar,
  Mail,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  UserPlus
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Track current audio to prevent overlap
let currentAudio = null;

export default function BookNow() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [sessionId, setSessionId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [bookingConfirmed, setBookingConfirmed] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [availability, setAvailability] = useState(null);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [showPhonePrompt, setShowPhonePrompt] = useState(true);
  const [phoneNumber, setPhoneNumber] = useState("");
  const [returningGuest, setReturningGuest] = useState(null);
  const scrollRef = useRef(null);
  const inputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const hasPlayedGreeting = useRef(false);
  const isRecordingRef = useRef(false); // Track recording state for closure

  // Text-to-Speech function using Web Speech API
  const speakText = (text) => {
    if (!voiceEnabled || !('speechSynthesis' in window)) return;
    
    // Stop any currently playing audio
    if (currentAudio) {
      currentAudio.pause();
      currentAudio = null;
    }
    window.speechSynthesis.cancel();
    
    // Clean text for speech (remove emojis and special chars)
    const cleanText = text.replace(/[🏨⚠️•\n]/g, ' ').replace(/\$/g, ' dollars ').replace(/\s+/g, ' ').trim();
    
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 0.95;
    utterance.pitch = 1.1;
    utterance.volume = 0.9;
    
    // Try to use a female voice
    const voices = window.speechSynthesis.getVoices();
    const femaleVoice = voices.find(v => 
      v.name.toLowerCase().includes('female') || 
      v.name.toLowerCase().includes('samantha') ||
      v.name.toLowerCase().includes('victoria') ||
      v.name.toLowerCase().includes('karen') ||
      v.name.toLowerCase().includes('google us english')
    );
    if (femaleVoice) {
      utterance.voice = femaleVoice;
    }
    
    setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    
    window.speechSynthesis.speak(utterance);
  };

  // Stop speaking
  const stopSpeaking = () => {
    if (currentAudio) {
      currentAudio.pause();
      currentAudio = null;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setIsSpeaking(false);
  };

  // Fetch availability and play voice greeting on load
  useEffect(() => {
    const fetchAvailability = async () => {
      try {
        const res = await axios.get(`${API}/chatbot/availability`);
        setAvailability(res.data);
        
        // Initial greeting asks for phone to identify returning guests
        let welcomeMsg = `Hi there! I'm Bitsy, your hotel concierge at Hodler Inn.\n\nTo give you the best service, please enter your phone number below so I can check if you've stayed with us before.`;
        
        if (res.data.is_sold_out) {
          welcomeMsg = `Hi there! I'm Bitsy, your hotel concierge at Hodler Inn.\n\nUnfortunately, we're currently fully booked online. Please call us at (918) 653-7801 to check availability.`;
          setShowPhonePrompt(false);
        }
        
        setMessages([{ role: "assistant", content: welcomeMsg }]);
        
        // Play voice greeting after a short delay (only once)
        if (!hasPlayedGreeting.current) {
          hasPlayedGreeting.current = true;
          setTimeout(() => {
            const voiceGreeting = res.data.is_sold_out 
              ? "Hi there! I'm Bitsy, your hotel concierge at Hodler Inn. Unfortunately, we're currently fully booked online. Please call us to check availability."
              : "Hi there! I'm Bitsy, your hotel concierge at Hodler Inn. Please enter your phone number so I can check if you've stayed with us before.";
            speakText(voiceGreeting);
          }, 500);
        }
      } catch (error) {
        const defaultMsg = "Hi there! I'm Bitsy, your hotel concierge at Hodler Inn.\n\nPlease enter your phone number below so I can check if you've stayed with us before.";
        setMessages([{ role: "assistant", content: defaultMsg }]);
        
        // Play default greeting
        if (!hasPlayedGreeting.current) {
          hasPlayedGreeting.current = true;
          setTimeout(() => {
            speakText("Hi there! I'm Bitsy, your hotel concierge at Hodler Inn. Please enter your phone number so I can check if you've stayed with us before.");
          }, 500);
        }
      }
    };
    
    // Load voices first (they may not be available immediately)
    if ('speechSynthesis' in window) {
      window.speechSynthesis.getVoices();
      window.speechSynthesis.onvoiceschanged = () => {
        window.speechSynthesis.getVoices();
      };
    }
    
    fetchAvailability();
    
    // Cleanup on unmount
    return () => {
      stopSpeaking();
    };
  }, []);

  // Handle phone number lookup
  const handlePhoneLookup = async () => {
    if (!phoneNumber.trim()) {
      toast.error("Please enter your phone number");
      return;
    }
    
    setIsLoading(true);
    setShowPhonePrompt(false);
    
    // Add user's phone as a message
    setMessages(prev => [...prev, { role: "user", content: phoneNumber }]);
    
    try {
      // Check if this is a returning guest
      const lookupRes = await axios.post(`${API}/chatbot/lookup-guest`, { phone: phoneNumber });
      
      if (lookupRes.data.found) {
        // Returning guest found!
        const guest = lookupRes.data.guest;
        setReturningGuest(guest);
        
        const welcomeBackMsg = `Welcome back, ${guest.guest_name}! Great to see you again.\n\nI have your info on file:\n• Email: ${guest.email}\n• Phone: ${guest.phone}\n• Last room preference: ${(guest.room_type || 'standard').charAt(0).toUpperCase() + (guest.room_type || 'standard').slice(1)}\n\nWhen would you like to stay with us this time?`;
        
        setMessages(prev => [...prev, { role: "assistant", content: welcomeBackMsg }]);
        
        if (voiceEnabled) {
          speakText(`Welcome back, ${guest.guest_name}! Great to see you again. When would you like to stay with us this time?`);
        }
        
        // Start a session with the returning guest info
        const sessionRes = await axios.post(`${API}/chatbot/message`, {
          message: `[SYSTEM: Returning guest identified - Name: ${guest.guest_name}, Email: ${guest.email}, Phone: ${guest.phone}, Preferred room: ${guest.room_type || 'standard'}. Welcome them back and only ask for dates and room preference.]`,
          session_id: null
        });
        setSessionId(sessionRes.data.session_id);
        
      } else {
        // New guest
        const singleRate = availability?.single_rate || 85;
        const doubleRate = availability?.double_rate || 95;
        const taxRate = availability?.tax_rate || 0;
        const taxInfo = taxRate > 0 ? ` (plus ${taxRate}% tax)` : "";
        
        const newGuestMsg = `Nice to meet you! Looks like this is your first time booking with us.\n\nWe offer comfortable rooms at great rates:\n• Single Bed - $${singleRate}/night\n• Double Bed - $${doubleRate}/night${taxInfo}\n\nWhen would you like to stay with us?`;
        
        setMessages(prev => [...prev, { role: "assistant", content: newGuestMsg }]);
        
        if (voiceEnabled) {
          speakText("Nice to meet you! Looks like this is your first time with us. When would you like to stay?");
        }
        
        // Start a new session
        const sessionRes = await axios.post(`${API}/chatbot/message`, {
          message: `[SYSTEM: New guest with phone ${phoneNumber}. Proceed with normal booking flow - collect name, email, dates, room preference.]`,
          session_id: null
        });
        setSessionId(sessionRes.data.session_id);
      }
    } catch (error) {
      console.error("Lookup error:", error);
      // Fall back to regular flow
      const singleRate = availability?.single_rate || 85;
      const doubleRate = availability?.double_rate || 95;
      
      const fallbackMsg = `Thanks! Let me help you book a room.\n\nWe offer:\n• Single Bed - $${singleRate}/night\n• Double Bed - $${doubleRate}/night\n\nWhen would you like to stay with us?`;
      
      setMessages(prev => [...prev, { role: "assistant", content: fallbackMsg }]);
      
      if (voiceEnabled) {
        speakText("Thanks! When would you like to stay with us?");
      }
    }
    
    setIsLoading(false);
  };

  // Skip phone lookup for new guests
  const handleSkipPhoneLookup = async () => {
    setShowPhonePrompt(false);
    setIsLoading(true);
    
    setMessages(prev => [...prev, { role: "user", content: "I'm a new guest" }]);
    
    const singleRate = availability?.single_rate || 85;
    const doubleRate = availability?.double_rate || 95;
    const taxRate = availability?.tax_rate || 0;
    const taxInfo = taxRate > 0 ? ` (plus ${taxRate}% tax)` : "";
    
    const newGuestMsg = `Welcome to Hodler Inn! I'd be happy to help you book a room.\n\nWe offer comfortable rooms at great rates:\n• Single Bed - $${singleRate}/night\n• Double Bed - $${doubleRate}/night${taxInfo}\n\nWhen would you like to stay with us?`;
    
    setMessages(prev => [...prev, { role: "assistant", content: newGuestMsg }]);
    
    if (voiceEnabled) {
      speakText("Welcome to Hodler Inn! When would you like to stay with us?");
    }
    
    setIsLoading(false);
  };

  // Auto scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = inputValue.trim();
    setInputValue("");
    
    // Add user message to chat
    setMessages(prev => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await axios.post(`${API}/chatbot/message`, {
        message: userMessage,
        session_id: sessionId
      });

      setSessionId(response.data.session_id);
      
      // Add assistant response
      setMessages(prev => [...prev, { 
        role: "assistant", 
        content: response.data.response 
      }]);

      // Speak the response
      if (voiceEnabled) {
        speakText(response.data.response);
      }

      // Check if booking was created
      if (response.data.booking_created && response.data.booking_details) {
        setBookingConfirmed(response.data.booking_details);
      }

    } catch (error) {
      console.error("Chat error:", error);
      const errorMsg = "I apologize, but I'm having trouble processing your request. Please try again or call us directly at (918) 653-7801.";
      setMessages(prev => [...prev, { 
        role: "assistant", 
        content: errorMsg 
      }]);
      if (voiceEnabled) {
        speakText(errorMsg);
      }
    }

    setIsLoading(false);
    inputRef.current?.focus();
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Voice recording with automatic silence detection
  const silenceTimeoutRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const streamRef = useRef(null);

  const startRecording = async () => {
    try {
      // Stop any currently playing speech
      stopSpeaking();
      
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      // Set up audio analysis for silence detection
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      analyserRef.current = audioContextRef.current.createAnalyser();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyserRef.current);
      analyserRef.current.fftSize = 512;
      
      const bufferLength = analyserRef.current.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      
      let silenceStart = null;
      const SILENCE_THRESHOLD = 15; // Audio level below this is considered silence
      const SILENCE_DURATION = 1500; // Stop after 1.5 seconds of silence
      
      // Monitor for silence
      const checkSilence = () => {
        if (!isRecordingRef.current || !analyserRef.current) return;
        
        analyserRef.current.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((a, b) => a + b, 0) / bufferLength;
        
        if (average < SILENCE_THRESHOLD) {
          if (!silenceStart) {
            silenceStart = Date.now();
          } else if (Date.now() - silenceStart > SILENCE_DURATION) {
            // Silence detected for long enough, stop recording
            stopRecording();
            return;
          }
        } else {
          silenceStart = null; // Reset if sound detected
        }
        
        silenceTimeoutRef.current = requestAnimationFrame(checkSilence);
      };

      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorderRef.current.onstop = async () => {
        // Clean up silence detection
        if (silenceTimeoutRef.current) {
          cancelAnimationFrame(silenceTimeoutRef.current);
        }
        if (audioContextRef.current) {
          audioContextRef.current.close();
        }
        
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        stream.getTracks().forEach(track => track.stop());
        await transcribeAudio(audioBlob);
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      isRecordingRef.current = true;
      
      // Start silence detection after a brief delay (to allow user to start speaking)
      setTimeout(() => {
        checkSilence();
      }, 1000);
      
    } catch (error) {
      console.error("Microphone access denied:", error);
      alert("Please allow microphone access to use voice input.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecordingRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      isRecordingRef.current = false;
      
      // Clean up
      if (silenceTimeoutRef.current) {
        cancelAnimationFrame(silenceTimeoutRef.current);
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    }
  };

  const transcribeAudio = async (audioBlob) => {
    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'recording.webm');
      
      const response = await axios.post(`${API}/chatbot/transcribe`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      if (response.data.transcript) {
        setInputValue(response.data.transcript);
        // Auto-send the transcribed message
        const userMessage = response.data.transcript;
        setInputValue("");
        setMessages(prev => [...prev, { role: "user", content: userMessage }]);
        
        // Send to chatbot
        const chatResponse = await axios.post(`${API}/chatbot/message`, {
          message: userMessage,
          session_id: sessionId
        });
        
        setSessionId(chatResponse.data.session_id);
        setMessages(prev => [...prev, { 
          role: "assistant", 
          content: chatResponse.data.response 
        }]);
        
        if (chatResponse.data.booking_created && chatResponse.data.booking_details) {
          setBookingConfirmed(chatResponse.data.booking_details);
        }
      }
    } catch (error) {
      console.error("Transcription error:", error);
      setMessages(prev => [...prev, { 
        role: "assistant", 
        content: "I couldn't understand that. Please try again or type your message." 
      }]);
    }
    setIsLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Header */}
      <header className="bg-black/40 backdrop-blur-md border-b border-amber-500/20 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <a 
            href="/" 
            className="flex items-center gap-3"
          >
            <div className="w-10 h-10 bg-gradient-to-br from-amber-400 to-amber-600 rounded-full flex items-center justify-center">
              <Home className="w-5 h-5 text-black" />
            </div>
            <div>
              <h1 className="font-bold text-xl text-white">Hodler Inn</h1>
              <p className="text-xs text-amber-400/80">Heavener, Oklahoma</p>
            </div>
          </a>
          <a 
            href="tel:9186537801" 
            className="flex items-center gap-2 bg-amber-500 hover:bg-amber-400 text-black px-4 py-2 rounded-full font-semibold transition-colors"
          >
            <Phone className="w-4 h-4" />
            <span className="hidden sm:inline">(918) 653-7801</span>
          </a>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-black/30 backdrop-blur border border-amber-500/20 rounded-xl p-4 flex items-center gap-3">
            <div className="w-10 h-10 bg-amber-500/20 rounded-full flex items-center justify-center">
              <MapPin className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <p className="text-white font-medium text-sm">Location</p>
              <p className="text-gray-400 text-xs">820 US-59, Heavener</p>
            </div>
          </div>
          <div className="bg-black/30 backdrop-blur border border-amber-500/20 rounded-xl p-4 flex items-center gap-3">
            <div className="w-10 h-10 bg-amber-500/20 rounded-full flex items-center justify-center">
              <Clock className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <p className="text-white font-medium text-sm">Check-in / Out</p>
              <p className="text-gray-400 text-xs">3:00 PM / 11:00 AM</p>
            </div>
          </div>
          <div className="bg-black/30 backdrop-blur border border-amber-500/20 rounded-xl p-4 flex items-center gap-3">
            <div className="w-10 h-10 bg-amber-500/20 rounded-full flex items-center justify-center">
              <Calendar className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <p className="text-white font-medium text-sm">Rates From</p>
              <p className="text-gray-400 text-xs">$85/night</p>
            </div>
          </div>
        </div>

        {/* Chat Container */}
        <div className="bg-black/40 backdrop-blur border border-amber-500/20 rounded-2xl overflow-hidden shadow-2xl">
          {/* Chat Header */}
          <div className="bg-gradient-to-r from-amber-500/20 to-amber-600/10 border-b border-amber-500/20 px-6 py-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-amber-400 to-amber-600 rounded-full flex items-center justify-center">
                <MessageCircle className="w-6 h-6 text-black" />
              </div>
              <div>
                <h2 className="text-white font-bold text-lg">Chat with Bitsy</h2>
                <p className="text-amber-400/80 text-sm">Your AI booking assistant</p>
              </div>
            </div>
          </div>

          {/* Booking Confirmation Banner */}
          <AnimatePresence>
            {bookingConfirmed && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="bg-emerald-500/20 border-b border-emerald-500/30 px-6 py-4"
              >
                <div className="flex items-start gap-3">
                  <CheckCircle className="w-6 h-6 text-emerald-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-emerald-400 font-semibold">Reservation Request Received!</p>
                    <p className="text-gray-300 text-sm mt-1">
                      Confirmation sent to {bookingConfirmed.email}
                    </p>
                    <div className="mt-2 bg-black/30 rounded-lg p-3 text-sm">
                      <p className="text-white">{bookingConfirmed.guest_name}</p>
                      <p className="text-gray-400">{bookingConfirmed.check_in} → {bookingConfirmed.check_out}</p>
                      <p className="text-amber-400">${bookingConfirmed.total} total ({bookingConfirmed.nights} nights)</p>
                    </div>
                    <div className="mt-3 flex items-center gap-2 text-amber-400 text-sm">
                      <Phone className="w-4 h-4" />
                      <span>Call (918) 653-7801 to confirm</span>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Messages Area */}
          <ScrollArea className="h-[400px] p-4" ref={scrollRef}>
            <div className="space-y-4">
              <AnimatePresence mode="popLayout">
                {messages.map((msg, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    {msg.role === "assistant" && (
                      <div className="w-8 h-8 bg-amber-500/20 rounded-full flex items-center justify-center flex-shrink-0">
                        <Bot className="w-4 h-4 text-amber-400" />
                      </div>
                    )}
                    <div
                      className={`max-w-[80%] px-4 py-3 rounded-2xl ${
                        msg.role === "user"
                          ? "bg-amber-500 text-black rounded-br-md"
                          : "bg-slate-800/80 text-gray-200 rounded-bl-md border border-slate-700/50"
                      }`}
                    >
                      <p className="whitespace-pre-wrap text-sm">{msg.content}</p>
                    </div>
                    {msg.role === "user" && (
                      <div className="w-8 h-8 bg-slate-700 rounded-full flex items-center justify-center flex-shrink-0">
                        <User className="w-4 h-4 text-gray-300" />
                      </div>
                    )}
                  </motion.div>
                ))}
              </AnimatePresence>

              {/* Loading indicator */}
              {isLoading && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex gap-3"
                >
                  <div className="w-8 h-8 bg-amber-500/20 rounded-full flex items-center justify-center">
                    <Bot className="w-4 h-4 text-amber-400" />
                  </div>
                  <div className="bg-slate-800/80 px-4 py-3 rounded-2xl rounded-bl-md border border-slate-700/50">
                    <div className="flex items-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin text-amber-400" />
                      <span className="text-gray-400 text-sm">Typing...</span>
                    </div>
                  </div>
                </motion.div>
              )}
            </div>
          </ScrollArea>

          {/* Input Area */}
          <div className="border-t border-amber-500/20 p-4 bg-black/20">
            {/* Phone Number Prompt */}
            {showPhonePrompt ? (
              <div className="space-y-3">
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-amber-400" />
                    <Input
                      value={phoneNumber}
                      onChange={(e) => setPhoneNumber(e.target.value)}
                      onKeyPress={(e) => e.key === "Enter" && handlePhoneLookup()}
                      placeholder="Enter your phone number..."
                      className="pl-10 bg-slate-800/80 border-slate-700 text-white placeholder:text-gray-500 focus:border-amber-500/50 focus:ring-amber-500/20"
                      disabled={isLoading}
                      data-testid="phone-input"
                      type="tel"
                    />
                  </div>
                  <Button
                    onClick={handlePhoneLookup}
                    disabled={!phoneNumber.trim() || isLoading}
                    className="bg-amber-500 hover:bg-amber-400 text-black px-6"
                    data-testid="phone-lookup-btn"
                  >
                    {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Continue"}
                  </Button>
                </div>
                <Button
                  onClick={handleSkipPhoneLookup}
                  variant="ghost"
                  className="w-full text-gray-400 hover:text-white hover:bg-slate-800/50"
                  disabled={isLoading}
                  data-testid="new-guest-btn"
                >
                  <UserPlus className="w-4 h-4 mr-2" />
                  I'm a new guest
                </Button>
              </div>
            ) : (
              /* Regular Chat Input */
              <div className="flex gap-2">
                <Button
                  onClick={() => {
                    if (isSpeaking) {
                      stopSpeaking();
                    }
                    setVoiceEnabled(!voiceEnabled);
                  }}
                  className={`px-3 transition-all ${
                    voiceEnabled 
                      ? "bg-amber-500/20 hover:bg-amber-500/30 text-amber-400 border border-amber-500/30" 
                      : "bg-slate-800 hover:bg-slate-700 text-gray-500"
                  }`}
                  data-testid="voice-toggle-btn"
                  title={voiceEnabled ? "Voice on - click to mute" : "Voice off - click to enable"}
                >
                  {voiceEnabled ? (
                    isSpeaking ? <Volume2 className="w-4 h-4 animate-pulse" /> : <Volume2 className="w-4 h-4" />
                  ) : (
                    <VolumeX className="w-4 h-4" />
                  )}
                </Button>
                <Input
                  ref={inputRef}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder={isRecording ? "Listening..." : "Type or tap mic to speak..."}
                  className="flex-1 bg-slate-800/80 border-slate-700 text-white placeholder:text-gray-500 focus:border-amber-500/50 focus:ring-amber-500/20"
                  disabled={isLoading || isRecording}
                  data-testid="chat-input"
                />
                <Button
                  onClick={isRecording ? stopRecording : startRecording}
                  disabled={isLoading}
                  className={`px-4 transition-all ${
                    isRecording 
                      ? "bg-red-500 hover:bg-red-400 text-white animate-pulse" 
                      : "bg-slate-700 hover:bg-slate-600 text-gray-300"
                  }`}
                  data-testid="voice-btn"
                  title={isRecording ? "Stop recording" : "Start voice input"}
                >
                  {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                </Button>
                <Button
                  onClick={sendMessage}
                  disabled={!inputValue.trim() || isLoading}
                  className="bg-amber-500 hover:bg-amber-400 text-black px-6"
                  data-testid="chat-send-btn"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            )}
            <p className="text-center text-gray-500 text-xs mt-3">
              By making a reservation, you agree to confirm by calling (918) 653-7801
            </p>
          </div>
        </div>

        {/* Important Notice */}
        <div className="mt-6 bg-amber-500/10 border border-amber-500/30 rounded-xl p-4">
          <div className="flex items-start gap-3">
            <Phone className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-amber-400 font-semibold text-sm">Important Notice</p>
              <p className="text-gray-400 text-sm mt-1">
                Online reservations must be confirmed by calling (918) 653-7801. 
                Unconfirmed reservations will be automatically cancelled 48 hours before arrival.
                Payment is collected at check-in.
              </p>
            </div>
          </div>
        </div>

        {/* Contact Info */}
        <div className="mt-6 text-center">
          <p className="text-gray-500 text-sm">
            Need immediate assistance? Call us at{" "}
            <a href="tel:9186537801" className="text-amber-400 hover:underline">(918) 653-7801</a>
          </p>
        </div>
      </div>

      {/* Footer */}
      <footer className="mt-16 py-8 border-t border-slate-800">
        <div className="container mx-auto px-4 text-center">
          <p className="text-gray-500 text-sm">
            © {new Date().getFullYear()} Hodler Inn. All rights reserved.
          </p>
          <p className="text-gray-600 text-xs mt-2">
            820 US-59, Heavener, OK 74937
          </p>
        </div>
      </footer>
    </div>
  );
}
