import { useState, useEffect } from "react";
import { FaCheck, FaTimes, FaHome, FaClipboardList, FaUser } from "react-icons/fa";
import "./App.css";
// Import the audio file directly
import audioFile from "./audios/audio_order.wav";

export default function OrderPage() {
  const [clientPhone, setClientPhone] = useState("");
  const [clientName, setClientName] = useState("");
  const [showClientInfo, setShowClientInfo] = useState(false);
  const [hideButtons, setHideButtons] = useState(false);
  
  useEffect(() => {
    fetch("http://127.0.0.1:5000/api/tts-order-status?client_id=1")
      .then((res) => res.json())
      .then((data) => {
        setClientPhone(data.client_phone || "٠٥٥٥٥٥٥٥٥٥"); // Default Arabic number if none provided
        setClientName(data.client_name || "أحمد محمد"); // Default Arabic name if none provided
      })
      .catch(error => {
        console.error("❌ Error fetching client data:", error);
        // Set default values in case of error
        setClientPhone("٠٥٥٥٥٥٥٥٥٥");
        setClientName("أحمد محمد");
      });
  }, []);

  const handleAgree = () => {
    setShowClientInfo(true);
    setHideButtons(true);
  };

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      {/* Navbar */}
      <div className="fixed bottom-0 w-full bg-white shadow-md flex justify-around p-3 border-t">
        <FaHome className="text-gray-500 text-2xl" />
        <FaClipboardList className="text-green-500 text-2xl" />
        <FaUser className="text-gray-500 text-2xl" />
      </div>
      {/* Content */}
      <div className="flex-1 flex flex-col items-center justify-center p-4">
        <h1 className="text-xl font-bold mb-4">طلبيات جديدة</h1>
        
        {/* Client Info Display */}
        {showClientInfo && (
          <div className="bg-white p-4 rounded-lg shadow-md mb-4 w-full text-right">
            <h2 className="text-lg font-bold mb-2">معلومات على لكليان</h2>
            <p className="mb-1"><span className="font-semibold">{clientName} : الاسم</span></p>
            <p><span className="font-semibold">رقم الهاتف:</span> {clientPhone}</p>
          </div>
        )}
        
        {/* Audio Player with static file */}
        <audio controls className="w-full mb-4">
          <source src={audioFile} type="audio/wav" />
          Your browser does not support the audio element.
        </audio>
        
        {/* Buttons - only shown if hideButtons is false */}
        {!hideButtons && (
          <div className="flex gap-4">
            <button
              onClick={handleAgree}
              className="bg-green-500 text-white px-6 py-2 rounded flex items-center gap-2"
            >
              <FaCheck /> اوافق
            </button>
            <button className="border border-red-500 text-red-500 px-6 py-2 rounded flex items-center gap-2">
              <FaTimes /> ارفض
            </button>
          </div>
        )}
      </div>
    </div>
  );
}