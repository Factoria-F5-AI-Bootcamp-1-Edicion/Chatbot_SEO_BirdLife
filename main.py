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
import backoff
from openai.error import RateLimitError

#Llamado de la función load_dotenv para descargar la variables guardadas en el archivo .env
load_dotenv()

#Insertar clave de openai
openai.api_key = env["OPENAI_API_KEY"]
#Insertar clave del telebot
bot = telebot.TeleBot(env["BOT_API_KEY"])
#Insertar clave de Mongo
mongodb_url = os.getenv("MONGO_URL")
#Insertar claves de redis
redis_host = os.getenv ("redis_host")
redis_port = os.getenv ("redis_port")
redis_password = os.getenv ("redis_password")


# Verificar si las claves están definidas
if not env.get("OPENAI_API_KEY"):
    print("La clave de API de OpenAI no está definida en las variables de entorno.")
if not env.get("BOT_API_KEY"):
    print("La clave de API del bot de Telegram no está definida en las variables de entorno.")
if not env.get("MONGO_URL"):
    print("La URL de momgodb no está definida en las variables de entorno.")
if not env.get("redis_host"):
    print("La redis_host no está definida en las variables de entorno.")
if not env.get("redis_port"):
    print("El puerto de redis no está definido en las variables de entorno.")
if not env.get("redis_password"):
    print("El password de redis no está definido en las variables de entorno.")

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


#Acceso al archivo .txt que contiene el texto base que empleará las respuestas a las preguntas realizadas.
try:
    with open('instructions.txt', 'r', encoding='utf-8') as f:
        INSTRUCTIONS = f.read().strip()
# En caso que no se haya creado el archivo .txt que incluye el texto base, mostrar el siguiente mensaje de error.
except FileNotFoundError:
    print("El archivo 'instructions.txt' no se encontró en el directorio actual.")
    logging.critical("El archivo 'instructions.txt' no se encontró en el directorio actual.")
    sys.exit()

# Variable de caché configurada con 14 días
cache = TTLCache(maxsize=100, ttl=1209600)

#Sistema de logging
logging.basicConfig(filename='bot.log', level=logging.DEBUG, format='Date-Time : %(asctime)s : Line No. : %(lineno)d - %(message)s',filemode='w')


# Registro de la función que responde a los comandos /start /help. Cuando alguno de los comandos es recibido se envía un mensaje de bienvenida
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    logging.debug("Received a 'start' or 'help' command")
    # Definir mensaje de bienvenida que mostrará el chatbot.
    welcome_message = "Hola, soy PiaBot." \
                      "Esta información es proporcionada por un equipo de expertos en el cuidado de aves silvestres de SEO BirdLife." \
                      "No se acepta ninguna responsabilidad por cualquier daño o pérdida que pueda resultar de su aplicación. " \
                      "¡Comencemos! 👋🤖. " \
                      
    bot.reply_to(message, welcome_message)


# Función para el uso del texto base 'INSTRUCTIONS'.
def get_instructions():
    # En caso que la consulta realizada esté almacenada en el caché, retornará la respuesta previamente almacenada.
    if 'INSTRUCTIONS' in cache:
        return cache['INSTRUCTIONS']
    # De lo contrario consultará el texto base para proporcionar la respuesta. 
    else:
        with open('instructions.txt', 'r', encoding='utf-8') as f:
            INSTRUCTIONS = f.read().strip()
            cache['INSTRUCTIONS'] = INSTRUCTIONS
            return INSTRUCTIONS
        
# El decorador de telebot se ejecutará para cada mensaje entrante sin importar su contenido. La función lambda siempre devuelve verdadero para cualquier mensaje entrante
@bot.message_handler(func=lambda message: True)

# El decorador de backoff permite que el código intente la solicitud de forma segura y automática hasta un número máximo de veces cuando se encuentra un error de límite de llamadas a la API. Se limita el número de intentos y el tiempo de espera
@backoff.on_exception(backoff.expo, RateLimitError, max_tries=10, max_time=60)

#Función que tramita las preguntas recibidas, graba las respuestas y registra el mensaje por id de usuario con fecha y hora.
def get_codex(message):
    question = str(message.text)
    user_id = message.from_user.id
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    context = f"User ID: {user_id}\n" + f"Timestamp: {timestamp}\n" + get_instructions() + "/n" + question + "\n\n"

    # Si la respuesta no existe en el caché, la crea con Openai a partir del texto base.
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
        "datetime": datetime.now() # Class method que retorna la fecha y hora local actual.

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


