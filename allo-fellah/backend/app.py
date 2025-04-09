from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import pandas as pd
import logging
import socket
from bot import run_chatbot_message, session_states

logging.basicConfig(level=logging.INFO)

PORT = 5000
app = Flask(__name__)

CORS(app)

@app.after_request
def add_security_headers(response):
    response.headers["Permissions-Policy"] = "microphone=()"
    return response

def load_csv(file_name):
    try:
        return pd.read_csv(file_name)
    except FileNotFoundError:
        logging.warning(f"Warning: {file_name} not found. Returning empty DataFrame.")
        return pd.DataFrame()

def save_csv(df, file_name):
    df.to_csv(file_name, index=False)

clients_df = load_csv("clients.csv")
orders_df = load_csv("orders.csv")
farmers_df = load_csv("farmers.csv")

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    language = data.get('language', 'french')
    client_id = int(data.get('client_id', 1))

    response, state_info, detected_products_count, product_orders_count = run_chatbot_message(
        user_message,
        language,
        client_id
    )

    session = session_states.get(client_id, {})
    detected_products = []
    product_orders = []

    if client_id in session_states:
        if session.get("current_product"):
            detected_products = [{
                'id': int(session["current_product"]["id"]),
                'name': session["current_product"]["name"]
            }]
        
        for p in session.get("product_orders", []):
            product_orders.append({
                'id': int(p["product_id"]),
                'name': p["product_name"],
                'quantity': int(p["quantity"])
            })

    return jsonify({
        'response': response,
        'state': state_info,
        'detected_products': detected_products,
        'product_orders': product_orders
    })

@app.route('/api/order-status', methods=['GET'])
def order_status():
    client_id = request.args.get('client_id', type=int)
    if client_id is None:
        return jsonify({'error': 'Client ID is required'}), 400

    orders_df = load_csv("orders.csv")
    client_orders = orders_df[(orders_df['client_id'] == client_id) & (orders_df['status'] == 'Pending')]

    if client_orders.empty:
        return jsonify({'message': 'No confirmed orders found for this client.'}), 404

    latest_order = client_orders.sort_values(by="id", ascending=False).iloc[0]

    clients_df = load_csv("clients.csv")
    farmers_df = load_csv("farmers.csv")

    client_row = clients_df[clients_df['id'] == client_id]
    client_info = client_row.iloc[0].to_dict() if not client_row.empty else {'name': 'Unknown', 'phone': 'Unknown'}

    farmer_id = int(latest_order.get('farmer_id', 0))
    farmer_row = farmers_df[farmers_df['id'] == farmer_id] if farmer_id else None
    farmer_info = farmer_row.iloc[0].to_dict() if farmer_row is not None and not farmer_row.empty else {'name': 'Unknown'}

    order_details = {
        'client': {
            'id': int(client_id),
            'name': client_info.get('name', 'Unknown'),
            'phone': str(client_info.get('phone', 'Unknown'))
        },
        'farmer': {
            'id': farmer_id,
            'name': farmer_info.get('name', 'Unknown')
        },
        'products': [
            {
                'id': int(latest_order.get('product_id', 0)),
                'quantity': int(latest_order.get('quantity', 0))
            }
        ],
        'delivery_time': latest_order.get('delivery_time', 'Unknown')
    }

    return jsonify(order_details)

@app.route("/save_order", methods=["POST"])
def save_order():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid data"}), 400

    orders_df = load_csv("orders.csv")

    new_order = pd.DataFrame([{
        'client_id': data.get('client_id', 0),
        'product_name': data.get('product_name', 'Unknown'),
        'quantity': data.get('quantity', 'Unknown'),
        'farmer_selected': data.get('Farmer_selected', 'Unknown'),
        'delivery_time': data.get('Delivery_time', 'Unknown'),
        'status': 'Pending'
    }])

    orders_df = pd.concat([orders_df, new_order], ignore_index=True)
    save_csv(orders_df, "orders.csv")

    return jsonify({"message": "Order saved successfully", "order": new_order.to_dict(orient="records")[0]})


if __name__ == '__main__':
    local_ip = socket.gethostbyname(socket.gethostname())

    print("\nFlask server is running! Access it at:")
    print(f"Local:      http://127.0.0.1:{PORT}")
    print(f"Network:    http://{local_ip}:{PORT}  (For phone access)\n")

    app.run(host='0.0.0.0', port=PORT, debug=True)
