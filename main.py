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
#Llamado de la función load_dotenv para descargar la variables guardadas en el archivo .env
load_dotenv()

#Insertar clave de openai
openai.api_key = env["OPENAI_API_KEY"]
#Insertar clave del telebot
bot = telebot.TeleBot(env["BOT_API_KEY"])


#Con este statement se accede al archivo .txt que contine el texto base que empleará openai para elaborar las respuestas a las preguntas realizadas.
with open('instructions.txt', 'r', encoding='utf-8') as f:
    INSTRUCTIONS = f.read().strip()

# Configurar el logging para escribir debug messages en el archivo bot.log
logging.basicConfig(filename='bot.log', level=logging.DEBUG, format='Date-Time : %(asctime)s : Line No. : %(lineno)d - %(message)s',filemode='w')

# Registro de la función que responde a los comandos /start /help. Cuando alguno de los comandos es recibido se envia un mensaje de bienvenida
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    logging.debug("Received a 'start' or 'help' command")
    welcome_message = "Hola, soy PiaBot, una inteligencia artificial entrenada por OpenAI. " \
                      "Esta información es proporcionada por un chatbot creado por un equipo de expertos en el cuidado de aves silvestres. " \
                      "No se acepta ninguna responsabilidad por cualquier daño o pérdida que pueda resultar de su aplicación. " \
                      "¡Comencemos! 👋🤖. " \
                      
    bot.reply_to(message, welcome_message)

#Función que tramita las preguntas recibidas, crea un prompt que incluye el texto base y las preguntas, envia el prompt a openai para generar la respuesta y devuelverla al usuario. 
# Registramos el mensaje por id de usuario con fecha y hora.
@bot.message_handler(func=lambda message: True)
def get_codex(message):
    question = str(message.text)
    user_id = message.from_user.id
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    context = f"User ID: {user_id}\n" + INSTRUCTIONS + "\n" + question + "\n" + f"Timestamp: {timestamp}\n"
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


# Encapsular el proceso de inicialización del bot

def main():
    # Eliminar webhook antes de empezar el sondeo
    bot.delete_webhook()
    # Iniciar el bot
    bot.polling(none_stop=True)
if __name__ == "__main__":
    main()


