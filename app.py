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

app = Flask(__name__)

# =====================================================================
# CONFIGURAÇÕES DO ECOSSISTEMA (ALTERADO PARA RITMO ACELERADO)
# =====================================================================
ATIVAR_LIGACOES_AUTOMATICAS = True # Vira True para o loop rodar sozinho ao ligar o app
INTERVALO_MINUTOS = 2              # Tempo entre o fim de uma chamada e o disparo da próxima
TIMEOUT_SEGUNDOS = 7               # Janela estrita de 7 segundos para evitar a caixa postal

# --- TWILIO ---


NUMERO_TWILIO = '+16189964461'
MEU_NUMERO_CELULAR = '5592981233982'

# --- VONAGE ---



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

SUPABASE_URL = 'https://gzekubsjpcgrxgomoriy.supabase.co'

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

def calcular_estimativa_transporte(destino_texto):
    lat_origem, lon_origem = -3.1190275, -60.0217314 
    url_busca = "https://nominatim.openstreetmap.org/search"
    params = {'q': f"{destino_texto}, Manaus, Amazonas", 'format': 'json', 'limit': 1}
    try:
        resp = requests.get(url_busca, params=params, headers={'User-Agent': 'AssistenteVoz/1.0'}, timeout=4)
        if resp.status_code == 200 and resp.json():
            local_dados = resp.json()[0]
            lat_destino = float(local_dados['lat'])
            lon_destino = float(local_dados['lon'])
            nome_completo = local_dados.get('display_name', '')
            rad = math.pi / 180
            dlat = (lat_destino - lat_origem) * rad
            dlon = (lon_destino - lon_origem) * rad
            a = math.sin(dlat/2)**2 + math.cos(lat_origem*rad) * math.cos(lat_destino*rad) * math.sin(dlon/2)**2
            distancia_km = 2 * 6371 * math.asin(math.sqrt(a))
            distancia_real_aprox = distancia_km * 1.3
            tarifa_base = 4.50
            custo_por_km = 2.10
            tempo_estimado_minutos = distancia_real_aprox * 2.5 
            custo_por_minuto = 0.25
            preco_final = tarifa_base + (distancia_real_aprox * custo_por_km) + (tempo_estimado_minutos * custo_por_minuto)
            if preco_final < 8.00: preco_final = 8.00
            return f" [Transporte: Destino encontrado: {nome_completo}. Distância aprox: {distancia_real_aprox:.1f}km. Preço estimado UberX/99: R$ {preco_final:.2f}]"
    except Exception as e:
        print(f"[ERRO TRANSPORTE] {e}", file=sys.stderr)
    return " [Transporte: Não foi possível calcular a rota para esse destino no momento]"

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
# ROTAS DO SERVIDOR WEB E DISPAROS
# =====================================================================
def disparar_ligacao_assistente():
    try:
        # O parâmetro timeout define quantos segundos o Twilio deixa chamando antes de desistir
        client_twilio.calls.create(
            url='https://twilo-eqee.onrender.com/twilio/voice', 
            to='+' + MEU_NUMERO_CELULAR, 
            from_=NUMERO_TWILIO, 
            timeout=TIMEOUT_SEGUNDOS
        )
        return "Chamada disparada via Twilio!"
    except Exception as e_twilio:
        try:
            # O ringing_timer faz exatamente a mesma coisa na infraestrutura da Vonage
            vonage_voice.create_call({
                'to': [{'type': 'phone', 'number': MEU_NUMERO_CELULAR}], 
                'from': {'type': 'phone', 'number': VONAGE_NUMERO_ORIGEM}, 
                'answer_url': ['https://twilo-eqee.onrender.com/vonage/voice'], 
                'ringing_timer': TIMEOUT_SEGUNDOS
            })
            return "Chamada disparada via Vonage!"
        except Exception as e_vonage:
            return f"Erro Crítico: {e_vonage}"

@app.route("/trigger", methods=['GET', 'POST'])
def trigger_call_route():
    return disparar_ligacao_assistente(), 200

@app.route("/twilio/voice", methods=['GET', 'POST'])
def twilio_voice():
    response = VoiceResponse()
    response.gather(input='speech', action='https://twilo-eqee.onrender.com/process?provider=twilio', language='pt-BR', speech_timeout='auto').say("Conexão estabelecida. Pode falar.", language='pt-BR', voice="Polly.Vitoria")
    return str(response), 200, {'Content-Type': 'text/xml'}

@app.route("/vonage/voice", methods=['GET', 'POST'])
def vonage_voice_input():
    return jsonify([{"action": "talk", "text": "Conexão estabelecida. Pode falar.", "language": "pt-BR", "bargeIn": True}, {"action": "input", "type": ["speech"], "speech": {"language": "pt-BR", "endOnSilence": 1.5}, "eventUrl": ["https://twilo-eqee.onrender.com/process?provider=vonage"]}]), 200

