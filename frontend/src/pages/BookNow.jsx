import { useState, useRef, useEffect } from "react";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
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
  VolumeX
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
  const [pendingGreeting, setPendingGreeting] = useState(null); // For mobile - needs tap to play
  const scrollRef = useRef(null);
  const inputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const hasPlayedGreeting = useRef(false);
  const isRecordingRef = useRef(false);
  const userHasInteracted = useRef(false);

  // Detect if mobile device
  const isMobile = () => {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
  };

  // Speak text using Web Speech API
  const speakText = (text, isGreeting = false) => {
    if (!voiceEnabled || !('speechSynthesis' in window)) return;
    
    // On mobile, if user hasn't interacted yet and this is the greeting, save it for later
    if (isMobile() && isGreeting && !userHasInteracted.current) {
      setPendingGreeting(text);
      return;
    }
    
    // Stop any currently playing
    stopSpeaking();
    
    // Clean text for speech
    const cleanText = text.replace(/[🏨⚠️•\n\*]/g, ' ').replace(/\$/g, ' dollars ').replace(/\s+/g, ' ').trim();
    
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 0.95;
    utterance.pitch = 1.0;
    utterance.volume = 0.9;
    
    // Try to get a good voice
    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = voices.find(v => 
      v.name.toLowerCase().includes('samantha') ||
      v.name.toLowerCase().includes('google us english') ||
      v.name.toLowerCase().includes('microsoft zira') ||
      v.lang === 'en-US'
    );
    if (preferredVoice) {
      utterance.voice = preferredVoice;
    }
    
    setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = (e) => {
      console.log('Speech error:', e);
      setIsSpeaking(false);
    };
    
    // On mobile, resume speechSynthesis in case it's paused
    if (isMobile()) {
      window.speechSynthesis.cancel(); // Clear any stuck utterances
      setTimeout(() => {
        window.speechSynthesis.speak(utterance);
      }, 100);
    } else {
      window.speechSynthesis.speak(utterance);
    }
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
        
        // Get pricing info
        const singleRate = res.data.single_rate || 79;
        const doubleRate = res.data.double_rate || 89;
        const taxRate = res.data.tax_rate || 0;
        
        // Simple greeting without rate info (rates shown in card below)
        let welcomeMsg = `Hi there! I'm Bitsy, your hotel concierge at Hodler Inn. How may I help you today?\n\nJust let me know when you'd like to stay, or if you've been here before, share your phone number and I'll look up your info!`;
        
        if (res.data.is_sold_out) {
          welcomeMsg = `Hi there! I'm Bitsy, your hotel concierge at Hodler Inn.\n\nUnfortunately, we're currently fully booked online. Please call us at (918) 653-7801 to check availability.`;
        }
        
        setMessages([{ role: "assistant", content: welcomeMsg }]);
        
        // Play voice greeting using Web Speech API (autoplays on desktop, needs tap on mobile)
        if (!hasPlayedGreeting.current) {
          hasPlayedGreeting.current = true;
          setTimeout(() => {
            const greeting = res.data.is_sold_out 
              ? "Hi there! I'm Bitsy, your hotel concierge at Hodler Inn. Unfortunately, we're currently fully booked online. Please call us to check availability."
              : "Hi there! I'm Bitsy, your hotel concierge at Hodler Inn. How may I help you today?";
            speakText(greeting, true); // true = isGreeting
          }, 500);
        }
      } catch (error) {
        const defaultMsg = "Hi there! I'm Bitsy, your hotel concierge at Hodler Inn. How may I help you today?\n\nJust let me know when you'd like to stay!";
        setMessages([{ role: "assistant", content: defaultMsg }]);
        
        // Play default greeting
        if (!hasPlayedGreeting.current) {
          hasPlayedGreeting.current = true;
          setTimeout(() => {
            speakText("Hi there! I'm Bitsy, your hotel concierge at Hodler Inn. How may I help you today?", true);
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

  // Handle first user interaction on mobile - play pending greeting
  const handleUserInteraction = () => {
    if (!userHasInteracted.current) {
      userHasInteracted.current = true;
      if (pendingGreeting) {
        speakText(pendingGreeting, false); // Now safe to play
        setPendingGreeting(null);
      }
    }
  };

  // Play pending greeting when user taps the button
  const playPendingGreeting = () => {
    userHasInteracted.current = true;
    if (pendingGreeting) {
      speakText(pendingGreeting, false);
      setPendingGreeting(null);
    }
  };

  // Auto scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;
    
    // Mark user as having interacted
    handleUserInteraction();

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
              <p className="text-gray-400 text-xs">$79 + tax</p>
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
              {/* Tap to hear greeting button for mobile */}
              {pendingGreeting && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="flex justify-center"
                >
                  <button
                    onClick={playPendingGreeting}
                    className="flex items-center gap-2 bg-gradient-to-r from-amber-500 to-amber-600 text-black px-4 py-2 rounded-full text-sm font-medium hover:from-amber-400 hover:to-amber-500 transition-all shadow-lg"
                  >
                    <Volume2 className="w-4 h-4" />
                    <span>Tap to hear Bitsy</span>
                  </button>
                </motion.div>
              )}
              
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

              {/* Rate Card - shown in chat after greeting */}
              {messages.length > 0 && messages[0].role === "assistant" && availability && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex gap-3"
                >
                  <div className="w-8 h-8 flex-shrink-0"></div>
                  <div className="bg-gradient-to-br from-slate-800/90 to-slate-900/90 border border-amber-500/30 rounded-xl p-4 max-w-[90%]">
                    <h4 className="text-amber-400 font-semibold text-center text-sm mb-3">Room Rates</h4>
                    <div className="grid grid-cols-2 gap-2">
                      <div className="bg-black/40 rounded-lg p-2 text-center">
                        <p className="text-gray-400 text-xs">Single Bed</p>
                        <p className="text-white font-bold">${availability.single_rate || 79}</p>
                        {(availability.tax_rate || 0) > 0 && (
                          <>
                            <p className="text-gray-500 text-xs">+ ${((availability.single_rate || 79) * (availability.tax_rate / 100)).toFixed(2)} tax</p>
                            <p className="text-amber-400 font-semibold text-xs">
                              Total: ${((availability.single_rate || 79) * (1 + availability.tax_rate / 100)).toFixed(2)}/night
                            </p>
                          </>
                        )}
                      </div>
                      <div className="bg-black/40 rounded-lg p-2 text-center">
                        <p className="text-gray-400 text-xs">Double Bed</p>
                        <p className="text-white font-bold">${availability.double_rate || 89}</p>
                        {(availability.tax_rate || 0) > 0 && (
                          <>
                            <p className="text-gray-500 text-xs">+ ${((availability.double_rate || 89) * (availability.tax_rate / 100)).toFixed(2)} tax</p>
                            <p className="text-amber-400 font-semibold text-xs">
                              Total: ${((availability.double_rate || 89) * (1 + availability.tax_rate / 100)).toFixed(2)}/night
                            </p>
                          </>
                        )}
                      </div>
                    </div>
                    <div className="mt-2 pt-2 border-t border-slate-700/50 flex justify-center gap-3 text-xs text-gray-500">
                      <span>Check-in: 3 PM</span>
                      <span>•</span>
                      <span>Check-out: 11 AM</span>
                    </div>
                  </div>
                </motion.div>
              )}

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
            {/* Regular Chat Input - always show */}
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
                placeholder={isRecording ? "Listening..." : "Type your message or tap mic to speak..."}
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
            <p className="text-center text-gray-500 text-xs mt-3">
              By making a reservation, you agree to confirm by calling (918) 653-7801
            </p>
            
            {/* Policy Notice - visible in chat */}
            <div className="flex items-center justify-center gap-4 mt-3 py-2 px-3 bg-red-500/10 border border-red-500/20 rounded-lg">
              <div className="flex items-center gap-1.5">
                <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 text-red-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>
                </svg>
                <span className="text-red-400 text-xs font-bold">100% Non-Smoking</span>
              </div>
              <div className="flex items-center gap-1.5">
                <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 text-red-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>
                </svg>
                <span className="text-red-400 text-xs font-bold">No Pets</span>
              </div>
            </div>
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

        {/* Contact */}
        <div className="mt-6 text-center">
          <a href="tel:9186537801" className="inline-flex items-center gap-2 text-amber-400 hover:text-amber-300 transition-colors">
            <Phone className="w-4 h-4" />
            <span>(918) 653-7801</span>
          </a>
        </div>
      </div>

      {/* Footer */}
      <footer className="mt-8 py-6 bg-slate-900/50 border-t border-slate-800">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row items-center justify-center gap-4">
            <div className="flex items-center gap-3">
              <MapPin className="w-4 h-4 text-amber-500/60" />
              <span className="text-gray-500 text-sm">820 US-59, Heavener, OK 74937</span>
            </div>
            <span className="text-gray-600 hidden md:inline">•</span>
            <p className="text-gray-600 text-xs">
              © {new Date().getFullYear()} Hodler Inn
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
