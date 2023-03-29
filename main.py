#Importación de las librerias
import os
import openai
from os import environ as env
from dotenv import load_dotenv
import telebot
import logging
import requests
import json
import datetime
import redis
#Llamado de la función load_dotenv para descargar la variables guardadas en el archivo .env
load_dotenv()

#Insertar clave de openai
openai.api_key = env["OPENAI_API_KEY"]
#Insertar clave del telebot
bot = telebot.TeleBot(env["BOT_API_KEY"])
#La parte de chaché de Redis
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
redis_conn = redis.from_url(redis_url)


# Verificar si las claves están definidas
if not env.get("OPENAI_API_KEY"):
    print("La clave de API de OpenAI no está definida en las variables de entorno.")
if not env.get("BOT_API_KEY"):
    print("La clave de API del bot de Telegram no está definida en las variables de entorno.")

# Configurar OpenAI y Telegram bot si las claves están definidas
try:
    openai.api_key = env["OPENAI_API_KEY"]
except TypeError:
    print("La clave de API de OpenAI no es válida.")
try:
    bot = telebot.TeleBot(env["BOT_API_KEY"])
except TypeError:
    print("La clave de API del bot de Telegram no es válida.")
    
#Con este statement se accede al archivo .txt que contine el texto base que empleará openai para elaborar las respuestas a las preguntas realizadas.
try:
    with open('instructions.txt', 'r', encoding='utf-8') as f:
        INSTRUCTIONS = f.read().strip()
except FileNotFoundError:
    print("El archivo 'instructions.txt' no se encontró en el directorio actual.")

# Variable de caché configurada con 14 días
cache = TTLCache(maxsize=100, ttl=1209600)

#Sistema de logging
logging.basicConfig(filename='bot.log', level=logging.INFO, format='Date-Time : %(asctime)s : Line No. : %(lineno)d - %(message)s',filemode='w')
logging.getLogger().setLevel(logging.WARNING)

# Registro de la función que responde a los comandos /start /help. Cuando alguno de los comandos es recibido se envia un mensaje de bienvenida
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    logging.debug("Received a 'start' or 'help' command")
    welcome_message = "Hola, soy PiaBot." \
                      "Esta información es proporcionada por un equipo de expertos en el cuidado de aves silvestres de SEO BirdLife." \
                      "No se acepta ninguna responsabilidad por cualquier daño o pérdida que pueda resultar de su aplicación. " \
                      "¡Comencemos! 👋🤖. " \
                      
    bot.reply_to(message, welcome_message)


#Funcion para las intrucciones
def get_instructions():
    if 'INSTRUCTIONS' in cache:
        return cache['INSTRUCTIONS']
    else:
        with open('instructions.txt', 'r', encoding='utf-8') as f:
            INSTRUCTIONS = f.read().strip()
            cache['INSTRUCTIONS'] = INSTRUCTIONS
            return INSTRUCTIONS
        
#Función que tramita las preguntas recibidas, crea un prompt que incluye el texto base y las preguntas, envia el prompt a openai para generar la respuesta y devuelverla al usuario. 
# Registramos el mensaje por id de usuario con fecha y hora.
@bot.message_handler(func=lambda message: True)
def get_codex(message):
    question = str(message.text)
    user_id = message.from_user.id
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    context = f"User ID: {user_id}\n" + "fTimestamp: {timestamp}\n" + get_instructions() + "/n" + question + "\n\n"

    #Primero revisa en la caché si tiene la respuesta similar, sino, la crea con Openai
    if redis_conn.get(question):
        answer = redis_conn.get(question).decode('utf-8')
    else:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=context,
            temperature=0.5,
            max_tokens=1024,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0.6,
            stop=None
        )
        answer = response.choices[0].text.strip()
        #La caché de Redis para guardar las respuestas
        redis_conn.set(question, answer) 



    with open("preguntas_respuestas.txt", "a", encoding="utf-8") as file:
        file.write(f"User ID: {user_id}\n")
        file.write(f"Fecha y hora: {timestamp}\n")
        file.write(f"Pregunta: {question}\n")
        file.write(f"Respuesta: {answer}\n\n")

    bot.reply_to(message, answer)

#Esta función toma la pregunta del usuario como input, se la envia al api moderation de openai y retorna una lista de flag content si la pregunta viola la politica de moderación.
def get_moderation(question):
    errors = {
        "hate": "Content that expresses, incites, or promotes hate based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste.",
        "hate/threatening": "Hateful content that also includes violence or serious harm towards the targeted group.",
        "self-harm": "Content that promotes, encourages, or depicts acts of self-harm, such as suicide, cutting, and eating disorders.",
        "sexual": "Content meant to arouse sexual excitement, such as the description of sexual activity, or that promotes sexual services (excluding sex education and wellness).",
        "sexual/minors": "Sexual content that includes an individual who is under 18 years old.",
        "violence": "Content that promotes or glorifies violence or celebrates the suffering or humiliation of others.",
        "violence/graphic": "Violent content that depicts death, violence, or serious physical injury in extreme graphic detail.",
    }
    response = openai.Moderation.create(input=question)
    if response.results[0].flagged:
        result = [
            error
            for category, error in errors.items()
            if response.results[0].categories[category]
        ]
        return result
    return None

# Función conexión a mongodb
def store_chatbot_conversation(database_bot, collection_bot, user_id, user_question, chatbot_response):
    # Conectarse al servidor de MongoDB
    client = pymongo.MongoClient("mongodb://localhost:27017/")

    # Acceder a la base de datos y a la colección
    db = client[database_bot]
    collection = db[collection_bot]

    # Crear un documento con la conversación y la fecha y hora actual
    conversation = {
        "user_id": user_id,
        "user_question": user_question,
        "chatbot_response": chatbot_response,
        "datetime": datetime.now() # Classmethod que retorna la fecha y hora local actual.

    }

    # Insertar el documento en la colección
    result = collection.insert_one(conversation)

    # Imprimir el ID del documento insertado
    print("Conversación insertado con éxito. ID:", result.inserted_id)

# Encapsular el proceso de inicialización del bot
def main():
    # Eliminar webhook antes de empezar el sondeo
    bot.delete_webhook()
    # Iniciar el bot
    bot.polling(none_stop=True)
if __name__ == "__main__":
    main()


