import sys
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
from groq import Groq
import requests
from duckduckgo_search import DDGS
from supabase import create_client, Client as SupabaseClient

app = Flask(__name__)

# CONFIGURAÇÕES (Seus dados ativos do Twilio + IA Groq)
ACCOUNT_SID = 'ACa290536a8629089fbebd1d00faa9f605'
AUTH_TOKEN = 'd7267c4849fc1f1ea1a96e2283553f42'
NUMERO_TWILIO = '+16189964461'
MEU_NUMERO_CELULAR = '+5592981233982'
GROQ_API_KEY = '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' # Sua chave ativa do Groq

# CONFIGURAÇÕES SUPABASE (Substitua pelos seus dados reais do painel do Supabase)
SUPABASE_URL = 'https://gzekubsjpcgrxgomoriy.supabase.co/rest/v1/'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd6ZWt1YnNqcGNncnhnb21vcml5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA4NzA3NDgsImV4cCI6MjA5NjQ0Njc0OH0.AxMl-aczglJgazwCyMZtQc191vVGjxhSiR98jUmBdAU'

# Inicialização dos Clientes
client = Client(ACCOUNT_SID, AUTH_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)
supabase: SupabaseClient = create_client(SUPABASE_URL, SUPABASE_KEY)

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

def buscar_na_internet(termo_busca):
    try:
        with DDGS() as ddgs:
            resultados = [r['body'] for r in ddgs.text(termo_busca, max_results=2)]
            if resultados:
                return f" [Internet: {' | '.join(resultados)}]"
    except Exception as e:
        print(f"[ERRO BUSCA] {e}", file=sys.stderr)
    return ""

@app.route("/")
def home():
    return "Olá Mestre! Oque deseja?"

@app.route("/trigger", methods=['GET', 'POST'])
def trigger_call():
    try:
        client.calls.create(
            url='https://twilo-eqee.onrender.com/voice',
            to=MEU_NUMERO_CELULAR,
            from_=NUMERO_TWILIO,
            timeout=60
        )
        return "Chamada disparada!", 200
    except Exception as e:
        return f"Erro: {e}", 500

@app.route("/voice", methods=['GET', 'POST'])
def voice():
    response = VoiceResponse()
    LINK_PROCESS = 'https://twilo-eqee.onrender.com/process'
    gather = response.gather(input='speech', action=LINK_PROCESS, language='pt-BR', speech_timeout='auto')
    gather.say("Arbo sistema online. Pode falar.", language='pt-BR', voice="Polly.Vitoria")
    return str(response), 200, {'Content-Type': 'text/xml'}

@app.route("/process", methods=['GET', 'POST'])
def process():
    user_speech = request.form.get('SpeechResult')
    response = VoiceResponse()
    LINK_PROCESS = 'https://twilo-eqee.onrender.com/process'

    if not user_speech:
        gather = response.gather(input='speech', action=LINK_PROCESS, language='pt-BR', speech_timeout='auto')
        return str(response), 200, {'Content-Type': 'text/xml'}

    fala_usuario = user_speech.lower()
    if any(cmd in fala_usuario for cmd in ["pode desligar", "tchau", "desliga"]):
        response.say("Conexão encerrada. Até logo!", language='pt-BR', voice="Polly.Vitoria")
        response.hangup()
        return str(response), 200, {'Content-Type': 'text/xml'}

    contexto_extra = ""
    try:
        # PARSER TRIPLO (8B): Agora identifica intenção de WhatsApp, locais e buscas na web
        extracao = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "Você é um classificador de intenções. Responda ESTRITAMENTE no formato:\n"
                        "WHATSAPP: [ENVIAR se o usuário quer mandar mensagem, LER se quer ver mensagens novas, ou NENHUM] | "
                        "PARA: [nome do contato ou NENHUM] | TXT: [conteúdo da mensagem a ser enviada ou NENHUM] | "
                        "LOCAL: [lugar citado ou NENHUM] | BUSCA: [termo para internet ou NENHUM]"
                    )
                },
                {"role": "user", "content": user_speech}
            ],
            temperature=0.0,
            max_tokens=100
        )
        dados_extraidos = extracao.choices[0].message.content.strip()
        print(f"[SISTEMA LOG] Parser: {dados_extraidos}", file=sys.stderr)
        
        # Quebrando as variáveis do parser
        partes = {p.split(":")[0].strip(): p.split(":")[1].strip() for p in dados_extraidos.split("|") if ":" in p}
        
        # AÇÃO 1: Tratar Envio de WhatsApp (Salva no Supabase)
        if partes.get("WHATSAPP") == "ENVIAR" and partes.get("PARA") != "NENHUM":
            supabase.table("whatsapp_comandos").insert({
                "destinatario": partes.get("PARA"),
                "mensagem": partes.get("TXT")
            }).execute()
            contexto_extra += f" [Confirmação técnica: O comando de enviar mensagem para {partes.get('PARA')} foi registrado com sucesso no banco de dados para o computador de casa ler.]"
            
        # AÇÃO 2: Tratar Leitura de WhatsApp (Busca do Supabase)
        elif partes.get("WHATSAPP") == "LER":
            dados_msg = supabase.table("whatsapp_mensagens").select("*").eq("lida_por_usuario", False).order("recebido_em", desc=True).limit(3).execute()
            if dados_msg.data:
                resumo_msgs = " | ".join([f"De {m['remetente']}: {m['mensagem']}" for m in dados_msg.data])
                contexto_extra += f" [Mensagens não lidas encontradas no WhatsApp de casa: {resumo_msgs}]"
                # Marca como lidas
                for m in dados_msg.data:
                    supabase.table("whatsapp_mensagens").update({"lida_por_usuario": True}).eq("id", m["id"]).execute()
            else:
                contexto_extra += " [Não há nenhuma mensagem nova ou não lida no WhatsApp de casa no momento.]"

        # AÇÃO 3: Mapas e Internet tradicionais
        if partes.get("LOCAL") != "NENHUM":
            contexto_extra += consultar_mapa_manaus(partes.get("LOCAL"))
        if partes.get("BUSCA") != "NENHUM":
            contexto_extra += buscar_na_internet(partes.get("BUSCA"))
                
    except Exception as e:
        print(f"[ERRO PARSER] {e}", file=sys.stderr)

    prompt_sistema = (
        "Você é o copiloto de inteligência avançada do ecossistema Arbo. O ano atual é 2026 e o usuário está em Manaus, Amazonas. "
        "Você é capaz de controlar o WhatsApp dele através dos comandos técnicos injetados no contexto. "
        "Se o contexto confirmar que uma mensagem foi enviada, avise de forma natural e parceira. "
        "Se houver mensagens recebidas do WhatsApp no contexto, relate-as para o usuário de forma clara. "
        "Seja extremamente curto, direto e conversacional (máximo de 3 frases)."
    )

    try:
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
        ia_resposta = "Tive um pequeno atraso na ponte com o banco de dados. Pode repetir?"

    gather = response.gather(input='speech', action=LINK_PROCESS, language='pt-BR', speech_timeout='auto')
    gather.say(ia_resposta, language='pt-BR', voice="Polly.Vitoria")
    
    return str(response), 200, {'Content-Type': 'text/xml'}
