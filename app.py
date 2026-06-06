import sys
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
from groq import Groq
import requests
from duckduckgo_search import DDGS

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

# FUNÇÃO: Consulta a API de mapas para Manaus
def consultar_mapa_manaus(local_texto):
    url = "https://nominatim.openstreetmap.org/search"
    headers = {'User-Agent': 'ArboAssistant/1.0 (jader@evo.com)'}
    params = {'q': f"{local_texto}, Manaus", 'format': 'json', 'limit': 1}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=4)
        if response.status_code == 200 and response.json():
            return f" [Mapa de Manaus: Localizado em {response.json()[0].get('display_name', '')}]"
    except Exception as e:
        print(f"[ERRO MAPA] {e}", file=sys.stderr)
    return ""

# FUNÇÃO: Faz a busca em tempo real na internet de graça
def buscar_na_internet(termo_busca):
    try:
        with DDGS() as ddgs:
            resultados = [r['body'] for r in ddgs.text(termo_busca, max_results=2)]
            if resultados:
                return f" [Dados em Tempo Real da Internet: {' | '.join(resultados)}]"
    except Exception as e:
        print(f"[ERRO BUSCA WEB] {e}", file=sys.stderr)
    return ""

@app.route("/")
def home():
    return "Arbo Sistema Conectado à Internet em Tempo Real!"

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

# 3. O CÉREBRO CONECTADO À WEB COM REDUNDÂNCIA
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

    contexto_extra = ""
    try:
        # PARSER DUPLO (8B): Extrai local do mapa E termo de busca na internet ao mesmo tempo
        extracao = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system", 
                    "content": "Você é um assistente de extração de dados. Responda ESTRITAMENTE no formato exato: LOCAL: [nome do lugar ou NENHUM] | BUSCA: [termo de pesquisa para internet sobre notícias, fatos atuais, clima, ou NENHUM]"
                },
                {"role": "user", "content": user_speech}
            ],
            temperature=0.0,
            max_tokens=60
        )
        dados_extraidos = extracao.choices[0].message.content.strip()
        print(f"[SISTEMA LOG] Extração: {dados_extraidos}", file=sys.stderr)
        
        # Processando a resposta do extrator
        if "LOCAL:" in dados_extraidos and "BUSCA:" in dados_extraidos:
            partes = dados_extraidos.split("|")
            loc = partes[0].replace("LOCAL:", "").strip()
            bus = partes[1].replace("BUSCA:", "").strip()
            
            if "NENHUM" not in loc.upper() and len(loc) > 2:
                contexto_extra += consultar_mapa_manaus(loc)
            if "NENHUM" not in bus.upper() and len(bus) > 2:
                contexto_extra += buscar_na_internet(bus)
                
    except Exception as e:
        print(f"[ERRO ANALISADOR PREVIO] {e}", file=sys.stderr)

    # Diretrizes Soberanas da IA (Ciente do Tempo Real e do Ano Atual de 2026)
    prompt_sistema = (
        "Você é o copiloto de inteligência avançada do ecossistema Arbo. Seu objetivo é ajudar o usuário "
        "em tudo, usando máxima sabedoria. NOTA CRÍTICA: O ano atual é 2026. O usuário está em MANAUS, AMAZONAS. "
        "Sempre que anexado à pergunta houver dados em tempo real da internet ou do mapa, use-os como verdade absoluta "
        "para responder com precisão. Responda de forma muito curta, natural e direta ao ponto (máximo de 3 frases)."
    )

    ia_resposta = ""
    try:
        # TENTATIVA 1: Llama 3.3 70B com internet injetada
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": f"{user_speech} {contexto_extra}"}
            ],
            temperature=0.3,
            max_tokens=250
        )
        ia_resposta = completion.choices[0].message.content
    except Exception as e70b:
        print(f"[SISTEMA] Recuando para o modelo 8B: {e70b}", file=sys.stderr)
        try:
            # FALLBACK: Llama 3.1 8B assume se o grande falhar
            completion = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": prompt_sistema},
                    {"role": "user", "content": f"{user_speech} {contexto_extra}"}
                ],
                temperature=0.3,
                max_tokens=200
            )
            ia_resposta = completion.choices[0].message.content
        except Exception as e8b:
            ia_resposta = "Tive um pequeno atraso na busca de dados. Pode repetir?"

    # Interrupção ativa e voz da Vitória
    gather = response.gather(input='speech', action=LINK_PROCESS, language='pt-BR', speech_timeout='auto')
    gather.say(ia_resposta, language='pt-BR', voice="Polly.Vitoria")
    
    return str(response), 200, {'Content-Type': 'text/xml'}
