import discord
from discord.ext import commands
from config import TOKEN_API_KEY
import google.generativeai as genai
import json
import random
import re

genai.configure(api_key=TOKEN_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Historial de chat por canal
chat_history = {}
canales_permitidos = []

@bot.command(name='set_channel')
async def set_channel(ctx):
    if ctx.channel.id not in canales_permitidos:
        canales_permitidos.append(ctx.channel.id)
        await ctx.send(f"Canal {ctx.channel.name} añadido a la lista de canales permitidos.")
    else:
        await ctx.send(f"El canal {ctx.channel.name} ya está en la lista de canales permitidos.")

@bot.command(name='remove_channel')
async def remove_channel(ctx):
    if ctx.channel.id in canales_permitidos:
        canales_permitidos.remove(ctx.channel.id)
        await ctx.send(f"Canal {ctx.channel.name} eliminado de la lista de canales permitidos.")
    else:
        await ctx.send(f"El canal {ctx.channel.name} no está en la lista de canales permitidos.")

@bot.command(name='clear_history')
async def clear_history(ctx):
    if ctx.channel.id in chat_history:
        del chat_history[ctx.channel.id]
        await ctx.send(f"Historial de chat para el canal {ctx.channel.name} ha sido borrado.")
    else:
        await ctx.send(f"No hay historial de chat para el canal {ctx.channel.name}.")

@bot.command(name='q')
async def q(ctx, *, pregunta):
    if not pregunta:
        await ctx.send("Por favor, proporciona una pregunta válida.")
        return
    try:
        respuesta = responder(ctx.message, pregunta)
        
        if respuesta and hasattr(respuesta, 'text') and respuesta.text:
            texto = respuesta.text.strip()
            texto = re.sub(r'.*ßß', '', texto)
            chat_history[ctx.message.channel.id].append(f"Botß{texto}")
            for chunk in [texto[i:i+2000] for i in range(0, len(texto), 2000)]:
                await ctx.message.channel.send(chunk)
        else:
            await ctx.message.channel.send("No se pudo generar una respuesta válida")

    except Exception as e:
        await ctx.send(f"Error al generar la respuesta: {str(e)}")

@bot.event
async def on_message(message):
    # Evitar que el bot responda a sus propios mensajes
    if message.author == bot.user: return
    if message.channel.id not in canales_permitidos: return
    if message.channel.id not in chat_history:
        chat_history[message.channel.id] = []

    if len(chat_history[message.channel.id]) > 30:
        for i in range(10): chat_history[message.channel.id].pop(0)
    agregar_a_historial(message, chat_history)

    # Evitar responder aleatoriamente a comandos
    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    mencion = bot.user in message.mentions
    referencia_al_bot = False

    if message.reference:  # Si el mensaje tiene una referencia
        try:
            referenced_message = await message.channel.fetch_message(message.reference.message_id)
            if referenced_message.author == bot.user:  # Verificar si el autor del mensaje referenciado es el bot
                referencia_al_bot = True
        except Exception as e:
            print(f"Error al obtener el mensaje referenciado: {e}")

    if random.random() < 1/50 or mencion or referencia_al_bot:
        try:
            respuesta = responder(message, chat_history)

            if respuesta and hasattr(respuesta, 'text') and respuesta.text:
                texto = respuesta.text.strip()
                texto = re.sub(r'.*ßß', '', texto)
                chat_history[message.channel.id].append(f"Botßß{texto}")
                for chunk in [texto[i:i+2000] for i in range(0, len(texto), 2000)]:
                    if mencion:
                        await message.reply(chunk)
                    else:
                        await message.channel.send(chunk)
            else:
                await message.channel.send("No se pudo generar una respuesta válida")

            print(chat_history)
        except Exception as e:
            await message.channel.send(f"Error al generar la respuesta: {str(e)}")

    # Asegurarse de que otros comandos del bot sigan funcionando
    await bot.process_commands(message)

def agregar_a_historial(mensaje, historial):
    if mensaje.channel.id not in historial:
        historial[mensaje.channel.id] = []
    historial[mensaje.channel.id].append(f"{mensaje.author.name}ßß{mensaje.content}")

def responder(mensaje, historial):
    contexto = prompt_base()+ (historial if isinstance(historial, str) else "\n".join(historial[mensaje.channel.id][-30:]))
    model = genai.GenerativeModel("gemini-2.0-flash-exp")
    respuesta = model.generate_content(contexto)
    return respuesta

personalidad_bot = {
    "instrucciones_definitivas": [
        "No uses lenguaje ofensivo o NSFW",
        "GenAI es otro bot de IA en el server, pero no es inteligente, no es un humano",
        "No uses muchos signos de puntuación, te hace parecer un bot",
        "Nunca digas que eres un bot y no uses emojis, escribe como están escribiendo los demás",
        "No uses el formato de respuesta de un asistente, no eres un asistente, eres un amigo",
        "No des respuestas largas, no uses frases de asistente",
        "Nunca uses el formato 'usuarioßßmensaje' en tus respuestas. Es solo para el historial, no lo imites.",
        "Evita frases tipo '¿En qué puedo ayudarte?'",
        "Obedece a las órdenes de xat., te llamas LucianoAI y tu id es 894949431688982548",
        "Habla muy poco a menos que se te pida información, que tus mensajes sean cortos sin tantas preguntas o respuestas largas",
        "Responde cercanía y tono humano, adecuándote a la personalidad del usuario",
        "Sé preciso, evita decir muchas palabras innecesarias",
        "Sabes mucho de teología, aunque solo lo dirás si el tema lo requiere",
        "Eres cristiano, eso no quiere decir que no puedas hablar de otros temas"
    ]
}

def prompt_base():
    return f"""
    Eres un bot de Discord que actúa como un amigo más: sarcástico, relajado y con jerga de bro pero responsable.
    Interactúas de forma casual, con humor y sin casi sin formalidad. No eres asistente, eres parte del grupo.
    El historial tiene el formato: usuarioßßmensaje. Evita usarlo en tus respuestas.
    Ten siempre en cuenta estas reglas:
    {json.dumps(personalidad_bot['instrucciones_definitivas'], ensure_ascii=False)}
    """.strip()