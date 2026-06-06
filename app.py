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
GROQ_API_KEY = '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' # Sua chave ativa do Groq

# Inicialização dos Clientes
client = Client(ACCOUNT_SID, AUTH_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)

@app.route("/")
def home():
    return "Arbo Assistente Conversacional Ativo no Render!"

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
    
    # Microfone aberto desde o segundo zero
    gather = response.gather(input='speech', action=LINK_PROCESS, language='pt-BR', speech_timeout='auto')
    gather.say("Arbo sistema online. Pode falar, estou te ouvindo.", language='pt-BR', voice="Polly.Vitoria")
    return str(response), 200, {'Content-Type': 'text/xml'}

# 3. O CÉREBRO COOPERATIVO E INTERRUPTÍVEL
@app.route("/process", methods=['GET', 'POST'])
def process():
    user_speech = request.form.get('SpeechResult')
    response = VoiceResponse()
    LINK_PROCESS = 'https://twilo-eqee.onrender.com/process'

    # Se houver silêncio ou falha na captação, reabre o microfone direto sem desligar
    if not user_speech:
        gather = response.gather(input='speech', action=LINK_PROCESS, language='pt-BR', speech_timeout='auto')
        return str(response), 200, {'Content-Type': 'text/xml'}

    # CONDIÇÃO DE DESLIGAMENTO EXPRESSA
    fala_usuario = user_speech.lower()
    if any(cmd in fala_usuario for cmd in ["pode desligar", "tchau", "desliga", "encerrar a chamada"]):
        response.say("Entendido. Fechando conexão. Até mais!", language='pt-BR', voice="Polly.Vitoria")
        response.hangup()
        return str(response), 200, {'Content-Type': 'text/xml'}

    try:
        # Prompt modelado para inteligência contextual avançada e questionamento ativo
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "Você é o copiloto de inteligência do ecossistema Arbo. Seu objetivo é ajudar o usuário "
                        "em absolutamente tudo o que ele precisar, agindo com extrema inteligência, clareza e parceria. "
                        "Aja como em uma conversa natural de telefone: compreenda a fundo o que ele quer dizer. "
                        "Se a pergunta dele for vaga ou se você precisar de mais detalhes para dar a resposta perfeita, "
                        "não tente adivinhar ou inventar caminhos malucos; em vez disso, responda com o que sabe e faça "
                        "uma pergunta inteligente de volta para guiar o papo. Mantenha as falas dinâmicas, fluidas e sem enrolação."
                    )
                },
                {
                    "role": "user", 
                    "content": user_speech
                }
            ],
            temperature=0.4, # Equilíbrio perfeito entre foco e capacidade de diálogo
            max_tokens=200
        )
        ia_resposta = completion.choices[0].message.content
    except Exception as e:
        print(f"[ERRO GROQ] {e}", file=sys.stderr)
        ia_resposta = "Deu um pequeno estalo na linha. Pode repetir o que falou?"

    # MÁGICA DA INTERRUPÇÃO AUTOMÁTICA: 
    # Ao envelopar o .say() dentro do .gather(), a Vitória começa a falar a resposta da IA,
    # mas se você começar a falar por cima, o Twilio corta o áudio dela na hora e processa sua nova fala!
    gather = response.gather(input='speech', action=LINK_PROCESS, language='pt-BR', speech_timeout='auto')
    gather.say(ia_resposta, language='pt-BR', voice="Polly.Vitoria")
    
    return str(response), 200, {'Content-Type': 'text/xml'}
