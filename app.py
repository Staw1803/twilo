import sys
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
from groq import Groq

app = Flask(__name__)

# CONFIGURAÇÕES (Seus dados ativos do Twilio + Nova IA Groq)
ACCOUNT_SID = 'ACa290536a8629089fbebd1d00faa9f605'
AUTH_TOKEN = 'd7267c4849fc1f1ea1a96e2283553f42'
NUMERO_TWILIO = '+16189964461'
MEU_NUMERO_CELULAR = '+5592981233982'

# COLE SUA CHAVE DO GROQ AQUI ABAIXO (Começa com gsk_)
GROQ_API_KEY = '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'

# Inicialização dos Clientes
client = Client(ACCOUNT_SID, AUTH_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)

@app.route("/")
def home():
    return "Arbo Sistema Online no Render com Groq!"

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

# 2. O ATENDIMENTO
@app.route("/voice", methods=['GET', 'POST'])
def voice():
    response = VoiceResponse()
    LINK_PROCESS = 'https://twilo-eqee.onrender.com/process'
    gather = response.gather(input='speech', action=LINK_PROCESS, language='pt-BR', speech_timeout='auto')
    gather.say("Arbo sistema online. Estou te ouvindo.", language='pt-BR', voice="Polly.Vitoria")
    return str(response), 200, {'Content-Type': 'text/xml'}

# 3. O CÉREBRO (Agora rodando Llama 3 super rápido e sem erro 429)
@app.route("/process", methods=['GET', 'POST'])
def process():
    user_speech = request.form.get('SpeechResult')
    if not user_speech:
        user_speech = "Alô"

    try:
        # Chamada para o Llama 3 da Groq (Livre de bloqueios de IP)
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

    response = VoiceResponse()
    response.say(ia_resposta, language='pt-BR', voice="Polly.Vitoria")
    return str(response), 200, {'Content-Type': 'text/xml'}
