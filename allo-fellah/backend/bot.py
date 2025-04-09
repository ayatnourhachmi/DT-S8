import os
import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta
from google import genai
from google.genai import types

client = genai.Client(
    api_key=os.environ.get("GOOGLE_API_KEY"),
)
model = "gemini-2.0-flash-exp"

products_df = pd.read_csv("products.csv")
farmers_df = pd.read_csv("farmers.csv")
clients_df = pd.read_csv("clients.csv")
farmer_products_df = pd.read_csv("farmer_products.csv")
orders_df = pd.read_csv("orders.csv")

french_products = {}
arabic_products = {}

for _, row in products_df.iterrows():
    product_id = row['id']
    english_name = row['name']
    french_name = row['french_name']
    arabic_name = row['arabic_name']
    
    french_products[french_name.lower()] = {
        'id': product_id,
        'name': french_name,
        'arabic_name': arabic_name,
        'english_name': english_name
    }
    
    arabic_products[arabic_name] = {
        'id': product_id,
        'name': arabic_name,
        'french_name': french_name,
        'english_name': english_name
    }

conversation = [
    types.Content(
        role="user",
        parts=[types.Part.from_text(text="bonjour")],
    ),
    types.Content(
        role="model",
        parts=[types.Part.from_text(text="Bonjour! Comment puis-je vous aider aujourd'hui? Souhaitez-vous commander quelque chose?")],
    ),
    types.Content(
        role="user",
        parts=[types.Part.from_text(text="سلام")],
    ),
    types.Content(
        role="model",
        parts=[types.Part.from_text(text="وعليكم السلام! كيف يمكنني مساعدتك اليوم؟ هل تود أن تطلب شيئًا؟")],
    )
]

product_list_french = "\n".join([f"- {p['name']}" for p in french_products.values()])
product_list_arabic = "\n".join([f"- {p['name']}" for p in arabic_products.values()])

farmer_products_data = []
for _, fp_row in farmer_products_df.iterrows():
    farmer_id = fp_row['farmer_id']
    product_id = fp_row['product_id']
    stock = fp_row['stock']
    price = fp_row['price']
    
    farmer_row = farmers_df[farmers_df['id'] == farmer_id]
    product_row = products_df[products_df['id'] == product_id]
    
    if not farmer_row.empty and not product_row.empty:
        farmer_name = farmer_row['name'].values[0]
        product_name = product_row['name'].values[0]
        
        farmer_products_data.append((farmer_name, product_name, stock, price))

farmer_details = "\n".join([
    f"- {farmer} sells {product} with {stock} kg available at {price} per kilo."
    for farmer, product, stock, price in farmer_products_data
])

system_instruction = [
    types.Part.from_text(text=f"""
    IMPORTANT: This is a multilingual ordering chatbot.
    - If the user speaks in Arabic, ALWAYS respond in Arabic.
    - If the user speaks in French, ALWAYS respond in French.
    - Never respond in English unless the user specifically uses English.
    
    Available products in French:
    {product_list_french}
    
    Available products in Arabic:
    {product_list_arabic}

    Farmer inventory:
    {farmer_details}

    **Chatbot Flow:**
    1. Greeting → Welcome user in their language.
    2. Product Selection → Ask what product they want to order.
    3. Quantity Selection → Ask how much they need.
    4. Stock Check:
       - If available → Proceed.
       - If unavailable → Inform user and ask if they want to choose another product or reduce quantity.
    5. More Products Option → Ask if they want more products.
    6. Delivery Time → Ask for delivery time (today/tomorrow, morning/evening).
    7. Farmer Selection:
       - Display only **farmers with sufficient stock**.
       - Rank **farmers by distance, price per kg, and feedback rating**.
       - Ask user to select a farmer.
    8. Order Confirmation → Summarize and confirm the order.
    9. Order details :(
        "product_name":
        "quantity":
        "farmer_name":
        "delivery_time":
        )"""
    )
]


