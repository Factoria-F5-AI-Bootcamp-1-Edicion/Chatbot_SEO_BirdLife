#Importación de las librerias
import os
import openai
from os import environ as env
from dotenv import load_dotenv
import telebot
import logging
import pymongo
import datetime
from datetime import datetime
import redis
from cachetools import TTLCache
import sys

#Llamado de la función load_dotenv para descargar la variables guardadas en el archivo .env
load_dotenv()

#Insertar clave de openai
openai.api_key = env["OPENAI_API_KEY"]
#Insertar clave del telebot
bot = telebot.TeleBot(env["BOT_API_KEY"])
#Insertar clave de Mongo
mongodb_url = os.getenv("MONGO_URI")
#Insertar claves de redis
redis_host = os.getenv ("redis_host")
redis_port = os.getenv ("redis_port")
redis_password = os.getenv ("redis_password")


# Verificar si las claves están definidas
if not env.get("OPENAI_API_KEY"):
    print("La clave de API de OpenAI no está definida en las variables de entorno.")
if not env.get("BOT_API_KEY"):
    print("La clave de API del bot de Telegram no está definida en las variables de entorno.")

# Control de excepciones de la API KEY de OpenAI
try:
    openai.api_key = env["OPENAI_API_KEY"]
except TypeError:
    print("La clave de API de OpenAI no es válida.")
    logging.critical("La clave de API de OpenAI no está definida en las variables de entorno.")
    sys.exit()
# Control de excepciones de Token de Telegram
try:
    bot = telebot.TeleBot(env["BOT_API_KEY"])
except TypeError:
    print("La clave de API del bot de Telegram no es válida.")
    logging.critical("La clave de API del bot de Telegram no está definida en las variables de entorno.")
    sys.exit()
# Control de excepciones de claves de Redis
try:
    r = redis.StrictRedis(host=redis_host, port=redis_port, password=redis_password, ssl=True)
except (redis.exceptions.ConnectionError, ValueError):
    print("No se pudo conectar a Redis con las credenciales proporcionadas.")
    logging.critical("No se pudo conectar a Redis con las credenciales proporcionadas.")
    sys.exit()


#Acceso al archivo .txt que contine el texto base que empleará las respuestas a las preguntas realizadas.
try:
    with open('instructions.txt', 'r', encoding='utf-8') as f:
        INSTRUCTIONS = f.read().strip()
except FileNotFoundError:
    print("El archivo 'instructions.txt' no se encontró en el directorio actual.")
    logging.critical("El archivo 'instructions.txt' no se encontró en el directorio actual.")
    sys.exit()

# Variable de caché configurada con 14 días
cache = TTLCache(maxsize=100, ttl=1209600)

#Sistema de logging
logging.basicConfig(filename='bot.log', level=logging.DEBUG, format='Date-Time : %(asctime)s : Line No. : %(lineno)d - %(message)s',filemode='w')


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
        
#Función que tramita las preguntas recibidas, grabamos las respuestas y lasregistramos el mensaje por id de usuario con fecha y hora.
@bot.message_handler(func=lambda message: True)
def get_codex(message):
    question = str(message.text)
    user_id = message.from_user.id
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    context = f"User ID: {user_id}\n" + "fTimestamp: {timestamp}\n" + get_instructions() + "/n" + question + "\n\n"

    #Primero revisa en la caché si tiene la respuesta similar, sino, la crea con Openai
    if r.get(question):
        answer = r.get(question).decode('utf-8')
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
        #Caché de Redis para guardar las respuestas
        r.set(question, answer)

    bot.reply_to(message, answer)
    # Almacenar la conversación en MongoDB
    store_chatbot_conversation("database_bot", "collection_bot", user_id, question, answer)

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
    client = pymongo.MongoClient(mongodb_url)

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
    print("Conversación insertada con éxito. ID:", result.inserted_id)

# Encapsular el proceso de inicialización del bot
def main():
    # Eliminar webhook antes de empezar el sondeo
    bot.delete_webhook()
    # Iniciar el bot
    bot.polling(none_stop=True)
if __name__ == "__main__":
    main()


