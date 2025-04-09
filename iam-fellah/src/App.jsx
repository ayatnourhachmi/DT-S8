import { useState, useEffect } from "react";
import { FaCheck, FaTimes, FaHome, FaClipboardList, FaUser } from "react-icons/fa";
import "./App.css";
import audioFile from "./audios/audio_order.wav";

export default function OrderPage() {
  const [clientPhone, setClientPhone] = useState("");
  const [clientName, setClientName] = useState("");
  const [showClientInfo, setShowClientInfo] = useState(false);
  const [hideButtons, setHideButtons] = useState(false);

  useEffect(() => {
    fetch("http://127.0.0.1:5001/api/tts-order-status?client_id=1")
      .then((res) => res.json())
      .then((data) => {
        setClientPhone(data.client_phone || "764029345");
        setClientName(data.client_name || "أحمد محمد");
      })
      .catch((error) => {
        console.error("❌ Error fetching client data:", error);
        setClientPhone("764029345");
        setClientName("أحمد محمد");
      });
  }, []);

  const handleAgree = () => {
    setShowClientInfo(true);
    setHideButtons(true);
  };

  return (
    <div className="flex flex-col h-screen bg-gray-100 text-right">
      <div className="fixed bottom-0 w-full bg-green-500 shadow-md flex justify-around p-4 border-t text-white text-xl">
        <FaHome className="hover:text-gray-200 transition duration-300" />
        <FaClipboardList className="text-white" />
        <FaUser className="hover:text-gray-200 transition duration-300" />
      </div>

      <div className="flex-1 flex flex-col items-center justify-center px-4 pt-6 pb-16">
        <h1 className="text-3xl font-medium mb-6 text-slate-800">📦 طلبيات جديدة</h1>

        {showClientInfo && (
          <div className="bg-white p-6 rounded-lg shadow-lg w-full max-w-md mb-6 border border-gray-200">
            <h2 className="text-lg font-medium mb-3 text-gray-700">معلومات على الكليان</h2>
            <p className="text-gray-600 mb-1">
              <span className="font-semibold text-gray-800">{clientName}</span> : الاسم
            </p>
            <p className="text-gray-600">
              <span className="font-semibold text-gray-800">رقم الهاتف:</span> {clientPhone}
            </p>
          </div>
        )}

        <div className="bg-white p-4 rounded-lg shadow-md w-full max-w-md flex flex-col items-center mb-6">
          <p className="text-gray-700 font-medium mb-2">🔊 استمع إلى تفاصيل الطلب</p>
          <audio controls className="w-full">
            <source src={audioFile} type="audio/wav" />
            Your browser does not support the audio element.
          </audio>
        </div>

        {!hideButtons && (
          <div className="flex gap-4">
            <button
              onClick={handleAgree}
              className="bg-green-500 text-white px-6 py-3 rounded-lg shadow-md flex items-center gap-2 hover:bg-green-600 transition duration-300"
            >
              <FaCheck /> اوافق
            </button>
            <button className="border border-red-500 text-red-500 px-6 py-3 rounded-lg shadow-md flex items-center gap-2 hover:bg-red-500 hover:text-white transition duration-300">
              <FaTimes /> ارفض
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