# =====================================================================
# O CÉREBRO UNIFICADO (PROCESSAMENTO DAS APIS)
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
    if any(cmd in fala_usuario for cmd in ["desligar", "tchau", "desliga", "encerrar"]):
        return encerrar_chamada(provedor)

    contexto_extra = ""
    try:
        extracao = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system", 
                    "content": "Responda ESTRITAMENTE: WHATSAPP: [ENVIAR ou NENHUM] | PARA: [nome ou NENHUM] | TXT: [mensagem ou NENHUM] | UBER: [Nome do destino final ou NENHUM] | BUSCA: [Assunto para pesquisar na web ou NENHUM]"
                },
                {"role": "user", "content": user_speech}
            ],
            temperature=0.0,
            max_tokens=100
        )
        dados_extraidos = extracao.choices[0].message.content.strip()
        partes = {p.split(":")[0].strip(): p.split(":")[1].strip() for p in dados_extraidos.split("|") if ":" in p}
        
        if partes.get("UBER") and partes.get("UBER") != "NENHUM":
            contexto_extra += calcular_estimativa_transporte(partes.get("UBER"))
            
        if partes.get("WHATSAPP") == "ENVIAR" and partes.get("PARA") != "NENHUM":
            supabase.table("whatsapp_comandos").insert({"destinatario": partes.get("PARA"), "mensagem": partes.get("TXT")}).execute()
            contexto_extra += f" [SISTEMA: Mensagem enviada para {partes.get('PARA')}.]"
            
        if partes.get("BUSCA") and partes.get("BUSCA") != "NENHUM":
            contexto_extra += buscar_na_internet(partes.get("BUSCA"))
                
    except Exception as e:
        print(f"[ERRO PARSER] {e}", file=sys.stderr)

    prompt_sistema = (
        "Você é uma inteligência artificial avançada operando em formato de chamada telefônica. O ano é 2026. "
        "Você está localizada em Manaus, Amazonas. Se o contexto contiver dados de 'Transporte', use essas informações "
        "para informar o preço estimado da corrida e a distância de forma natural, arredondando os valores para soar humano. "
        "Seja extremamente direto, claro e responda em no máximo duas frases curtas."
    )

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": f"Fala do usuário: '{user_speech}'. Dados injetados pelo sistema: {contexto_extra}"}
            ],
            temperature=0.4,
            max_tokens=150
        )
        ia_resposta = completion.choices[0].message.content
    except Exception:
        ia_resposta = "Houve uma oscilação na rede. Pode repetir?"

    return responder_usuario(provedor, ia_resposta)

def reabrir_microfone(provedor):
    if provedor == 'vonage': return jsonify([{"action": "input", "type": ["speech"], "speech": {"language": "pt-BR"}, "eventUrl": ["https://twilo-eqee.onrender.com/process?provider=vonage"]}]), 200
    r = VoiceResponse(); r.gather(input='speech', action='https://twilo-eqee.onrender.com/process?provider=twilio', language='pt-BR'); return str(r), 200, {'Content-Type': 'text/xml'}

def encerrar_chamada(provedor):
    if provedor == 'vonage': return jsonify([{"action": "talk", "text": "Conexão encerrada.", "language": "pt-BR"}, {"action": "hangup"}]), 200
    r = VoiceResponse(); r.say("Conexão encerrada.", language='pt-BR'); r.hangup(); return str(r), 200, {'Content-Type': 'text/xml'}

def responder_usuario(provedor, texto):
    if provedor == 'vonage': return jsonify([{"action": "talk", "text": texto, "language": "pt-BR", "bargeIn": True}, {"action": "input", "type": ["speech"], "speech": {"language": "pt-BR", "endOnSilence": 1.5}, "eventUrl": ["https://twilo-eqee.onrender.com/process?provider=vonage"]}]), 200
    r = VoiceResponse(); g = r.gather(input='speech', action='https://twilo-eqee.onrender.com/process?provider=twilio', language='pt-BR'); g.say(texto, language='pt-BR', voice="Polly.Vitoria"); return str(r), 200, {'Content-Type': 'text/xml'}

# =====================================================================
# LOOP SÍNCRONO EM SEGUNDO PLANO (THREAD AUTOMÁTICA)
# =====================================================================
def loop_de_ligacoes():
    while ATIVAR_LIGACOES_AUTOMATICAS:
        disparar_ligacao_assistente()
        # O sleep agora calcula o intervalo com base nos 2 minutos configurados
        time.sleep(INTERVALO_MINUTOS * 60)

# Dispara a Thread em paralelo para o Flask rodar sem travar a porta 5000
if ATIVAR_LIGACOES_AUTOMATICAS:
    threading.Thread(target=loop_de_ligacoes, daemon=True).start()

if __name__ == "__main__":
    app.run(port=5000, debug=True)
