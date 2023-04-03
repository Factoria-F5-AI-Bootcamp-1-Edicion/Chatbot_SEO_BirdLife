<h1 align="center">
  <p align="center">PIABOT: La historia detrás de la creación del chatbot inteligente de SEO BirdLife en Telegram
</p>
  <img align="center" width="80%" src="https://user-images.githubusercontent.com/108665441/229526033-503d5f12-ace1-48b3-a4f0-d4edd314bc56.png">
</h1>

# :clipboard: Descripción del proyecto

PIABOT es un chatbot inteligente que se conecta a Telegram y utiliza el modelo DaVinci de OpenAI para brindar información sobre cómo actuar si se encuentra un pollito fuera de su nido, especialmente durante el verano cuando son más propensos a caer debido al calor.

El proyecto fue desarrollado por alumnos de Factoria F5 AI Bootcamp en colaboración con SEO BirdLife con el objetivo de contribuir a la preservación de las aves en España. 

## Significado de PIABOT :baby_chick:

PIABOT es un juego de palabras que hace referencia a los pollitos y la inteligencia artificial utilizada en el chatbot.

# :mechanical_arm: Estado del proyecto
:white_check_mark: Proyecto en funcionamiento :white_check_mark:

El proyecto se encuentra en estado funcional, pero existen oportunidades de mejora para optimizar su rendimiento y ofrecer una experiencia de alta calidad. Para lograr esto, se requiere adquirir servicios premium de la API de OpenAI, Azure Redis y MongoDB. Esto es especialmente importante para empresas que manejan grandes cantidades de datos y requieren un alto nivel de confiabilidad y seguridad en su infraestructura de bases de datos.

## :wrench: Funcionalidades del proyecto

- `Funcionalidad 1`: brinda información sobre qué hacer si se encuentra un pollito fuera de su nido.
- `Funcionalidad 2`: integración con Telegram para una experiencia de uso más amigable y accesible.
- `Funcionalidad 3`: reconocimiento de lenguaje natural para brindar una respuesta personalizada a cada consulta.

## 📁 Acceso al proyecto

*Clona el contenido del repositorio* >> [Chatbot_SEO_BirdLife](https://github.com/Factoria-F5-AI-Bootcamp-1-Edicion/Chatbot_SEO_BirdLife.git)

```
git clone https://github.com/usuario/nombre-repositorio.git
```

## 🛠️ Abre y ejecuta el proyecto en 5 pasos

**1. Crea un entorno específicamente para este proyecto con Conda o Venv:**

+ **OPCIÓN 1: Conda:**
```
conda create -n nombreEntorno
```
Activar el entorno:
```
conda activate nombre-del-entorno
```
+ **OPCIÓN 2: Venv:**

Situate en la carpeta donde quieres crear tu entorno e ingresa el siguiente comando:

```
python -m venv nombredetuentorno
```
Activa el entorno virtual 
+ **Windows:**
```
nombredetuentorno\Scripts\activate.bat
```
+ **Mac o Linux:**
```
source nombredetuentorno/bin/activate
```

**2. Dentro de este entorno debes instalar todas las librerías necesarias con la siguiente línea de comando:**

```
pip install -r requirements.txt
```

**3. Crea un archivo .env para guardar el token de Telegram, Key de Api Openai, conexión principal a Mongo y Redis en Azure. Recuerda que este archivo debe estar incluido en *.gitignore*:**

```
OPENAI_API_KEY = "Tu api key de Openai"
BOT_API_KEY ="Tu token de bot de telegram"
MONGO_URI = "Conexión de Mongo en Azure"

redis_host= "Host de Redis en Azure"
redis_port= "Puerto"
redis_password="Key de Redis en azure"
```
**4. Nuestro script hace uso de un prompt por lo que será necesario crear un archivo `instructions.txt`.**

**5. Situate en la carpeta que contiene los archivos y desde allí ejecute:**

```
python3 main.py
```
**6. Y ¡listo! nuestro chatbot inteligente estará funcionando 🤖**

<p align="center">
  <img src="https://user-images.githubusercontent.com/108665441/229521453-6f06ed07-fb58-4ea1-b796-b9d4d737c2ab.png" width="25%">
</p>


# :wrench: Tecnologías usadas:

   - **Desarrollo:** DaVinci de OpenAI, Telebot, Pymongo, Redis, Azure Redis, Azure MongoDB.
   - **Documentación:** [Notion](https://www.notion.so/PiaBot-5774b2b4ccfb49669a1df3693c9389ef)
   - **Presentación:** [Canva](https://www.canva.com/design/DAFfC6VpyJA/v7fzxCaGd_5JzFs-MtbjJw/watch?utm_content=DAFfC6VpyJA&utm_campaign=designshare&utm_medium=link&utm_source=publishsharelink)

## Autores
![equipo]()

## :mailbox:Contacta con nosotros:
+ [Alexandra Mendoza](https://www.linkedin.com/in/alexandra-mendoza-malasquez/)
+ [Ana de Córdoba](https://www.linkedin.com/in/anadecordoba/)
+ [Henry Suárez](https://www.linkedin.com/in/henry-su%C3%A1rez-b60419256/)
+ [Pablo Ruano](https://www.linkedin.com/in/pabloruanosainz/)

<p align="center"><em>¡Protege las aves con la ayuda de <strong>PIABOT</strong>, el chatbot inteligente de SEO BirdLife!</em></p>