def extract_order_details(session_state):
    """
    Extract structured order details from the session state
    for better logging and debugging.
    
    Args:
        session_state: Current session state dictionary
        
    Returns:
        dict: Structured order details
    """
    order_details = {
        "products": [],
        "farmer_name": None,
        "farmer_id": None,
        "delivery_time": None,
        "total_items": 0,
        "total_quantity": 0,
        "language": session_state.get("current_language", "unknown"),
        "state": session_state.get("current_state", "unknown")
    }
    
    for product_order in session_state.get("product_orders", []):
        product_info = {
            "product_id": product_order.get("product_id"),
            "name": product_order.get("product_name"),
            "quantity": product_order.get("quantity", 0)
        }
        order_details["products"].append(product_info)
        order_details["total_items"] += 1
        order_details["total_quantity"] += product_order.get("quantity", 0)
    
    if session_state.get("selected_farmer") is not None:
        order_details["farmer_id"] = session_state.get("selected_farmer")
        
        if session_state.get("available_farmers"):
            for farmer in session_state.get("available_farmers"):
                if farmer.get("id") == session_state.get("selected_farmer"):
                    order_details["farmer_name"] = farmer.get("name")
                    break
    
    if session_state.get("delivery_time"):
        delivery_time = session_state.get("delivery_time")
        if delivery_time:
            parts = delivery_time.split("_")
            if len(parts) == 2:
                order_details["delivery_time"] = f"{parts[0]} {parts[1]}"
            else:
                order_details["delivery_time"] = delivery_time
    
    return order_details

def print_order_summary(order_details):
    """
    Pretty print order details to console in a structured format.
    
    Args:
        order_details: Structured order details dictionary
    """
    print("\n" + "=" * 50)
    print(" ORDER SUMMARY ".center(50, "="))
    print("=" * 50)
    
    print(f"Language: {order_details['language']}")
    print(f"Current State: {order_details['state']}")
    print("-" * 50)
    
    if order_details["products"]:
        print("PRODUCTS:")
        for i, product in enumerate(order_details["products"], 1):
            print(f"  {i}. {product['name']} - {product['quantity']} kg (ID: {product['product_id']})")
        print(f"Total Items: {order_details['total_items']}")
        print(f"Total Quantity: {order_details['total_quantity']} kg")
    else:
        print("No products selected yet")
    
    print("-" * 50)
    
    if order_details["farmer_name"]:
        print(f"Selected Farmer: {order_details['farmer_name']} (ID: {order_details['farmer_id']})")
    else:
        print("No farmer selected yet")
    
    if order_details["delivery_time"]:
        print(f"Delivery Time: {order_details['delivery_time']}")
    else:
        print("No delivery time specified yet")
    
    print("=" * 50 + "\n")

def check_stock(product_id, quantity):
    if product_id is None:
        return None
        
    available_farmers = []
    for _, row in farmer_products_df[farmer_products_df['product_id'] == product_id].iterrows():
        if row['stock'] >= quantity:
            farmer_id = row['farmer_id']
            farmer_row = farmers_df[farmers_df['id'] == farmer_id]
            
            if not farmer_row.empty:
                farmer_row = farmer_row.iloc[0]
                available_farmers.append((
                    farmer_id, 
                    farmer_row['name'], 
                    row['stock'], 
                    row['price']
                ))

    if not available_farmers:
        return None

    return available_farmers


def find_best_farmers(product_id, quantity, client_id):
    """Fix: Ensure only farmers with sufficient stock are shown in ranking"""
    if product_id is None or client_id is None:
        return None
        
    client_row = clients_df[clients_df['id'] == client_id]
    if client_row.empty:
        return None
        
    client_row = client_row.iloc[0]
    client_lat, client_lon = client_row['latitude'], client_row['longitude']
    
    available_farmers = []
    for _, row in farmer_products_df[farmer_products_df['product_id'] == product_id].iterrows():
        if row['stock'] >= quantity:
            farmer_id = row['farmer_id']
            farmer_row = farmers_df[farmers_df['id'] == farmer_id]
            
            if not farmer_row.empty:
                farmer_row = farmer_row.iloc[0]
                
                distance = np.sqrt((farmer_row['latitude'] - client_lat) ** 2 + (farmer_row['longitude'] - client_lon) ** 2)
                
                available_farmers.append({
                    "id": farmer_id,
                    "name": farmer_row['name'],
                    "stock": row['stock'],
                    "price": row['price'],
                    "distance": distance,
                    "feedback": farmer_row['feedback']
                })

    if not available_farmers:
        return None
    
    sorted_farmers = sorted(available_farmers, key=lambda x: (x['distance'], x['price'], -x['feedback']))
    
    return sorted_farmers[:3]  # Return top 3 best options


