import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { Mic, MicOff, Send, Volume2, VolumeX, MessageCircle } from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL;

export default function BitsyEmbed() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [isReady, setIsReady] = useState(false);
  const [conversationId] = useState(() => `embed-${Date.now()}`);
  
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);
  const audioRef = useRef(null);

  // Wake up server on load
  useEffect(() => {
    const wakeServer = async () => {
      try {
        await axios.get(`${API}/api/health`);
        setIsReady(true);
        // Add welcome message
        setMessages([{
          role: "assistant",
          content: "Hi! I'm Bitsy, your AI concierge at Hodler Inn. How can I help you today?"
        }]);
      } catch (e) {
        console.log("Waking up server...");
        setTimeout(wakeServer, 2000);
      }
    };
    wakeServer();
  }, []);

  // Scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Speech recognition setup
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      
      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInputMessage(transcript);
        handleSendMessage(transcript);
      };
      
      recognitionRef.current.onend = () => setIsRecording(false);
      recognitionRef.current.onerror = () => setIsRecording(false);
    }
  }, []);

  const speakText = async (text) => {
    if (!voiceEnabled) return;
    setIsSpeaking(true);
    try {
      const response = await axios.post(`${API}/api/tts`, { text }, { responseType: 'blob' });
      const audioUrl = URL.createObjectURL(response.data);
      audioRef.current = new Audio(audioUrl);
      audioRef.current.onended = () => setIsSpeaking(false);
      audioRef.current.play();
    } catch (e) {
      setIsSpeaking(false);
    }
  };

  const handleSendMessage = async (msg) => {
    const messageToSend = msg || inputMessage;
    if (!messageToSend.trim()) return;
    
    setMessages(prev => [...prev, { role: "user", content: messageToSend }]);
    setInputMessage("");
    setIsLoading(true);
    
    try {
      const response = await axios.post(`${API}/api/chatbot`, {
        message: messageToSend,
        conversation_id: conversationId
      });
      
      const reply = response.data.response || response.data.message;
      setMessages(prev => [...prev, { role: "assistant", content: reply }]);
      speakText(reply);
    } catch (e) {
      setMessages(prev => [...prev, { 
        role: "assistant", 
        content: "Sorry, I'm having trouble right now. Please try again." 
      }]);
    }
    setIsLoading(false);
  };

  const toggleRecording = () => {
    if (isRecording) {
      recognitionRef.current?.stop();
    } else {
      recognitionRef.current?.start();
      setIsRecording(true);
    }
  };

  if (!isReady) {
    return (
      <div className="h-screen w-full bg-gradient-to-br from-amber-900 to-stone-900 flex items-center justify-center">
        <div className="text-center text-white">
          <div className="w-16 h-16 border-4 border-amber-400 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-amber-200">Starting Bitsy...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-full bg-gradient-to-br from-amber-900 to-stone-900 flex flex-col">
      {/* Header */}
      <div className="bg-black/30 p-3 flex items-center gap-3 border-b border-amber-500/30">
        <div className="w-10 h-10 rounded-full bg-amber-500 flex items-center justify-center">
          <MessageCircle className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="text-white font-bold">Bitsy</h1>
          <p className="text-amber-200 text-xs">Hodler Inn AI Concierge</p>
        </div>
        <button 
          onClick={() => setVoiceEnabled(!voiceEnabled)}
          className="ml-auto p-2 rounded-full hover:bg-white/10"
        >
          {voiceEnabled ? 
            <Volume2 className="w-5 h-5 text-amber-400" /> : 
            <VolumeX className="w-5 h-5 text-gray-400" />
          }
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] p-3 rounded-2xl ${
              msg.role === 'user' 
                ? 'bg-amber-500 text-white rounded-br-none' 
                : 'bg-stone-700 text-white rounded-bl-none'
            }`}>
              {msg.content}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-stone-700 p-3 rounded-2xl rounded-bl-none">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-amber-400 rounded-full animate-bounce"></span>
                <span className="w-2 h-2 bg-amber-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></span>
                <span className="w-2 h-2 bg-amber-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-3 bg-black/30 border-t border-amber-500/30">
        <div className="flex gap-2">
          <button
            onClick={toggleRecording}
            className={`p-3 rounded-full transition-colors ${
              isRecording 
                ? 'bg-red-500 animate-pulse' 
                : 'bg-amber-500 hover:bg-amber-600'
            }`}
          >
            {isRecording ? 
              <MicOff className="w-5 h-5 text-white" /> : 
              <Mic className="w-5 h-5 text-white" />
            }
          </button>
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="Type or speak..."
            className="flex-1 px-4 py-2 rounded-full bg-stone-700 text-white placeholder-gray-400 border border-amber-500/30 focus:outline-none focus:border-amber-500"
          />
          <button
            onClick={() => handleSendMessage()}
            disabled={!inputMessage.trim() || isLoading}
            className="p-3 rounded-full bg-amber-500 hover:bg-amber-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-5 h-5 text-white" />
          </button>
        </div>
      </div>
    </div>
  );
}
