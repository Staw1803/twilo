import time
from threading import Thread
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
import google.generativeai as genai

app = Flask(__name__)

# CONFIGURAÇÕES
ACCOUNT_SID = 'ACa290536a8629089fbebd1d00faa9f605'
AUTH_TOKEN = '6ba7e589c085a68ff4b21770ee52760a'
NUMERO_TWILIO = '+16189964461'
MEU_NUMERO_CELULAR = '+5592981233982'

# REGENERE SUA CHAVE NO GOOGLE AI STUDIO E COLE AQUI
genai.configure(api_key="AQ.Ab8RN6L-KmnSO-tjPzXMdEr7VzpCllACYP0c_JeDCmAYCu1naQ")

client = Client(ACCOUNT_SID, AUTH_TOKEN)
model = genai.GenerativeModel('gemini-1.5-flash')

# O CÉREBRO: Processamento de Voz
@app.route("/voice", methods=['POST'])
def voice():
    response = VoiceResponse()
    # Captura a voz e envia para a rota /process
    gather = response.gather(input='speech', action='/process', language='pt-BR', speechTimeout='auto')
    gather.say("Arbo sistema online. Estou te ouvindo.", language='pt-BR', voice="Polly.Vitoria")
    return str(response)

@app.route("/process", methods=['POST'])
def process():
    user_speech = request.form.get('SpeechResult')
    print(f"[IA] Usuário disse: {user_speech}")
    
    # Processa com o Gemini
    try:
        ia_resposta = model.generate_content(f"Responda de forma curta e prática: {user_speech}").text
    except Exception as e:
        ia_resposta = "Desculpe, houve um erro no processamento."
        print(f"[ERRO IA] {e}")
    
    response = VoiceResponse()
    response.say(ia_resposta, language='pt-BR', voice="Polly.Vitoria")
    return str(response)

# O DISPARADOR: Martelada a cada 2 minutos
def loop_martelada():
    while True:
        try:
            print("[STATUS] Disparando chamada...")
            client.calls.create(
                url='https://arbo-jader.loca.lt/voice', 
                to=MEU_NUMERO_CELULAR,
                from_=NUMERO_TWILIO,
                timeout=60
            )
        except Exception as e:
            print(f"[ERRO TWILIO] {e}")
        
        time.sleep(120) # 2 minutos

if __name__ == "__main__":
    # Espera 5 segundos para o túnel estabilizar antes de disparar
    time.sleep(5)
    Thread(target=loop_martelada, daemon=True).start()
    app.run(port=5000)