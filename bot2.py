from ast import pattern
import asyncio
from telethon import Button, TelegramClient, events
import telethon
from telethon.client import buttons
from telethon.errors import SessionPasswordNeededError
from telethon.sessions import StringSession
from auth_manager import AuthManager
from groupsandchannel import groupsandchannel
import requests
from file_manager import FileManager
from MessageProcces.processMessage import processMessage
import MessageProcces.telegramService 

# Configuración del bot y del cliente
api_id = 29618407
api_hash = '9139cd380cc27d66802056cd6aa70317'
bot_token = '7890267305:AAEOU8SjxTJ0fv6lKnMIjW60SZhuuqoLrS8'

bot = TelegramClient(StringSession(), api_id, api_hash).start(bot_token=bot_token)
auth_manager = AuthManager(api_id, api_hash)

# Diccionario temporal solo para el proceso de autenticación
temp_auth_data = {}
user_config = {}

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
@bot.on(events.NewMessage(pattern='/messageSettings'))
async def configurarMensajes(event):
    chat_id = event.chat_id
    gac = groupsandchannel(api_id, api_hash)
    token = gac.getStringSession(chat_id)
    if not token:
        await event.respond("El usuario no está conectado")
        return
    # Establecemos la configuración y el flag para esperar el mensaje a reenviar
    user_config[chat_id] = {
        "chat_id": chat_id,
        "ids_destino": [],
        "token": token,
        "awaiting_message": True  # Flag para indicar que se espera el mensaje a reenviar
    }
    await event.respond("Envia el mensaje (texto, imagen, video, etc.) que deseas reenviar.")

# Modificamos el handler para que solo procese mensajes cuando se está esperando el mensaje a reenviar
@bot.on(events.NewMessage(func=lambda e: 
    e.chat_id in user_config and user_config[e.chat_id].get("awaiting_message", False) and (e.text or e.message.media)
))
async def enviarMensajes(event):
    chat_id = event.chat_id
    user_config[chat_id]["awaiting_message"] = False
    print("Comenzando proceso de configuracion de mensaje ...")
    if event.text.startswith('/'):
        user_config[chat_id]["awaiting_message"] = True
        return
    print("El mensaje no es un comando ")
    mensaje = {}
    description = event.message.message if event.message.message else None
    if event.text:
        print("El mensaje es un texto ")
        mensaje['texto'] = event.text
    elif description:
        mensaje["texto"] = description
    if event.message.media:
        if isinstance(event.message.media, telethon.types.MessageMediaPhoto):
            type = 'image'
            extension = 'jpg'
        elif isinstance(event.message.media , telethon.types.MessageMediaDocument):
            type = 'document'
            extension = event.message.media.document.mime_type.split('/')[-1]
        elif isinstance(event.message.media , telethon.types.MessageMediaVideo):
            type = 'video'
            extension = 'mp4'
        content = await event.message.download_media(bytes)
        fileManager = FileManager()
        route = fileManager.Save_File(content ,type , extension)
        print(route)
        mensaje['media'] = route
    user_config[chat_id]["mensaje"] = mensaje

    token = user_config[chat_id].get("token")
    if not token:
        await event.respond("El usuario no está conectado")
        return

    client = TelegramClient(StringSession(token), api_id, api_hash)
    try:
        await client.connect()
        dialogs = await client.get_dialogs()
    except Exception as e:
        await event.respond("Error al obtener tus grupos. Vuelve a conectarte al bot")
        return
    finally:
        await client.disconnect()

    lista_grupos = {
        str(dialog.id): dialog.title
        for dialog in dialogs if dialog.is_group or dialog.is_channel
    }
    user_config[chat_id]["grupos disponibles"] = lista_grupos
    await event.respond("Por favor espere a que se muestren todos los grupos y presione el boton agregar en cada grupo hacia el cual desee reenviar el mensaje.\n"
                        "Despues que termine presione el boton 🎯 He terminado")
    for group_id , group_name in lista_grupos.items():
        texto = f"{group_name}"
        button = [Button.inline("✅ Agregar" , data=f"toggle:{group_id}")]
        await event.respond(texto , buttons = button)
    button = [Button.inline("🎯 He terminado" , data="finished")]
    await event.respond("Si ya terminó de seleccionar los grupos por favor presione el botón ", buttons=button)    
@bot.on(events.CallbackQuery(pattern=r'toggle:(\S+)'))
async def callback_toggle(event):
    chat_id = event.chat_id
    group_id = event.data.decode().split(":", 1)[1]
    config = user_config.get(chat_id)
    if not config:
        await event.answer("La configuración ya ha finalizado" , alert= True)
        return
    if group_id in config["ids_destino"]:
        config["ids_destino"].remove(group_id)
        newText = "✅ Agregar"
    else:
        config["ids_destino"].append(group_id)
        newText = "❌ Eliminar"
    try:
        await event.edit(buttons=[[Button.inline(newText, data=f"toggle:{group_id}")]])
    except Exception as e:
        if "Content of the message was not modified" in str(e):
            pass
        else:
            print("Error al editar el mensaje:", e)
    await event.answer("¡Actualizado!")
@bot.on(events.CallbackQuery(pattern=r"finished"))
async def finished_handler(event):
    chat_id = event.chat_id
    if chat_id not in user_config:
        await event.answer("No se encontro una configuracion activa. ", alert= True)
        return
    await event.respond("Por favor envie el intervalo en minutos")
@bot.on(events.NewMessage(func=lambda e: e.chat_id in user_config and e.text and e.text.isdigit()))
async def recibir_intervalo(event):
    chat_id = event.chat_id
    intervalo = int(event.text)
    user_config[chat_id]["intervalo"] = intervalo
    
    data = {
        "chat_id": user_config[chat_id]["chat_id"],
        "ids_destino": user_config[chat_id]["ids_destino"],
        "mensaje" : user_config[chat_id]["mensaje"],
        "intervalo" : user_config[chat_id]["intervalo"]
    }
    print(data["mensaje"])      
    try:
        response = requests.post(f"http://localhost:3000/configuracio-mensaje", json=data)
        if response.status_code == 200:
            del user_config[chat_id]
            await event.respond("✅ Configuración completada. Tu mensaje se reenviará automáticamente.")
        else:
            await event.respond("❌ Error al enviar la configuración a la API.")
    except Exception as e:
        await event.respond(f"❌ Error al enviar la configuración a la API: {e}")
async def MessageProcess():
    while True:
        print("Pedidiendo datos a la api")
        status_code,datos = await processMessage().GetMessageToApi("http://localhost:3000/configuracio-mensaje")
        if status_code != 200 or not datos:
            print("⏳ No hay mensajes para reenviar, esperando 1 minuto...")
            await asyncio.sleep(60)
            continue
        elif status_code == 200 :
            print(f"✅ Se encontraron mensajes para reenviar. {datos}")
            splitdates = processMessage().Split_Array_Dates(datos)
            task = []
            for lote in splitdates:
                for message in lote :
                    id_user = message["idUserTelegram"]
                    session_token = message["sessionToken"]
                    task.append(MessageProcces.telegramService.ReSend_Message(api_id , api_hash , id_user ,session_token , message))
            await asyncio.gather(*task)
            print("⏳ Esperando 1 minuto antes de la siguiente ejecución...")
            await asyncio.sleep(60)
# Iniciar el bot
if __name__ == "__main__":
    print("Bot iniciado...")
    loop = asyncio.get_event_loop()
    loop.create_task(MessageProcess())
    bot.run_until_disconnected()
