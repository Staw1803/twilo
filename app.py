import os
import sys
import threading
import time
import math
from flask import Flask, request, jsonify
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client as TwilioClient
from groq import Groq
import requests
from duckduckgo_search import DDGS
from supabase import create_client, Client as SupabaseClient
import vonage
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env (se local) ou do ambiente (Render)
load_dotenv()

app = Flask(__name__)

# --- CONFIGURAÇÕES ---
ATIVAR_LIGACOES_AUTOMATICAS = True
INTERVALO_MINUTOS = 2
TIMEOUT_SEGUNDOS = 7

# --- CREDENCIAIS SEGURAS (Puxadas do Render/Env) ---
TWILIO_SID = os.getenv('TWILIO_SID')
TWILIO_TOKEN = os.getenv('TWILIO_TOKEN')
NUMERO_TWILIO = os.getenv('NUMERO_TWILIO')
MEU_NUMERO_CELULAR = os.getenv('MEU_NUMERO_CELULAR')

VONAGE_API_SECRET = os.getenv('VONAGE_API_SECRET')
VONAGE_APP_ID = os.getenv('VONAGE_APP_ID')
VONAGE_NUMERO_ORIGEM = os.getenv('VONAGE_NUMERO_ORIGEM')
VONAGE_PRIVATE_KEY = os.getenv('VONAGE_PRIVATE_KEY')

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# --- INICIALIZAÇÃO ---
client_twilio = TwilioClient(TWILIO_SID, TWILIO_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)
supabase: SupabaseClient = create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    vonage_client = vonage.Client(application_id=VONAGE_APP_ID, private_key=VONAGE_PRIVATE_KEY)
    vonage_voice = vonage.Voice(vonage_client)
except Exception as e:
    print(f"[AVISO VONAGE] Configurações pendentes: {e}", file=sys.stderr)

# --- FERRAMENTAS ---
def calcular_estimativa_transporte(destino_texto):
    lat_origem, lon_origem = -3.1190275, -60.0217314 
    url_busca = "https://nominatim.openstreetmap.org/search"
    params = {'q': f"{destino_texto}, Manaus, Amazonas", 'format': 'json', 'limit': 1}
    try:
        resp = requests.get(url_busca, params=params, headers={'User-Agent': 'ArboBot/1.0'}, timeout=4)
        if resp.status_code == 200 and resp.json():
            local = resp.json()[0]
            lat_d, lon_d = float(local['lat']), float(local['lon'])
            rad = math.pi / 180
            dlat, dlon = (lat_d - lat_origem) * rad, (lon_d - lon_origem) * rad
            a = math.sin(dlat/2)**2 + math.cos(lat_origem*rad) * math.cos(lat_d*rad) * math.sin(dlon/2)**2
            dist = (2 * 6371 * math.asin(math.sqrt(a))) * 1.3
            preco = max(8.00, 4.50 + (dist * 2.10) + ((dist * 2.5) * 0.25))
            return f" [Transporte: Destino: {local.get('display_name')}. Dist: {dist:.1f}km. Preço aprox: R$ {preco:.2f}]"
    except Exception as e:
        print(f"[ERRO TRANSPORTE] {e}", file=sys.stderr)
    return ""

def buscar_na_internet(termo):
    try:
        with DDGS() as ddgs:
            res = [r['body'] for r in ddgs.text(termo, max_results=2)]
            return f" [Internet: {' | '.join(res)}]"
    except:
        return ""

# --- ROTAS ---
@app.route("/twilio/voice", methods=['POST'])
def twilio_voice():
    r = VoiceResponse()
    r.gather(input='speech', action='https://twilo-eqee.onrender.com/process?provider=twilio', language='pt-BR').say("Conexão estabelecida.", language='pt-BR', voice="Polly.Vitoria")
    return str(r), 200, {'Content-Type': 'text/xml'}

@app.route("/process", methods=['POST'])
def process():
    p = request.args.get('provider')
    user_speech = request.form.get('SpeechResult') if p == 'twilio' else request.get_json().get('speech', {}).get('results', [{}])[0].get('text', '')
    
    if not user_speech: return responder_usuario(p, "Pode repetir?")
    
    ctx = ""
    try:
        ext = groq_client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "system", "content": "Extraia comandos: WHATSAPP:[ENVIAR/NENHUM]|PARA:[nome]|TXT:[msg]|UBER:[destino]|BUSCA:[termo]"}, {"role": "user", "content": user_speech}], temperature=0)
        partes = {line.split(":")[0].strip(): line.split(":")[1].strip() for line in ext.choices[0].message.content.split("|") if ":" in line}
        
        if partes.get("UBER") != "NENHUM": ctx += calcular_estimativa_transporte(partes["UBER"])
        if partes.get("BUSCA") != "NENHUM": ctx += buscar_na_internet(partes["BUSCA"])
    except: pass

    res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "system", "content": "Seja breve. Ano 2026. Manaus."}, {"role": "user", "content": f"Usuario: {user_speech}. Contexto: {ctx}"}])
    return responder_usuario(p, res.choices[0].message.content)

def responder_usuario(p, txt):
    if p == 'twilio':
        r = VoiceResponse(); g = r.gather(input='speech', action='https://twilo-eqee.onrender.com/process?provider=twilio'); g.say(txt, language='pt-BR'); return str(r), 200, {'Content-Type': 'text/xml'}
    return jsonify([{"action": "talk", "text": txt}, {"action": "input", "type": ["speech"], "eventUrl": ["https://twilo-eqee.onrender.com/process?provider=vonage"]}])

def disparar_ligacao():
    try:
        client_twilio.calls.create(url='https://twilo-eqee.onrender.com/twilio/voice', to='+' + MEU_NUMERO_CELULAR, from_=NUMERO_TWILIO, timeout=TIMEOUT_SEGUNDOS)
    except: pass

def loop():
    while ATIVAR_LIGACOES_AUTOMATICAS:
        disparar_ligacao()
        time.sleep(INTERVALO_MINUTOS * 60)

if ATIVAR_LIGACOES_AUTOMATICAS:
    threading.Thread(target=loop, daemon=True).start()

if __name__ == "__main__":
    app.run(port=5000)
