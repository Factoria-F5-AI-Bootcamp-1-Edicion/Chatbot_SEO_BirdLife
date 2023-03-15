import os
import openai
import telegram
import logging
from os import environ as env
from dotenv import load_dotenv
from colorama import Fore, Back, Style
import telebot

# load values from the .env file if it exists
load_dotenv()

# configure OpenAI
#openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = env["OPENAI_API_KEY"]
bot = telebot.TeleBot(env["BOT_API_KEY"])
#bot = telegram.Bot("TOKEN_TELEGRAM").strip()


INSTRUCTIONS = """Te has encontrado un pollo de pájaro, observa si está herido o sangra, si está herido o sangra contacta con un centro de recuperación de aves, con agentes forestales o con el 112.
 Si estás en el campo y el pollito no está herido, no toques al pollito, pronto vendrán sus padres y le ayudarán. Si estas en zona urbana y el pollo es recién nacido o tiene algunas plumas y puedes ver el nido, devuelvelo a su nido con mucho cuidado, que los padres no lo van a rechazar y quédate mirando desde lejos. Si no puedes ver el nido, intenta construir una especie de nido en un lugar seguro que no corra peligro y déjalo cerca de donde lo has encontrado.
Si el pollo que te has encontrado es volantón, observa si es un lugar peligroso, si es peligroso ponlo en un lugar seguro cerca de donde lo has encontrado lejos de mascotas y tráfico y alejate. Si no es un lugar peligroso, no hagas nada, les pasa a los pollos que están aprendiendo a volar y los padres estarán cerca ayudándole.
Si el pollo que te has encontrado es un vencejo adulto, llévalo al borde de una repisa y si vuela siéntete orgulloso de haber salvado a un pollo de una especie amenazada.
Si el pollo adulto no vuela contacta con un centro de recuperación de aves, con agentes forestales o con el 112."""

ANSWER_SEQUENCE = "\nQ:"
QUESTION_SEQUENCE = "\nA: "
TEMPERATURE = 0.5
MAX_TOKENS = 500
FREQUENCY_PENALTY = 0
PRESENCE_PENALTY = 0.6
# limits how many questions we include in the prompt
MAX_CONTEXT_QUESTIONS = 10


#mensajes de entrada
@bot.message_handler(func=lambda message: True)
def get_codex(message):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt='"""\n{}\n"""'.format(message.text),
        temperature=0,
        max_tokens=1200,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=['"""'])

    bot.send_message(message.chat.id,
    f'```python\n{response["choices"][0]["text"]}\n```',
    parse_mode="Markdown")

bot.infinity_polling()

def get_moderation(question):
    """
    Check the question is safe to ask the model
    Parameters:
        question (str): The question to check
    Returns a list of errors if the question is not safe, otherwise returns None
    """

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
        # get the categories that are flagged and generate a message
        result = [
            error
            for category, error in errors.items()
            if response.results[0].categories[category]
        ]
        return result
    return None


def main():
    os.system("cls" if os.name == "nt" else "clear")
    # keep track of previous questions and answers
    previous_questions_and_answers = []
    while True:
        # ask the user for their question
        new_question = input(
            Fore.GREEN + Style.BRIGHT + "Hola, soy Ana, ¿tienes alguna pregunta para mí?: " + Style.RESET_ALL
        )
        # check the question is safe
        errors = get_moderation(new_question)
        if errors:
            print(
                Fore.RED
                + Style.BRIGHT
                + "Sorry, you're question didn't pass the moderation check:"
            )
            for error in errors:
                print(error)
            print(Style.RESET_ALL)
            continue
        # build the previous questions and answers into the prompt
        # use the last MAX_CONTEXT_QUESTIONS questions
        context = ""
        for question, answer in previous_questions_and_answers[-MAX_CONTEXT_QUESTIONS:]:
            context += QUESTION_SEQUENCE + question + ANSWER_SEQUENCE + answer

        # add the new question to the end of the context
        context += QUESTION_SEQUENCE + new_question + ANSWER_SEQUENCE

        # get the response from the model using the instructions and the context
        response = get_response(INSTRUCTIONS + context)

        # add the new question and answer to the list of previous questions and answers
        previous_questions_and_answers.append((new_question, response))

        # print the response
        print(Fore.CYAN + Style.BRIGHT + "-" + Style.NORMAL + response)


if __name__ == "__main__":
    main()