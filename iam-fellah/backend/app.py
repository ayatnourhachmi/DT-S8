from flask import Flask, request, jsonify
import requests
from tts import generate_tts  # Import the function from tts.py
from flask_cors import CORS  # Import CORS for cross-origin requests

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Function to translate the order response to Darija
def translate_to_darija(order_data):
    client_name = order_data["client"]["name"]
    client_phone = order_data["client"]["phone"]
    farmer_name = order_data["farmer"]["name"]
    delivery_time = order_data["delivery_time"]
    products = order_data["products"]
    
    # Translation mapping
    delivery_translation = {
        "tomorrow_morning": "غدا في الصباح",
        "tomorrow_evening": "غدا في العشية",
        "today_morning": "اليوم في الصباح",
        "today_evening": "اليوم في العشية"
    }
    
    product_translation = {
        1: "مطيشة",
        2: "بطاطا"
    }
    
    def format_quantity(quantity, product_name):
        if quantity >= 1:
            return f"{quantity} كيلو ديال {product_name}"
        elif quantity == 0.5:
            return f"نص كيلو ديال {product_name}"
        else:
            return f"{int(quantity * 1000)} غرام ديال {product_name}"
    
    product_list = "\n".join([
        format_quantity(p['quantity'], product_translation.get(p['id'], 'منتج مجهول'))
        for p in products
    ])
    
    translated_text = (
        f"واحدالسلام وعليكم سي {farmer_name}\n"
        f"عندك {product_list}\n"
        f"توصلها ل {client_name}\n"
        f"{delivery_translation.get(delivery_time, 'في وقت غير معروف')}\n"
        "باش تأكد لنا اتوصلها ضغط على الزر الاخضر وغطلع ليك نمرة لكليان\n"
        "أولا ضغط على لحمرا باش ترفض"
    )
    
    return translated_text, client_name, client_phone

@app.route('/api/tts-order-status', methods=['GET'])
def get_order_status_tts():
    client_id = request.args.get("client_id", 1)  # Default to 1 if not provided
    
    try:
        order_status_url = f"http://127.0.0.1:5001/api/order-status?client_id={client_id}"
        response = requests.get(order_status_url)
        
        if response.status_code != 200:
            return jsonify({
                "error": "Failed to fetch order status",
                "client_name": "عميل غير معروف",
                "client_phone": "٠٠٠٠٠٠٠٠٠٠"
            }), 500
            
        order_data = response.json()
        translated_text, client_name, client_phone = translate_to_darija(order_data)
        
        # Generate TTS from the translated text
        try:
            audio_file = "audios/audio_order.wav"  # Static file path to match the frontend
            generate_tts(translated_text, output_path=audio_file)  # Save locally instead of URL
            
            return jsonify({
                "success": True,
                "client_name": client_name,
                "client_phone": client_phone
            })
            
        except Exception as e:
            return jsonify({
                "error": f"TTS generation failed: {str(e)}",
                "client_name": client_name,
                "client_phone": client_phone
            })
            
    except Exception as e:
        return jsonify({
            "error": f"Server error: {str(e)}",
            "client_name": "عميل غير معروف",
            "client_phone": "٠٠٠٠٠٠٠٠٠٠"
        })

if __name__ == '__main__':
    app.run(debug=True, port=5000)