def save_order(client_id, product_orders, farmer_id, delivery_time):
    global orders_df, farmer_products_df
    
    print(f"Attempting to save order: client={client_id}, products={product_orders}, farmer={farmer_id}")
    
    if not product_orders or farmer_id is None:
        print("No products or farmer specified - cannot save order")
        return False
    
    try:
        new_orders = []
        
        for po in product_orders:
            new_order_id = orders_df['id'].max() + 1 if len(orders_df) > 0 else 1
            new_order = {
                'id': new_order_id,
                'client_id': client_id,
                'product_id': po['product_id'],
                'farmer_id': farmer_id,
                'quantity': po['quantity'],
                'status': 'Pending',
                'delivery_time': delivery_time,
            }
            
            print(f"New order created: {new_order}")
            new_orders.append(new_order)
            
            mask = (farmer_products_df['farmer_id'] == farmer_id) & (farmer_products_df['product_id'] == po['product_id'])
            if mask.any():
                farmer_products_df.loc[mask, 'stock'] -= po['quantity']
                print(f"Updated inventory for farmer {farmer_id}, product {po['product_id']}")
            else:
                print(f"No matching inventory found for farmer {farmer_id}, product {po['product_id']}")
        
        try:
            print("\n" + "#" * 60)
            print("# FINAL ORDER BEING SAVED TO DATABASE #".center(60, "#"))
            print("#" * 60)
            
            farmer_name = "Unknown"
            farmer_row = farmers_df[farmers_df['id'] == farmer_id]
            if not farmer_row.empty:
                farmer_name = farmer_row.iloc[0]['name']
            
            order_summary = {
                "products": [],
                "farmer_name": farmer_name,
                "farmer_id": farmer_id,
                "delivery_time": delivery_time,
                "client_id": client_id,
                "total_items": len(product_orders),
                "total_quantity": sum(po['quantity'] for po in product_orders)
            }
            
            for po in product_orders:
                order_summary["products"].append({
                    "product_id": po['product_id'],
                    "name": po['product_name'],
                    "quantity": po['quantity']
                })
            
            print_order_summary(order_summary)
            print("#" * 60 + "\n")
            
            orders_df = pd.concat([orders_df, pd.DataFrame(new_orders)], ignore_index=True)
            print(f"Orders DataFrame after update: {len(orders_df)} orders")
        except Exception as e:
            print(f"Error in concat operation: {e}")
            return False
        
        try:
            orders_df.to_csv("orders.csv", index=False)
            print(f"Order saved successfully! New order count: {len(new_orders)}")
            
            farmer_products_df.to_csv("farmer_products.csv", index=False)
            print("Inventory updated successfully!")
            
            success = verify_order_saved(client_id, new_orders[0]['product_id'], farmer_id)
            return success
        except Exception as e:
            print(f"Error writing to CSV: {e}")
            return False
            
    except Exception as e:
        print(f"Error processing order: {e}")
        return False

def verify_order_saved(client_id, product_id, farmer_id):
    """Verify if order was saved properly to CSV"""
    try:
        verification_df = pd.read_csv("orders.csv")
        matching_orders = verification_df[
            (verification_df['client_id'] == client_id) & 
            (verification_df['product_id'] == product_id) & 
            (verification_df['farmer_id'] == farmer_id)
        ]
        
        if len(matching_orders) > 0:
            print(f"Verification successful: {len(matching_orders)} matching orders found")
            return True
        else:
            print("Verification failed: No matching orders found")
            return False
    except Exception as e:
        print(f"Verification error: {e}")
        return False


def detect_language(text):
    """Detect language based on input text."""
    if any(char in text for char in 'ابتثجحخدذرزسشصضطظعغفقكلمنهوي'):
        return "arabic"
    elif any(char in text for char in 'éèêëàâäôöùûüçæœ') or re.search(r'\b(je|tu|vous|nous|le|la|les|bonjour|merci)\b', text.lower()):
        return "french"
    else:
        return "english"

def detect_products(message, language):
    detected_products = []
    
    if language == "french":
        product_dict = french_products
        message = message.lower()
    elif language == "arabic":
        product_dict = arabic_products
    else:
        for product_info in products_df.iterrows():
            product_name = product_info[1]['name'].lower()
            if product_name in message.lower():
                detected_products.append({
                    'id': product_info[1]['id'],
                    'name': product_info[1]['name'],
                    'french_name': product_info[1]['french_name'],
                    'arabic_name': product_info[1]['arabic_name']
                })
        return detected_products
        
    for product_name, product_info in product_dict.items():
        if product_name.lower() in message.lower():
            detected_products.append(product_info)
            
    return detected_products

