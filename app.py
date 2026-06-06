import sys
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
from groq import Groq

app = Flask(__name__)

# CONFIGURAÇÕES (Seus dados ativos do Twilio + IA Groq)
ACCOUNT_SID = 'ACa290536a8629089fbebd1d00faa9f605'
AUTH_TOKEN = 'd7267c4849fc1f1ea1a96e2283553f42'
NUMERO_TWILIO = '+16189964461'
MEU_NUMERO_CELULAR = '+5592981233982'
GROQ_API_KEY = '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'  # Garanta que sua chave gsk_ atual esteja aqui

# Inicialização dos Clientes
client = Client(ACCOUNT_SID, AUTH_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)

@app.route("/")
def home():
    return "Arbo Sistema Online no Render com Groq e Loop Ativo!"

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
    gather.say("Arbo sistema online. Estou te ouvindo.", language='pt-BR', voice="Polly.Vitoria")
    return str(response), 200, {'Content-Type': 'text/xml'}

# 3. O CÉREBRO COM LOOP INTELLIGENTE
@app.route("/process", methods=['GET', 'POST'])
def process():
    user_speech = request.form.get('SpeechResult')
    if not user_speech:
        user_speech = "Alô"

    response = VoiceResponse()
    LINK_PROCESS = 'https://twilo-eqee.onrender.com/process'

    # CONDIÇÃO DE DESLIGAMENTO (Engenharia Reversa de Comando)
    fala_usuario = user_speech.lower()
    if "pode desligar" in fala_usuario or "tchau" in fala_usuario or "desliga" in fala_usuario:
        response.say("Entendido. Encerrando o sistema Arbo. Até logo!", language='pt-BR', voice="Polly.Vitoria")
        response.hangup()  # Força o Twilio a bater o telefone
        return str(response), 200, {'Content-Type': 'text/xml'}

    try:
        # Chamada para o Llama 3.1 da Groq
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "user", "content": f"Responda em português, de forma muito curta, direta e prática: {user_speech}"}
            ]
        )
        ia_resposta = completion.choices[0].message.content
    except Exception as e:
        print(f"[ERRO GROQ] {e}", file=sys.stderr)
        ia_resposta = f"Erro na IA. Detalhe: {str(e)[:50]}"

    # 1. A Vitória fala a resposta da Inteligência Artificial
    response.say(ia_resposta, language='pt-BR', voice="Polly.Vitoria")
    
    # 2. MÁGICA DO LOOP: Logo após falar, ela já reabre o microfone esperando a próxima pergunta!
    response.gather(input='speech', action=LINK_PROCESS, language='pt-BR', speech_timeout='auto')
    
    return str(response), 200, {'Content-Type': 'text/xml'}
