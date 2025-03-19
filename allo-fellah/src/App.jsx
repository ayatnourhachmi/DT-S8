import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import { useState, useEffect, useRef } from "react";
import { Send, User, Bot, Mic, StopCircle } from "lucide-react";
import axios from "axios";

export default function Chatbot() {
  const [messages, setMessages] = useState([
    { type: "bot", text: "مرحبا! Bonjour! Comment puis-je vous aider aujourd'hui?" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [clientId] = useState(1); // Default client ID - can be dynamic based on login
  const [language, setLanguage] = useState("french"); // Default language
  const messagesEndRef = useRef(null);
  
  // Audio recording states
  const [isRecording, setIsRecording] = useState(false);
  const [audioURL, setAudioURL] = useState(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const detectLanguage = (text) => {
    // Simple language detection based on characters
    if (/[\u0600-\u06FF]/.test(text)) {
      return "arabic";
    } else if (/[éèêëàâäôöùûüçæœ]/i.test(text)) {
      return "french";
    }
    return language; // Keep current language if detection fails
  };

  const sendMessage = async () => {
    if (!input.trim() && !audioURL) return;
    
    if (input.trim()) {
      // Text message flow
      // Detect language from input
      const detectedLanguage = detectLanguage(input);
      setLanguage(detectedLanguage);
      
      // Add user message to UI
      const newMessages = [...messages, { type: "user", text: input }];
      setMessages(newMessages);
      setLoading(true);
      setInput("");
      
      try {
        // Send message to backend
        const response = await axios.post('http://localhost:5000/api/chat', {
          message: input,
          language: detectedLanguage,
          client_id: clientId
        });
        
        // Add bot response to UI
        setMessages((prev) => [
          ...prev,
          { type: "bot", text: response.data.response }
        ]);
      } catch (error) {
        console.error("Error communicating with chatbot:", error);
        setMessages((prev) => [
          ...prev,
          { type: "bot", text: "Sorry, I'm having trouble connecting to the server. Please try again later." }
        ]);
      } finally {
        setLoading(false);
      }
    } else if (audioURL) {
      // Audio message flow
      // Add user audio message to UI
      setMessages((prev) => [...prev, { type: "user", text: "🎤 Audio Message", isAudio: true, audioSrc: audioURL }]);
      setLoading(true);
      
      try {
        // Fetch the audio blob
        const audioBlob = await fetch(audioURL).then(r => r.blob());
        
        // Create form data to send audio file
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.wav');
        formData.append('client_id', clientId);
        formData.append('language', language);
        
        // Send audio to backend
        const response = await axios.post('http://localhost:5000/api/audio-chat', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        
        // Add bot response to UI
        setMessages((prev) => [
          ...prev,
          { type: "bot", text: response.data.response }
        ]);
      } catch (error) {
        console.error("Error sending audio to chatbot:", error);
        setMessages((prev) => [
          ...prev,
          { type: "bot", text: "Sorry, I couldn't process your audio message. Please try again." }
        ]);
      } finally {
        setLoading(false);
        setAudioURL(null); // Clear the audio after sending
      }
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };
  
  // Audio recording functions
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Reset audio chunks
      audioChunksRef.current = [];
      
      // Create media recorder
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      
      // Handle data available event
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };
      
      // Handle recording stop event
      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        const audioUrl = URL.createObjectURL(audioBlob);
        setAudioURL(audioUrl);
        
        // Stop all audio tracks
        stream.getTracks().forEach(track => track.stop());
      };
      
      // Start recording
      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error("Error accessing microphone:", error);
      alert("Could not access your microphone. Please check your permissions.");
    }
  };
  
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };
  
  const cancelRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setAudioURL(null);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-200 p-4">
      <div className="w-full max-w-sm h-[85vh] bg-white shadow-2xl rounded-3xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-center gap-2 text-lg font-semibold bg-green-600 text-white py-4 px-6">
          <Bot size={24} />
          <span>Allo Fellah Assistant</span>
        </div>
        
        {/* Chat Messages */}
        <div className="flex-1 overflow-auto p-4 space-y-3">
          {messages.map((msg, index) => (
            <div key={index} className={`flex ${msg.type === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`flex items-center gap-2 max-w-[80%] p-3 rounded-lg shadow-md ${
                msg.type === "user" ? "bg-green-500 text-white font-medium" : "bg-gray-100 text-gray-800"
              }`}>
                {msg.type === "user" ? <User size={18} /> : <Bot size={18} />}
                {msg.isAudio ? (
                  <div className="flex flex-col gap-1">
                    <p>{msg.text}</p>
                    <audio src={msg.audioSrc} controls className="max-w-full h-8"></audio>
                  </div>
                ) : (
                  <p style={{ direction: detectLanguage(msg.text) === "arabic" ? "rtl" : "ltr" }}>
                    {msg.text}
                  </p>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 text-gray-800 p-3 rounded-lg shadow-md">
                <div className="flex space-x-2">
                  <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: "0ms" }}></div>
                  <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: "300ms" }}></div>
                  <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: "600ms" }}></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        
        {/* Audio Preview (if recorded) */}
        {audioURL && !isRecording && (
          <div className="px-3 py-2 bg-gray-50 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-green-600">
                <Mic size={18} />
                <span className="text-sm">Audio recorded</span>
              </div>
              <div className="flex gap-2">
                <button 
                  onClick={() => setAudioURL(null)} 
                  className="text-xs text-red-500 hover:underline"
                >
                  Delete
                </button>
                <audio src={audioURL} controls className="h-8 w-32"></audio>
              </div>
            </div>
          </div>
        )}
        
        {/* Input Field */}
        <div className="flex items-center p-3 bg-gray-100 border-t border-gray-300">
          {isRecording ? (
            <div className="flex-1 flex items-center justify-between bg-white p-2 border border-red-300 rounded-full">
              <div className="flex items-center gap-2 text-red-500 ml-2">
                <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div>
                <span>Recording...</span>
              </div>
              <div className="flex gap-2">
                <button 
                  onClick={cancelRecording}
                  className="p-1 text-gray-500 hover:text-gray-700"
                >
                  Cancel
                </button>
                <button 
                  onClick={stopRecording} 
                  className="p-2 bg-red-500 hover:bg-red-600 text-white rounded-full"
                >
                  <StopCircle size={18} />
                </button>
              </div>
            </div>
          ) : (
            <>
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                className="flex-1 p-2 border border-gray-300 focus:border-green-500 rounded-full outline-none bg-white px-4 text-gray-800"
                placeholder="Type a message..."
                dir={language === "arabic" ? "rtl" : "ltr"}
                disabled={isRecording}
              />
              {!audioURL ? (
                <button
                  onClick={startRecording}
                  className="ml-2 p-2 bg-gray-400 hover:bg-gray-500 text-white rounded-full transition"
                  title="Record audio message"
                >
                  <Mic size={20} />
                </button>
              ) : null}
              <button 
                onClick={sendMessage} 
                disabled={loading || (isRecording && !input.trim() && !audioURL)}
                className={`ml-2 p-2 ${loading ? 'bg-gray-400' : 'bg-green-600 hover:bg-green-700'} 
                          text-white rounded-full transition`}
                title="Send message"
              >
                <Send size={20} />
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}