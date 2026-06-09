import sys
from flask import Flask, request, jsonify
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client as TwilioClient
from groq import Groq
import requests
from duckduckgo_search import DDGS
from supabase import create_client, Client as SupabaseClient
import vonage

app = Flask(__name__)

# =====================================================================
# CONFIGURAÇÕES DO ECOSSISTEMA
# =====================================================================

# --- TWILIO ---
TWILIO_SID = 'ACa290536a8629089fbebd1d00faa9f605'
TWILIO_TOKEN = '785f10ba3e3b1965a2c9f02e9654122a'
NUMERO_TWILIO = '+16189964461'
MEU_NUMERO_CELULAR = '5592981233982'

# --- VONAGE ---
VONAGE_API_SECRET = 'p6t3q(TNAsWE!r8q'
VONAGE_APP_ID = 'b90f5a80-e2f2-405d-a69d-a31e4407206a' 
VONAGE_NUMERO_ORIGEM = '12345678901'

VONAGE_PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDWwewScbUl0rDj
8GSpQqNILiPelv/zj9ajcMP/Y7BIlKL+idSf6Ku5Tp71lDqjGkBzOB6k4qwKJuPj
HkRh78Ov4KeJyxbY3otaWAnar2ZCncC5u+9knQ01le8rc+ZticwGKSsYVuu8KXRM
aZ4LhxcEHmnV5Lrwa22Y1x32lR1+sBUU+T+saR8tlQo+30hHOUDEDSZbYjXp8pSi
UxcvS66tUCaKTQ4j+V7TwLvILjd5UPx5wmM42Rb1cT152Id5UgC5tV6nFjcWAmBL
yX4tVAHOppSTSuCR0bSC26J7s0FNOhS9eRKFJ6vOrjIDNw6zPDau2VFCOYLOqTpI
+KPqENHPAgMBAAECggEABhA26b+7cpRD7vDplqciqbYLyIwQ2+qSuniY6rarfSZy
glHtO+U7e/bj9rZhqsXh+J7RVqxuWQxcthveUw7hl9n1llFdQBrrFPjpW6WaHdq1
sfNuwIjNR6xdB/1fYyEB2VFY6HiucoM6clyFBs7177rVbXbmGZr0NDLWo2X1uDmT
3wgg7TdcEPE9DmFBLjxSjAWJjIA75DkNOImErOsRoR0p8Cza19B8ddoEVjGIildS
ZLbgpj0Qgd2ufl4Vm8t95/hdU7Lij/JRG8lqqGU2anaYbWnfDCPVRat3bUQnrqQ1
1SX1NXD3I1bDQ32gPFmxVsTWwJg8UECMm99EL5pusQKBgQD6uWGe/QqIhrSZLHlN
jNzjtBMl3ScWCXZd44pwr6Q6G2SxruHvfiywGbdvF2eZ8oKYCi6Oh2eXaWEuHcpm
ynXxyMcOiDfTot4jQfaPXTYgNT7bmpIOzJEIFnnpd4Qre01aOmsLEU1brw69B6ZW
f2ovMqc0UqpZz4OIsVAyGFn49wKBgQDbRssOB15pOus7xC+HaWaKHjcfEFy8edW2
mDgiQ7yAZaEPrH/HKWuc1RZqxr7zUrZPN3XxOViVaqW1bE0JIi+2GbUtkc+kCbui
tr09+iXiwDwcN0MziepgTjXxjDJ1fxyr72ofhFbAPW3ANj4RcZUDId9aByxXpYNg
0/OEMS9P6QKBgQDQucnyUNgXBoWMywCFNhKiIcSbDfw/FUuMKCSVYTOICEwQu/Vt
qo3LYO1bt5FRERn1NuzBTSpJW7pCaRyZ7Ey6J5rHl1Fah8kEcyKvATtRHuKgcZLM
bTMEF6oQWaYXiMPBrMZ2ZUYQYLEVXyvz8IjWmAWownT85YusHWkU+z7TywKBgHax
nGqMnJNTnE+uw5eF+0ZaUrYS8k/nl0KOpRwPFHNgD83fLw+MoT60rbzAtk4aAKti
twoLY6MFpotNA2olQjRNOCBhpEcEKbhLOKbayDU0n5UaaNr2FZNp4pNMs2ecldWP
9B75UMgguE7qTbC9jc6zQCaIaX1MD5CTSmbNBPI5AoGBAKKQAGVjtYdMNQM9ILkL
pMsfTVHwkza7xhl4AFPBvLroXGo0WFHyHPE1dIGsLxv8vvKl5opL3c2AdUXJR0+3
BI79sqq42gvhMIYkB00SyVeQ+Ci5EtrxAdmxFmG8kktnDG9jHjPVV8vkMDmH8LLw
y6DuGldnMmCOdpXpm3Umc99O
-----END PRIVATE KEY-----"""

# --- GROQ & SUPABASE ---
GROQ_API_KEY = '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'
SUPABASE_URL = 'https://gzekubsjpcgrxgomoriy.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd6ZWt1YnNqcGNncnhnb21vcml5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA4NzA3NDgsImV4cCI6MjA5NjQ0Njc0OH0.AxMl-aczglJgazwCyMZtQc191vVGjxhSiR98jUmBdAU'

# =====================================================================
# INICIALIZAÇÃO E FERRAMENTAS DE INTELIGÊNCIA
# =====================================================================
client_twilio = TwilioClient(TWILIO_SID, TWILIO_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)
supabase: SupabaseClient = create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    vonage_client = vonage.Client(application_id=VONAGE_APP_ID, private_key=VONAGE_PRIVATE_KEY)
    vonage_voice = vonage.Voice(vonage_client)
except Exception as e:
    print(f"[AVISO VONAGE] Configurações pendentes: {e}", file=sys.stderr)

# FERRAMENTA 1: GPS Manaus
def consultar_mapa_manaus(local_texto):
    url = "https://nominatim.openstreetmap.org/search"
    params = {'q': f"{local_texto}, Manaus, Amazonas", 'format': 'json', 'limit': 1}
    try:
        resp = requests.get(url, params=params, headers={'User-Agent': 'Arbo/1.0'}, timeout=4)
        if resp.status_code == 200 and resp.json():
            return f" [Mapa: {resp.json()[0].get('display_name', '')}]"
    except:
        pass
    return " [Mapa: Local não encontrado com precisão]"

# FERRAMENTA 2: Internet em Tempo Real
def buscar_na_internet(termo_busca):
    try:
        with DDGS() as ddgs:
            resultados = [r['body'] for r in ddgs.text(termo_busca, max_results=2)]
            if resultados:
                return f" [Internet Real-Time: {' | '.join(resultados)}]"
    except:
        pass
    return " [Internet: Falha na busca]"

# =====================================================================
# ROTAS DE GATILHO E VOZ
# =====================================================================
@app.route("/trigger", methods=['GET', 'POST'])
def trigger_call():
    try:
        client_twilio.calls.create(url='https://twilo-eqee.onrender.com/twilio/voice', to='+' + MEU_NUMERO_CELULAR, from_=NUMERO_TWILIO, timeout=60)
        return "Chamada disparada via Twilio!", 200
    except Exception as e_twilio:
        print(f"[FAILOVER] Twilio sem saldo. Erro: {e_twilio}. Tentando Vonage...", file=sys.stderr)
        try:
            vonage_voice.create_call({'to': [{'type': 'phone', 'number': MEU_NUMERO_CELULAR}], 'from': {'type': 'phone', 'number': VONAGE_NUMERO_ORIGEM}, 'answer_url': ['https://twilo-eqee.onrender.com/vonage/voice']})
            return "Chamada disparada via Vonage com sucesso!", 200
        except Exception as e_vonage:
            return f"Erro Crítico nos dois provedores: {e_vonage}", 500

@app.route("/twilio/voice", methods=['GET', 'POST'])
def twilio_voice():
    response = VoiceResponse()
    response.gather(input='speech', action='https://twilo-eqee.onrender.com/process?provider=twilio', language='pt-BR', speech_timeout='auto').say("Arbo online. Pode falar.", language='pt-BR', voice="Polly.Vitoria")
    return str(response), 200, {'Content-Type': 'text/xml'}

@app.route("/vonage/voice", methods=['GET', 'POST'])
def vonage_voice_input():
    return jsonify([{"action": "talk", "text": "Arbo online. Pode falar.", "language": "pt-BR", "bargeIn": True}, {"action": "input", "type": ["speech"], "speech": {"language": "pt-BR", "endOnSilence": 1.5}, "eventUrl": ["https://twilo-eqee.onrender.com/process?provider=vonage"]}]), 200

# =====================================================================
# O CÉREBRO UNIFICADO
# =====================================================================
@app.route("/process", methods=['GET', 'POST'])
def process():
    provedor = request.args.get('provider', 'twilio')
    
    if provedor == 'vonage':
        dados_vonage = request.get_json() or {}
        speech_results = dados_vonage.get('speech', {}).get('results', [])
        user_speech = speech_results[0].get('text', '') if speech_results else ''
    else:
        user_speech = request.form.get('SpeechResult', '')

    if not user_speech:
        return reabrir_microfone(provedor)

    fala_usuario = user_speech.lower()
    if any(cmd in fala_usuario for cmd in ["desligar", "tchau", "desliga"]):
        return encerrar_chamada(provedor)

    contexto_extra = ""
    try:
        # PARSER DE INTENÇÕES (8B) - Agora detecta locais e buscas na internet
        extracao = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system", 
                    "content": "Responda ESTRITAMENTE: WHATSAPP: [ENVIAR ou NENHUM] | PARA: [nome ou NENHUM] | TXT: [mensagem ou NENHUM] | LOCAL: [Lugar em Manaus citado ou NENHUM] | BUSCA: [Assunto para pesquisar no google ou NENHUM]"
                },
                {"role": "user", "content": user_speech}
            ],
            temperature=0.0,
            max_tokens=100
        )
        dados_extraidos = extracao.choices[0].message.content.strip()
        partes = {p.split(":")[0].strip(): p.split(":")[1].strip() for p in dados_extraidos.split("|") if ":" in p}
        
        # AÇÃO 1: WhatsApp
        if partes.get("WHATSAPP") == "ENVIAR" and partes.get("PARA") != "NENHUM":
            supabase.table("whatsapp_comandos").insert({"destinatario": partes.get("PARA"), "mensagem": partes.get("TXT")}).execute()
            contexto_extra += f" [SISTEMA: A mensagem para {partes.get('PARA')} foi enviada.]"
            
        # AÇÃO 2: GPS e Mapas
        if partes.get("LOCAL") and partes.get("LOCAL") != "NENHUM":
            contexto_extra += consultar_mapa_manaus(partes.get("LOCAL"))
            
        # AÇÃO 3: Pesquisa no Google/DuckDuckGo
        if partes.get("BUSCA") and partes.get("BUSCA") != "NENHUM":
            contexto_extra += buscar_na_internet(partes.get("BUSCA"))
                
    except Exception as e:
        print(f"[ERRO PARSER] {e}", file=sys.stderr)

    # PROMPT DE PERSONALIDADE (70B)
    prompt_sistema = (
        "Você é o assistente avançado do ecossistema Arbo. O ano é 2026. "
        "Você opera de Manaus, Amazonas, e tem profundo conhecimento da cidade. "
        "Se o usuário fizer uma pergunta e o contexto trouxer dados da 'Internet Real-Time' ou 'Mapa', "
        "use essas informações para dar uma resposta inteligente e atualizada, mas com suas próprias palavras. "
        "Aja de forma muito natural, parecendo um humano conversando. Seja ultra direto, sem enrolação (máximo 2 frases curtas). "
        "Se não souber algo, diga a verdade."
    )

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": f"O que o usuário falou: '{user_speech}'. Dados do sistema: {contexto_extra}"}
            ],
            temperature=0.4,
            max_tokens=150
        )
        ia_resposta = completion.choices[0].message.content
    except Exception:
        ia_resposta = "Tive um pequeno atraso de conexão. Pode repetir?"

    return responder_usuario(provedor, ia_resposta)

# =====================================================================
# FUNÇÕES AUXILIARES DE ADAPTAÇÃO DE SINAL
# =====================================================================
def reabrir_microfone(provedor):
    if provedor == 'vonage': return jsonify([{"action": "input", "type": ["speech"], "speech": {"language": "pt-BR"}, "eventUrl": ["https://twilo-eqee.onrender.com/process?provider=vonage"]}]), 200
    r = VoiceResponse(); r.gather(input='speech', action='https://twilo-eqee.onrender.com/process?provider=twilio', language='pt-BR'); return str(r), 200, {'Content-Type': 'text/xml'}

def encerrar_chamada(provedor):
    if provedor == 'vonage': return jsonify([{"action": "talk", "text": "Conexão encerrada.", "language": "pt-BR"}, {"action": "hangup"}]), 200
    r = VoiceResponse(); r.say("Conexão encerrada.", language='pt-BR'); r.hangup(); return str(r), 200, {'Content-Type': 'text/xml'}

def responder_usuario(provedor, texto):
    if provedor == 'vonage': return jsonify([{"action": "talk", "text": texto, "language": "pt-BR", "bargeIn": True}, {"action": "input", "type": ["speech"], "speech": {"language": "pt-BR", "endOnSilence": 1.5}, "eventUrl": ["https://twilo-eqee.onrender.com/process?provider=vonage"]}]), 200
    r = VoiceResponse(); g = r.gather(input='speech', action='https://twilo-eqee.onrender.com/process?provider=twilio', language='pt-BR'); g.say(texto, language='pt-BR', voice="Polly.Vitoria"); return str(r), 200, {'Content-Type': 'text/xml'}
