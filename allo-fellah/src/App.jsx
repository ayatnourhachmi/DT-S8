import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import { useState, useEffect, useRef } from "react";
import { Send, User, Bot } from "lucide-react";
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
    if (!input.trim()) return;
    
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
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
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
                <p style={{ direction: detectLanguage(msg.text) === "arabic" ? "rtl" : "ltr" }}>
                  {msg.text}
                </p>
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
        
        {/* Input Field */}
        <div className="flex items-center p-3 bg-gray-100 border-t border-gray-300">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            className="flex-1 p-2 border border-gray-300 focus:border-green-500 rounded-full outline-none bg-white px-4 text-gray-800"
            placeholder="Type a message..."
            dir={language === "arabic" ? "rtl" : "ltr"}
          />
          <button 
            onClick={sendMessage} 
            disabled={loading}
            className={`ml-2 p-2 ${loading ? 'bg-gray-400' : 'bg-green-600 hover:bg-green-700'} 
                      text-white rounded-full transition`}
          >
            <Send size={20} />
          </button>
        </div>
      </div>
    </div>
  );
}