def extract_quantity(message, language):
    """Extract numeric quantity from user input in French, Arabic, or English."""
    number_words = {
        "french": {
            "un": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5,
            "six": 6, "sept": 7, "huit": 8, "neuf": 9, "dix": 10
        },
        "arabic": {
            "واحد": 1, "اثنان": 2, "ثلاثة": 3, "أربعة": 4, "خمسة": 5,
            "ستة": 6, "سبعة": 7, "ثمانية": 8, "تسعة": 9, "عشرة": 10
        },
        "english": {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
        }
    }

    match = re.search(r"(\d+)", message)
    if match:
        return int(match.group(1))

    words = message.split()
    for word in words:
        word_lower = word.lower()
        for lang, number_dict in number_words.items():
            if word_lower in number_dict:
                return number_dict[word_lower]

    return 1

def process_order_request(user_input, language, client_id):
    detected_products = detect_products(user_input, language)
    
    if not detected_products:
        if language == "french":
            return "Je n'ai pas trouvé ce produit dans notre catalogue. Pouvez-vous préciser?", None
        elif language == "arabic":
            return "لم أجد هذا المنتج في دليلنا. هل يمكنك التوضيح؟", None
        else:
            return "I couldn't find this product in our catalog. Could you please specify?", None

    product = detected_products[0]
    quantity = extract_quantity(user_input, language)
    
    available_farmers = check_stock(product['id'], quantity)
    
    if available_farmers is None:
        if language == "french":
            return f"Malheureusement, nous n'avons pas {quantity}kg de {product['name']} en stock. " \
                f"Souhaitez-vous en commander une quantité inférieure ou choisir un autre produit?", None
        elif language == "arabic":
            return f"للأسف، ليس لدينا {quantity} كجم من {product['name']} في المخزون. " \
                f"هل ترغب في طلب كمية أقل أو اختيار منتج آخر؟", None
        else:
            return f"Unfortunately, we don't have {quantity}kg of {product['name']} in stock. " \
                f"Would you like to order a smaller quantity or choose another product?", None

    best_farmers = find_best_farmers(product['id'], quantity, client_id)
    
    if not best_farmers:
        if language == "french":
            return f"Aucun agriculteur proche ne peut fournir {quantity}kg de {product['name']}. Voulez-vous essayer un autre produit?", None
        elif language == "arabic":
            return f"لا يوجد مزارع قريب يمكنه توفير {quantity} كجم من {product['name']}. هل تريد تجربة منتج آخر؟", None
        else:
            return f"No nearby farmer can provide {quantity}kg of {product['name']}. Would you like to try another product?", None
    
    if language == "french":
        farmer_options = "\n".join([
            f"{i+1}. {f['name']} - {f['price']}dh/kg, {round(f['distance'], 2)}km, Note: {f['feedback']}/5"
            for i, f in enumerate(best_farmers)
        ])
        response = f"Voici les agriculteurs disponibles pour {quantity}kg de {product['name']}:\n{farmer_options}\n" \
               f"Veuillez choisir un numéro."
    elif language == "arabic":
        farmer_options = "\n".join([
            f"{i+1}. {f['name']} - {f['price']}درهم/كجم, {round(f['distance'], 2)}كم, تقييم: {f['feedback']}/5"
            for i, f in enumerate(best_farmers)
        ])
        response = f"إليك المزارعين المتاحين لـ {quantity} كجم من {product['name']}:\n{farmer_options}\n" \
               f"يرجى اختيار رقم."
    else:
        farmer_options = "\n".join([
            f"{i+1}. {f['name']} - {f['price']}dh/kg, {round(f['distance'], 2)}km, Rating: {f['feedback']}/5"
            for i, f in enumerate(best_farmers)
        ])
        response = f"Here are the available farmers for {quantity}kg of {product['name']}:\n{farmer_options}\n" \
               f"Please choose a number."
    
    return response, product


session_states = {}

