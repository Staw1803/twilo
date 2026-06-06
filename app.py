import sys
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
from groq import Groq
import requests

app = Flask(__name__)

# CONFIGURAÇÕES (Seus dados ativos do Twilio + IA Groq)
ACCOUNT_SID = 'ACa290536a8629089fbebd1d00faa9f605'
AUTH_TOKEN = 'd7267c4849fc1f1ea1a96e2283553f42'
NUMERO_TWILIO = '+16189964461'
MEU_NUMERO_CELULAR = '+5592981233982'
GROQ_API_KEY = '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' # Sua chave ativa do Groq

# Inicialização dos Clientes
client = Client(ACCOUNT_SID, AUTH_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)

# FUNÇÃO AUXILIAR: Consulta a API de mapas real (OpenStreetMap) filtrada para Manaus
def consultar_mapa_manaus(local_texto):
    url = "https://nominatim.openstreetmap.org/search"
    headers = {'User-Agent': 'ArboAssistant/1.0 (jader@evo.com)'}
    params = {
        'q': f"{local_texto}, Manaus",
        'format': 'json',
        'limit': 1,
        'addressdetails': 1
    }
    try:
        response = requests.get(url, params=params, headers=headers, timeout=4)
        if response.status_code == 200 and response.json():
            dados = response.json()[0]
            endereco = dados.get('display_name', '')
            return f" [Informação Real do Mapa de Manaus: Esse local se encontra em: {endereco}]"
    except Exception as e:
        print(f"[ERRO API MAPA] {e}", file=sys.stderr)
    return ""

@app.route("/")
def home():
    return "Arbo Sistema Geográfico Ativo no Render!"

# 1. O DISPARADOR
@app.route("/trigger", methods=['GET', 'POST'])
def trigger_call():
    try:
        client.calls.create(
            url='https://twilo-eqee.onrender.com/voice',
            to=MEU_NUMERO_CELULAR,
            from_=NUMERO_TWILIO,
            timeout=60
        )
        return "Chamada disparada com sucesso via Render!", 200
    except Exception as e:
        return f"Erro ao disparar: {e}", 500

# 2. O ATENDIMENTO INICIAL
@app.route("/voice", methods=['GET', 'POST'])
def voice():
    response = VoiceResponse()
    LINK_PROCESS = 'https://twilo-eqee.onrender.com/process'
    gather = response.gather(input='speech', action=LINK_PROCESS, language='pt-BR', speech_timeout='auto')
    gather.say("Arbo sistema online. Pode falar, estou te ouvindo.", language='pt-BR', voice="Polly.Vitoria")
    return str(response), 200, {'Content-Type': 'text/xml'}

# 3. O CÉREBRO COM CONSULTA EM API DE MAPAS
@app.route("/process", methods=['GET', 'POST'])
def process():
    user_speech = request.form.get('SpeechResult')
    response = VoiceResponse()
    LINK_PROCESS = 'https://twilo-eqee.onrender.com/process'

    if not user_speech:
        gather = response.gather(input='speech', action=LINK_PROCESS, language='pt-BR', speech_timeout='auto')
        return str(response), 200, {'Content-Type': 'text/xml'}

    fala_usuario = user_speech.lower()
    if any(cmd in fala_usuario for cmd in ["pode desligar", "tchau", "desliga", "encerrar a chamada"]):
        response.say("Entendido. Fechando conexão. Até mais!", language='pt-BR', voice="Polly.Vitoria")
        response.hangup()
        return str(response), 200, {'Content-Type': 'text/xml'}

    contexto_mapa = ""
    try:
        # PASSO 1: Passo ultra rápido pela IA para extrair se há locais na frase
        extracao = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Identifique se o usuário citou algum lugar, rua, bairro ou ponto turístico. Se sim, responda APENAS com o nome do local isolado. Se não houver local, responda NENHUM."},
                {"role": "user", "content": user_speech}
            ],
            temperature=0.0,
            max_tokens=30
        )
        local_detectado = extracao.choices[0].message.content.strip()
        
        # PASSO 2: Se ela achou um local, nós batemos na API de mapas real
        if "NENHUM" not in local_detectado.upper() and len(local_detectado) > 2:
            print(f"[MAPA LOG] Buscando coordenadas para: {local_detectado}", file=sys.stderr)
            contexto_mapa = consultar_mapa_manaus(local_detectado)
    except Exception as e:
        print(f"[ERRO AGENTE EXTRAÇÃO] {e}", file=sys.stderr)

    try:
        # PASSO 3: Resposta final combinando a pergunta do usuário com o dado real da API de Mapas
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "Você é o copiloto de inteligência do sistema Arbo. O usuário está em MANAUS, AMAZONAS. "
                        "Use as informações reais fornecidas pela API de mapas anexadas à pergunta para se orientar geograficamente. "
                        "Seja extremamente inteligente, natural e prestativo. Responda de forma curta, conversacional e direta (máximo duas frases)."
                    )
                },
                {
                    "role": "user", 
                    "content": f"{user_speech} {contexto_mapa}"
                }
            ],
            temperature=0.2,
            max_tokens=200
        )
        ia_resposta = completion.choices[0].message.content
    except Exception as e:
        print(f"[ERRO GROQ FINAL] {e}", file=sys.stderr)
        ia_resposta = "Deu um pequeno estalo na linha. Pode repetir?"

    # Vitória fala com os dados blindados da API de mapas
    gather = response.gather(input='speech', action=LINK_PROCESS, language='pt-BR', speech_timeout='auto')
    gather.say(ia_resposta, language='pt-BR', voice="Polly.Vitoria")
    
    return str(response), 200, {'Content-Type': 'text/xml'}
