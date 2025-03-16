from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import pandas as pd
from bot import run_chatbot_message, session_states

# Load clients CSV
clients_df = pd.read_csv("clients.csv")  # Ensure this file exists

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    language = data.get('language', 'french')
    client_id = int(data.get('client_id', 1))  # Convert client_id to int
    
    response, state_info, detected_products_count, product_orders_count = run_chatbot_message(
        user_message,
        language,
        client_id
    )
    
    # Get actual detected products and product orders from session
    session = session_states.get(client_id, {})
    detected_products = []
    
    # First bug fix: run_chatbot_message returns counts, not actual objects
    # We need to get the actual product objects from the session
    if client_id in session_states:
        # Get current product if any
        if session.get("current_product"):
            detected_products = [{
                'id': int(session["current_product"]["id"]),  # Convert int64 to int
                'name': session["current_product"]["name"]
            }]
        
        # Get product orders
        product_orders = []
        for p in session.get("product_orders", []):
            product_orders.append({
                'id': int(p["product_id"]),  # Convert int64 to int
                'name': p["product_name"],
                'quantity': int(p["quantity"])  # Convert int64 to int
            })
    else:
        # Initialize empty lists if no session
        detected_products = []
        product_orders = []
    
    return jsonify({
        'response': response,
        'state': state_info,
        'detected_products': detected_products,
        'product_orders': product_orders
    })

@app.route('/api/order-status', methods=['GET'])
def order_status():
    client_id = request.args.get('client_id', type=int)
    if not client_id:
        return jsonify({'error': 'Client ID is required'}), 400
    
    # Reload orders from CSV
    orders_df = pd.read_csv("orders.csv")
    
    client_orders = orders_df[(orders_df['client_id'] == client_id) & (orders_df['status'] == 'Pending')]
    
    if client_orders.empty:
        return jsonify({'message': 'No confirmed orders found for this client.'}), 404
    
    latest_order = client_orders.iloc[-1]
    
    # Load client and farmer info
    clients_df = pd.read_csv("clients.csv")
    farmers_df = pd.read_csv("farmers.csv")
    
    client_row = clients_df[clients_df['id'] == client_id]
    client_info = client_row.iloc[0].to_dict() if not client_row.empty else {'name': 'Unknown', 'phone': 'Unknown'}
    
    farmer_id = int(latest_order['farmer_id'])  # Convert int64 to int
    farmer_row = farmers_df[farmers_df['id'] == farmer_id] if farmer_id else None
    farmer_info = farmer_row.iloc[0].to_dict() if farmer_row is not None and not farmer_row.empty else {'name': 'Unknown'}
    
    # Convert order data
    order_details = {
        'client': {
            'id': int(client_id),  # Convert int64 to int
            'name': client_info.get('name', 'Unknown'),
            'phone': str(client_info.get('phone', 'Unknown'))  # Convert int64 to str
        },
        'farmer': {
            'id': farmer_id,
            'name': farmer_info.get('name', 'Unknown')
        },
        'products': [
            {
                'id': int(latest_order['product_id']),  # Convert int64 to int
                'quantity': int(latest_order['quantity'])  # Convert int64 to int
            }
        ],
        'delivery_time': latest_order['delivery_time']
    }
    
    return jsonify(order_details)

if __name__ == '__main__':
    app.run(debug=True, port=5001)