import sys
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
import google.generativeai as genai

app = Flask(__name__)

# CONFIGURAÇÕES (Seus dados salvos)
ACCOUNT_SID = 'ACa290536a8629089fbebd1d00faa9f605'
AUTH_TOKEN = 'd7267c4849fc1f1ea1a96e2283553f42'
NUMERO_TWILIO = '+16189964461'
MEU_NUMERO_CELULAR = '+5592981233982'
GEMINI_API_KEY = 'AIzaSyCbu8o4gfvD3VmSkUSn3re0ScGBMgTfdXU'

# Inicialização dos Clientes
client = Client(ACCOUNT_SID, AUTH_TOKEN)
genai.configure(api_key=GEMINI_API_KEY, transport='rest')
model = genai.GenerativeModel('gemini-2.0-flash')

@app.route("/")
def home():
    return "Arbo Sistema Online no Render!"

@app.route("/trigger", methods=['GET', 'POST'])
def trigger_call():
    try:
        # Nota: Ajustaremos este link assim que o Render gerar o seu link oficial
        client.calls.create(
            url='https://link-do-seu-render.onrender.com/voice',
            to=MEU_NUMERO_CELULAR,
            from_=NUMERO_TWILIO,
            timeout=60
        )
        return "Chamada disparada com sucesso!", 200
    except Exception as e:
        return f"Erro ao disparar: {e}", 500

@app.route("/voice", methods=['GET', 'POST'])
def voice():
    response = VoiceResponse()
    LINK_PROCESS = 'https://link-do-seu-render.onrender.com/process'
    gather = response.gather(input='speech', action=LINK_PROCESS, language='pt-BR', speech_timeout='auto')
    gather.say("Arbo sistema online. Estou te ouvindo.", language='pt-BR', voice="Polly.Vitoria")
    return str(response), 200, {'Content-Type': 'text/xml'}

@app.route("/process", methods=['GET', 'POST'])
def process():
    user_speech = request.form.get('SpeechResult')
    if not user_speech:
        user_speech = "Alô"

    try:
        ia_resposta = model.generate_content(f"Responda de forma curta e prática: {user_speech}").text
    except Exception as e:
        ia_resposta = f"Erro no Gemini. Detalhe: {str(e)[:50]}"

    response = VoiceResponse()
    response.say(ia_resposta, language='pt-BR', voice="Polly.Vitoria")
    return str(response), 200, {'Content-Type': 'text/xml'}
