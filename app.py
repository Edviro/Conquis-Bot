from flask import Flask, request, jsonify
import os
import requests
import json

# Crear la aplicación Flask
app = Flask(__name__)

# Variables de entorno
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN', 'default_token')
ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN', '')

print("=== CONFIGURACIÓN INICIAL ===")
print(f"VERIFY_TOKEN: {VERIFY_TOKEN}")
print(f"ACCESS_TOKEN configurado: {'Sí' if ACCESS_TOKEN else 'No'}")

@app.route('/')
def home():
    return jsonify({
        "status": "success",
        "message": "ConquisBot está funcionando correctamente!",
        "webhook_endpoint": "/webhook"
    })

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    print("=== VERIFICANDO WEBHOOK ===")
    
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    print(f"Mode: {mode}")
    print(f"Token recibido: {token}")
    print(f"Challenge: {challenge}")
    
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        print("✅ Webhook verificado!")
        return challenge
    else:
        print("❌ Verificación fallida")
        return "Forbidden", 403

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    print("=== WEBHOOK POST RECIBIDO ===")
    
    try:
        data = request.get_json()
        print("Datos recibidos:", json.dumps(data, indent=2))
        
        if data.get('object') == 'whatsapp_business_account':
            entries = data.get('entry', [])
            
            for entry in entries:
                changes = entry.get('changes', [])
                
                for change in changes:
                    if change.get('field') == 'messages':
                        process_messages(change.get('value', {}))
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

def process_messages(value):
    messages = value.get('messages', [])
    phone_number_id = value.get('metadata', {}).get('phone_number_id')
    
    for message in messages:
        sender = message.get('from')
        message_type = message.get('type')
        
        if message_type == 'text':
            text_body = message.get('text', {}).get('body', '')
            print(f"Mensaje de {sender}: {text_body}")
            
            # Respuesta simple
            response = f"Hola! Recibí tu mensaje: {text_body}"
            send_message(phone_number_id, sender, response)

def send_message(phone_number_id, to_number, message_text):
    if not ACCESS_TOKEN or not phone_number_id:
        print("❌ Faltan ACCESS_TOKEN o phone_number_id")
        return
    
    url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
    
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    data = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message_text}
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            print(f"✅ Mensaje enviado a {to_number}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error enviando: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Iniciando servidor en puerto {port}")
    app.run(host='0.0.0.0', port=port, debug=False)