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
GROQ_API_KEY = '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' # Garanta que sua chave gsk_ real esteja aqui

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
    return "Arbo com Sistema de Redundância Ativo no Render!"

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

# 3. O CÉREBRO COM REDUNDÂNCIA AUTOMÁTICA
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
        # Extração rápida de localização usando o modelo veloz
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
        
        if "NENHUM" not in local_detectado.upper() and len(local_detectado) > 2:
            contexto_mapa = consultar_mapa_manaus(local_detectado)
    except Exception as e:
        print(f"[ERRO AGENTE EXTRAÇÃO] {e}", file=sys.stderr)

    # Definição das diretrizes da IA
    prompt_sistema = (
        "Você é o copiloto de inteligência avançada do ecossistema Arbo. Seu objetivo é ajudar o usuário "
        "em absolutamente tudo o que ele precisar, agindo com máxima sabedoria, raciocínio lógico aguçado e parceria. "
        "O usuário está na cidade de MANAUS, AMAZONAS. Use os dados geográficos reais anexados à pergunta para se guiar. "
        "Converse de forma natural, fluida e inteligente. Se a pergunta dele exigir uma resposta complexa, explique "
        "de forma clara, mas direta e resumida (máximo de 3 frases) para ficar bom de ouvir pelo telefone."
    )

    ia_resposta = ""
    try:
        # TENTATIVA 1: Modelo Peso Pesado Correto (70B)
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": f"{user_speech} {contexto_mapa}"}
            ],
            temperature=0.4,
            max_tokens=250
        )
        ia_resposta = completion.choices[0].message.content
    except Exception as e70b:
        print(f"[SISTEMA] Recuando para o modelo 8B devido ao erro: {e70b}", file=sys.stderr)
        try:
            # TENTATIVA 2 (FALLBACK): O modelo 8B assume se o grande falhar
            completion = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": prompt_sistema},
                    {"role": "user", "content": f"{user_speech} {contexto_mapa}"}
                ],
                temperature=0.3,
                max_tokens=200
            )
            ia_resposta = completion.choices[0].message.content
        except Exception as e8b:
            print(f"[ERRO CRÍTICO] Falha total nas duas IAs: {e8b}", file=sys.stderr)
            ia_resposta = "Tive um pequeno apagão nas linhas de processamento. Pode repetir o que disse?"

    # Interrupção ativa e voz da Vitória
    gather = response.gather(input='speech', action=LINK_PROCESS, language='pt-BR', speech_timeout='auto')
    gather.say(ia_resposta, language='pt-BR', voice="Polly.Vitoria")
    
    return str(response), 200, {'Content-Type': 'text/xml'}
