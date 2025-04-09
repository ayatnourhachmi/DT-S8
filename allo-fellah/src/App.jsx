import { useState, useEffect, useRef } from "react";
import { Send, User, Bot} from "lucide-react";
import "./App.css";
import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL;

export default function Chatbot() {
  const [messages, setMessages] = useState([
    { type: "bot", text: "مرحبا! Bonjour! Comment puis-je vous aider aujourd'hui?" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [clientId] = useState(1); 
  const [language, setLanguage] = useState("french"); 
  const [orderData, setOrderData] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      // Only check bot messages
      if (lastMessage.type === "bot") {
        extractOrderDetails(lastMessage.text);
      }
    }
  }, [messages]);

  const detectLanguage = (text) => {
    if (/[\u0600-\u06FF]/.test(text)) {
      return "arabic";
    } else if (/[éèêëàâäôöùûüçæœ]/i.test(text)) {
      return "french";
    }
    return language;
  };

  const extractOrderDetails = (response) => {
    const regex = /\*\*Produit:\*\*\s+(.*?)\s+\*\*Quantité:\*\*\s+(.*?)\s+\*\*Producteur:\*\*\s+(.*?)\s+\*\*Livraison:\*\*\s+(.*?)(?:\s+|$)/;
    const matches = response.match(regex);
    
    if (matches) {
      const extractedData = {
        product_name: matches[1].trim(),
        quantity: matches[2].trim(),
        Farmer_selected: matches[3].trim(),
        Delivery_time: matches[4].trim()
      };
      setOrderData(extractedData);
      sendOrderToBackend(extractedData);
    }
  };

  const sendOrderToBackend = async (order) => {
    try {
      const response = await axios.post(`${API_URL}/save_order`, {
        ...order,
        client_id: clientId,
      });

      console.log("✅ Order saved:", response.data);
      
      setMessages((prev) => [
        ...prev, 
        { 
          type: "bot", 
          text: `Votre commande a été enregistrée avec succès! Produit: ${order.product_name}, Quantité: ${order.quantity}, Livraison prévue: ${order.Delivery_time}`
        }
      ]);
      
    } catch (error) {
      console.error("❌ Error sending order to backend:", error);
      
      setMessages((prev) => [
        ...prev, 
        { 
          type: "bot", 
          text: "Une erreur s'est produite lors de l'enregistrement de votre commande. Veuillez réessayer."
        }
      ]);
    }
  };

  const sendMessage = async () => {
    if (!input.trim()) return;

    const detectedLanguage = detectLanguage(input);
    setLanguage(detectedLanguage);

    const userMessage = input;
    setMessages((prev) => [...prev, { type: "user", text: userMessage }]);
    setLoading(true);
    setInput("");

    try {
      const response = await axios.post(`${API_URL}/api/chat`, {
        message: userMessage,
        language: detectedLanguage,
        client_id: clientId
      });

      setMessages((prev) => [...prev, { type: "bot", text: response.data.response }]);
    } catch (error) {
      console.error("❌ Error connecting to backend:", error);
      setMessages((prev) => [
        ...prev, 
        { 
          type: "bot", 
          text: detectedLanguage === "arabic" 
            ? "❌ خطأ: لا يمكن الاتصال بالخادم." 
            : "❌ Erreur: Impossible de se connecter au serveur." 
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-200 p-4">
      <div className="w-full max-w-sm h-[85vh] bg-white shadow-2xl rounded-3xl flex flex-col overflow-hidden">
        <div className="flex items-center justify-center gap-2 text-lg font-semibold bg-green-600 text-white py-4 px-6">
          <Bot size={24} />
          <span>Allo Fellah Assistant</span>
        </div>

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

        <div className="flex items-center p-3 bg-gray-100 border-t border-gray-300">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            className="flex-1 p-2 border border-gray-300 focus:border-green-500 rounded-full outline-none bg-white px-4 text-gray-800"
            placeholder="Type a message..."
            dir={language === "arabic" ? "rtl" : "ltr"}
          />
          <button 
            onClick={sendMessage} 
            disabled={loading || !input.trim()}
            className="ml-2 p-2 bg-green-600 hover:bg-green-700 text-white rounded-full transition flex items-center justify-center"
            title="Send message"
          >
            <Send size={20} />
          </button>
        </div>
      </div>
    </div>
  );
}