def run_chatbot_message(user_input, language_hint="french", client_id=1):
    if client_id not in session_states:
        session_states[client_id] = {
            "current_language": language_hint,
            "current_state": "greeting",
            "current_product": None,
            "product_orders": [],
            "delivery_time": None,
            "selected_farmer": None,
            "conversation": conversation.copy()
        }
    
    session = session_states[client_id]

    detected_language = detect_language(user_input)
    if detected_language != "english":
        session["current_language"] = detected_language
    
    state_info = ""
    
    if session["current_state"] == "greeting":
        detected_products = detect_products(user_input, session["current_language"])
        if detected_products:
            response, product = process_order_request(user_input, session["current_language"], client_id)
            session["current_product"] = product
            session["current_state"] = "quantity_selection" if product else "product_selection"
        else:
            session["current_state"] = "product_selection"
            state_info = "Please tell me what product you'd like to order."
    
    elif session["current_state"] == "product_selection":
        response, product = process_order_request(user_input, session["current_language"], client_id)
        session["current_product"] = product
        if product:
            session["current_state"] = "quantity_selection"
        else:
            state_info = "Still in product selection."
    
    elif session["current_state"] == "quantity_selection":
        quantity = extract_quantity(user_input, session["current_language"])
        
        if quantity > 0 and session["current_product"]:
            available_farmers = check_stock(session["current_product"]["id"], quantity)
            
            if available_farmers:
                session["product_orders"].append({
                    "product_id": session["current_product"]["id"],
                    "product_name": session["current_product"]["name"],
                    "quantity": quantity,
                    "available_farmers": available_farmers
                })
                session["current_state"] = "more_products"
                
                if session["current_language"] == "french":
                    state_info = f"Quantité de {quantity}kg pour {session['current_product']['name']} ajoutée."
                elif session["current_language"] == "arabic":
                    state_info = f"تمت إضافة كمية {quantity} كيلوغرام من {session['current_product']['name']}."
                else:
                    state_info = f"Added {quantity}kg of {session['current_product']['name']}."
            else:
                if session["current_language"] == "french":
                    state_info = f"Quantité non disponible pour {session['current_product']['name']}."
                elif session["current_language"] == "arabic":
                    state_info = f"الكمية غير متوفرة لـ {session['current_product']['name']}."
                else:
                    state_info = f"Quantity not available for {session['current_product']['name']}."
    
    elif session["current_state"] == "more_products":
        if any(word in user_input.lower() for word in ["oui", "yes", "نعم", "أجل"]):
            session["current_state"] = "product_selection"
            session["current_product"] = None
        else:
            session["current_state"] = "delivery_time"
    
    elif session["current_state"] == "delivery_time":
        if any(word in user_input.lower() for word in ["aujourd", "today", "اليوم"]):
            time_preference = "today"
        else:
            time_preference = "tomorrow"
            
        if any(word in user_input.lower() for word in ["matin", "morning", "صباح"]):
            day_part = "morning"
        else:
            day_part = "evening"
            
        session["delivery_time"] = f"{time_preference}_{day_part}"
        session["current_state"] = "farmer_selection"
        
        if session["product_orders"]:
            first_order = session["product_orders"][0]
            best_farmers = find_best_farmers(
                first_order["product_id"], 
                first_order["quantity"], 
                client_id
            )
            
            if best_farmers:
                if session["current_language"] == "french":
                    farmer_options = "\n".join([
                        f"{i+1}. {f['name']} - {f['price']}dh/kg, {round(f['distance'], 2)}km, Note: {f['feedback']}/5"
                        for i, f in enumerate(best_farmers)
                    ])
                    state_info = f"Veuillez choisir un agriculteur:\n{farmer_options}"
                elif session["current_language"] == "arabic":
                    farmer_options = "\n".join([
                        f"{i+1}. {f['name']} - {f['price']}درهم/كجم, {round(f['distance'], 2)}كم, تقييم: {f['feedback']}/5"
                        for i, f in enumerate(best_farmers)
                    ])
                    state_info = f"يرجى اختيار مزارع:\n{farmer_options}"
                else:
                    farmer_options = "\n".join([
                        f"{i+1}. {f['name']} - {f['price']}dh/kg, {round(f['distance'], 2)}km, Rating: {f['feedback']}/5"
                        for i, f in enumerate(best_farmers)
                    ])
                    state_info = f"Please choose a farmer:\n{farmer_options}"
                
                session["available_farmers"] = best_farmers
    
    elif session["current_state"] == "farmer_selection":
        try:
            selected_num = int(re.search(r'(\d+)', user_input).group(1))
            if 1 <= selected_num <= len(session["available_farmers"]):
                selected_farmer = session["available_farmers"][selected_num - 1]
                session["selected_farmer"] = selected_farmer["id"]
                session["current_state"] = "order_confirmation"
                
                products_summary = []
                for po in session["product_orders"]:
                    products_summary.append(f"{po['product_name']}: {po['quantity']}kg")
                
                if session["current_language"] == "french":
                    state_info = f"Récapitulatif de commande:\n" \
                                f"Produits: {', '.join(products_summary)}\n" \
                                f"Agriculteur: {selected_farmer['name']}\n" \
                                f"Livraison: {session['delivery_time'].replace('_', ' ')}\n" \
                                f"Veuillez confirmer (oui/non)"
                elif session["current_language"] == "arabic":
                    state_info = f"ملخص الطلب:\n" \
                                f"المنتجات: {', '.join(products_summary)}\n" \
                                f"المزارع: {selected_farmer['name']}\n" \
                                f"وقت التسليم: {session['delivery_time'].replace('_', ' ')}\n" \
                                f"يرجى التأكيد (نعم/لا)"
                else:
                    state_info = f"Order summary:\n" \
                                f"Products: {', '.join(products_summary)}\n" \
                                f"Farmer: {selected_farmer['name']}\n" \
                                f"Delivery time: {session['delivery_time'].replace('_', ' ')}\n" \
                                f"Please confirm (yes/no)"
        except:
            if session["current_language"] == "french":
                state_info = "Sélection non valide. Veuillez choisir un numéro."
            elif session["current_language"] == "arabic":
                state_info = "اختيار غير صالح. يرجى اختيار رقم."
            else:
                state_info = "Invalid selection. Please choose a number."
    
    elif session["current_state"] == "order_confirmation":
        if any(word in user_input.lower() for word in ["oui", "yes", "نعم", "أجل"]):
            order_saved = save_order(
                client_id, 
                session["product_orders"], 
                session["selected_farmer"], 
                session["delivery_time"]
            )
            
            if order_saved:
                current_language = session["current_language"]
                session.clear()
                session["current_language"] = current_language
                session["current_state"] = "greeting"
                session["product_orders"] = []
                session["conversation"] = conversation.copy()
                
                if session["current_language"] == "french":
                    state_info = "Commande confirmée avec succès! Souhaitez-vous commander autre chose?"
                elif session["current_language"] == "arabic":
                    state_info = "تم تأكيد الطلب بنجاح! هل ترغب في طلب شيء آخر؟"
                else:
                    state_info = "Order confirmed successfully! Would you like to order something else?"
            else:
                if session["current_language"] == "french":
                    state_info = "Erreur lors de l'enregistrement de la commande. Veuillez réessayer."
                elif session["current_language"] == "arabic":
                    state_info = "خطأ في حفظ الطلب. يرجى المحاولة مرة أخرى."
                else:
                    state_info = "Error saving the order. Please try again."
        else:
            if session["current_language"] == "french":
                state_info = "Commande annulée. Que souhaitez-vous faire maintenant?"
            elif session["current_language"] == "arabic":
                state_info = "تم إلغاء الطلب. ماذا تريد أن تفعل الآن؟"
            else:
                state_info = "Order canceled. What would you like to do now?"
            
            session["current_state"] = "greeting"
    
    if session["product_orders"]:
        products_summary = []
        for po in session["product_orders"]:
            products_summary.append(f"{po['product_name']}: {po['quantity']}kg")
        
        lang = session["current_language"]
        if lang == "french":
            state_info += f"\nProduits commandés: {', '.join(products_summary)}"
        elif lang == "arabic":
            state_info += f"\nالمنتجات المطلوبة: {', '.join(products_summary)}"
        else:
            state_info += f"\nOrdered products: {', '.join(products_summary)}"
    
    session["conversation"].append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=f"{user_input}\n\nCONTEXT: {state_info}")]
        )
    )
    
    response = client.models.generate_content(
        model=model,
        contents=session["conversation"],
        config=types.GenerateContentConfig(
            temperature=1,
            top_p=0.95,
            top_k=40,
            max_output_tokens=1024,
            system_instruction=system_instruction
        )
    )
    
    session["conversation"].append(
        types.Content(
            role="model",
            parts=[types.Part.from_text(text=response.text)]
        )
    )
    
    order_details = extract_order_details(session_states[client_id])
    print_order_summary(order_details)

    return response.text, session["current_state"], len(detect_products(user_input, session["current_language"])), len(session["product_orders"])

if __name__ == "__main__":
    print("Chatbot initialized. Type 'exit' to quit.")
    client_id = 1
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'exit':
            break
            
        response, state, products_count, orders_count = run_chatbot_message(user_input, "french", client_id)
        print(f"\nBot: {response}")
        print(f"Debug - State: {state}, Detected Products: {products_count}, Orders: {orders_count}")