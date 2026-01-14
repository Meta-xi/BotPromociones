import asyncio
from telethon import Button, TelegramClient, events
import telethon
from telethon.client import buttons
from telethon.errors import SessionPasswordNeededError
from telethon.sessions import StringSession
from MessageProcces.processWhsatpp import processWhatsapp
from auth_manager import AuthManager
from groupsandchannel import groupsandchannel
import requests
from file_manager import FileManager
from MessageProcces.processMessage import processMessage
import MessageProcces.telegramService
import base64
from io import BytesIO
''' from PayMethods import PayMethods
import threading '''


api_id = 29618407
api_hash = '9139cd380cc27d66802056cd6aa70317'
bot_token = '8344191766:AAHpG3TeBmmSWaVHY2OIv-E6EOzEtn8-a1c'
criptobot_Token = '34426:AAb9Y4eTl5TAZMvzmTD1SlnS9L3Okouv8Hg'
api_criptobot_url = 'https://testnet-pay.crypt.bot/'

bot = TelegramClient(StringSession(), api_id, api_hash).start(bot_token=bot_token)
auth_manager = AuthManager(api_id, api_hash)
''' invoice_service = PayMethods(criptobot_Token=criptobot_Token) '''

temp_auth_data = {}
user_config = {}
groups_add = {}
groups_remove = {}
pending_configs: dict[int , list] = {}
pending_edit: dict[int , dict] = {}
plans = [
    {"nombre": "Plan Básico", "precio": 5, "duración": "1 mes" , },
    {"nombre": "Plan Intermedio", "precio": 10, "duración": "3 meses"},
    {"nombre": "Plan Avanzado", "precio": 20, "duración": "6 meses"}
]
instance_name_whatsapp : dict[int , dict] = {}
whatsapp_config = {}
@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    welcome_message = """
🤖 <b>¡Bienvenido al Bot de Promociones!</b>

Aquí tienes la lista de comandos disponibles:

▶️ <b>/start</b>  
Muestra este tutorial con la descripción de cada comando.

📱 <b>/connect &lt;número&gt;</b>  
Conecta tu cuenta de Telegram al bot.  
<code>Ejemplo: /connect +1234567890</code>

⚙️ <b>/message_settings</b>  
Inicia la configuración del reenvío de mensajes personalizados.

🔄 <b>/updateconfigs</b>  
Actualiza tus configuraciones existentes sin tener que recrearlas.

⏸️ <b>/pause</b>  
Detiene temporalmente una o varias configuraciones activas.

▶️ <b>/play</b>  
Reanuda las configuraciones previamente pausadas.

🗑️ <b>/deleteconfig</b>  
Elimina una o varias configuraciones activas.

❌ <b>/logout</b>  
Desconecta tu cuenta del bot de forma segura.

🚀 <b>Para comenzar</b>, usa <code>/connect</code> seguido de tu número de teléfono.

📱  <b>/createinstancetowhatsapp</b>
Conecta tu cuenta de whatsapp al bot

⚙️ <b>/beginprocesstoconfigwhatsapp</b> 
Inicia la configuración del reenvío de mensajes personalizados hacia whatsapp.
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
            await event.respond(" Autenticado correctamente ", parse_mode='html')
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
@bot.on(events.NewMessage(pattern='/message_settings'))
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
        token = await auth_manager.get_token(chat_id)
        if not token:
            await event.respond("El usuario no esta conectado , por favor conectese al bot y comience de nuevo")
            return
        headers = {
            'Authorization' : f"Bearer {token}",
            'Content-Type' : 'application/json'
        }
        session = requests.Session()
        session.trust_env = False
        response = session.post(f"https://apibotmassive-production.up.railway.app/configuracio-mensaje", json=data , headers=headers)
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
        status_code,datos = await processMessage().GetMessageToApi("https://apibotmassive-production.up.railway.app/configuracio-mensaje")
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
''' @bot.on(events.NewMessage(pattern = '/PaySubscription'))
async def StartPay(event):
    chat_id = event.chat_id
    buttons = []
    for i , plan in enumerate(plans):
        nombre = plan["nombre"]
        precio = plan["precio"]
        duracion = plan["duracion"]
        text = f"{nombre} , Precio: ${precio} ,Duracion: ${duracion}"
        buttons.append( [Button.inline(f"🛒 Comprar Pland" ,data =str(i))] ) 
        await event.respond(text , button)
@bot.on(events.CallbackQuery)
async def handler_button(event):
    plan_index = int(event.data.decode())
    select_plan = plans[plan_index]
    nombre = select_plan["nombre"]
    precio = select_plan["precio"]
    duracion = select_plan["duracion"]
    user_id = event.chat_id
    invoice = await invoice_service.create_invoice('USDT' ,str(precio) ,f'Suscripcion: {nombre} - {duracion}')
    if invoice['ok']:
        invoice_id = invoice['result']['invoice_id']
        pay_url = invoice['result']['pay_url']
        invoice = invoice_service.send_new_Transaction(invoice_id , user_id , precio)
        if invoice[0] == 200:
            await event.respond(f'✅ Has Seleccionado el {nombre}.\n\n 🔗 Realiza el pago usando este enlace: {pay_url}')
        else:
            await event.respond('❌ Hubo un error al crear la transaccion')
    else:
        await event.respond('❌ Hubo un error al crear la transaccion')
async def monitor_payments():
    while True:
        pending_payments = await invoice_service.get_transactions()
        for payment in pending_payments:
            invoice = payment['invoice_id']
            response = await invoice_service.check_invoice(invoice)
            if response['ok']:
                status = response['result']['status']
                if status == 'paid':
                    payment['status'] = 'paid'
                    bot.loop.create_task(bot.send_message(payment['user_id'] , f"✅ Has pagado la suscripcion de {payment['price']}. \n\nAhora puedes configurar mensajes para reenvio"))
        response = await invoice_service.send_modify_transactions(pending_payments)
        if response[0] == 200:
            print("✅ Transacciones actualizadas correctamente")
        else:
            print(f"❌ Error al actualizar transacciones: {response[1]}")
        await asyncio.sleep(60) '''
@bot.on(events.NewMessage(pattern='/updateconfigs'))
async def update_configs(event):
    chat_id = event.chat_id
    token = await auth_manager.get_token(chat_id)
    if not token:
        await event.respond("El usuario no esta conectado , por favor conectese al bot y comience de nuevo")
        return
    headers = {
        'Authorization' : f"Bearer {token}",
        'Content-Type' : 'application/json'
    }
    status_code , configs = await processMessage().GetMessagesToUpdate(f"https://apibotmassive-production.up.railway.app/configuracio-mensaje/GetconfigurationforUser/{chat_id}" , headers)
    if status_code != 200:
        await event.respond("⚠️ No pude obtener las configuraciones (código {}).".format(status_code))
        return
    if len(configs) == 0:
        await event.respond("No tienes configuraciones activas.")
        return
    sessionToken = configs[0]["sessionToken"]
    client = TelegramClient(StringSession(sessionToken) , api_id , api_hash)
    await client.connect()
    if not await client.is_user_authorized():
        await event.respond("⚠️ Usuario no autorizado, no se pueden obtener los grupos.")
        return
    groups = await MessageProcces.telegramService.cache_groups(client)
    await client.disconnect()
    for idx , cfg in enumerate(configs , start=1):
        total = len(configs)
        nombres = []
        for gid in cfg["ids_destino"]:
            try:
                ent = groups.get(int(gid))
                if not ent:
                    ent = await client.get_entity(int(gid))
                nombres.append(ent.title)
            except Exception:
                nombres.append(f"{gid} (No encontrado)")

        destinos_str = "\n-".join(nombres)
        text = cfg["mensaje"].get("texto" , "")
        caption = (
            f"📋 Ìndice: {idx}/{total}\n"
            f"⏱ Intervalo: {cfg['interval']} minutos\n"
            f"🎯 Destinos: \n{destinos_str}\n"
            f"📝 Mensaje: {text}"
        )
        media_path = cfg["mensaje"].get("media")
        if media_path:
            try:
                await bot.send_file(chat_id , file = media_path , caption = caption)
            except Exception as e:
                await event.respond(caption + "\n\n❌ No pude adjuntar la imagen")
                print(f"Error enviando media '{media_path}': {e}")
        else:
            await event.respond(caption)
    pending_configs[chat_id] = configs
    buttons = []
    row = []
    for i, _ in enumerate(configs, start=1):
        row.append(Button.inline(str(i), data=f'select:{i-1}'))
        if len(row) == 4:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([Button.inline("🎯 He terminado de actualizar" , data = f"update_finished")])
    await event.respond("🔢 Selecciona el índice de la configuración que quieres actualizar:" , buttons = buttons)
@bot.on(events.CallbackQuery(pattern = r'^select:(\d+)$'))
async def on_select_config(event):
    await event.answer()
    chat_id = event.chat_id
    idx = int(event.data.decode().split(':' , 1)[1])
    configs = pending_configs.get(chat_id)
    if not configs or idx < 0 or idx >= len(configs):
        return await event.answer("❌ Configuración no válida." , alert = True)
    config = configs[idx]
    nombres = []
    sessionToken = config["sessionToken"]
    client = TelegramClient(StringSession(sessionToken) , api_id , api_hash)
    await client.connect()
    if not await client.is_user_authorized():
        await event.answer("⚠️ Usuario no autorizado, no se pueden obtener los grupos." , alert = True)
        return
    grupos = await MessageProcces.telegramService.cache_groups(client)
    await client.disconnect()
    for gid in config["ids_destino"]:
        ent = grupos.get(int(gid))
        nombres.append(ent.title if ent else f"{gid} (No encontrado)")
    destinos_str = " \n- ".join(nombres)
    texto = config["mensaje"].get("texto" , "")
    caption = (
        f"⏱ Intervalo: {config['interval']} minutos\n"
        f"🎯 Destinos: {destinos_str}\n"
        f"📝 Mensaje: {texto}"
    )    
    media = config["mensaje"].get("media")
    if media: 
        await bot.send_file(chat_id , file = media , caption = caption)
    else:
        await bot.send_message(chat_id , caption)
    textos : list[str] = ["Intervalo" , "Destinos" , "Mensaje" , "Back"]
    data : list[str] = [f"interval:{idx}" , f"destinos:{idx}" , f"message:{idx}" , f"go_back:{idx}"]
    buttons = []
    row = []
    for texto , d in zip(textos , data):
        row.append(Button.inline(texto , data = d))
    buttons.append(row)
    await event.respond("Seleccione una opción" , buttons = buttons)
@bot.on(events.CallbackQuery(pattern = r'^go_back:(\d+)$'))
async def back_to_configs(event):
    await event.answer()
    chat_id = event.chat_id
    idx = int(event.data.decode().split(":" , 1)[1])
    configs = pending_configs.get(chat_id)
    if not configs:
        return await event.answer("No hay configuraciones activas.", alert=True)
    if chat_id in groups_add:
        config = configs[idx]
        old_groups = [int(g) for g in config["ids_destino"]]
        new_groups = groups_add.pop(chat_id)["groups_to_add"]
        merged = list(set(old_groups + [int(g) for g in new_groups]))
        merged_string = [str(g) for g in merged]
        config["ids_destino"] = merged_string
    if chat_id in groups_remove:
        config = configs[idx]
        old_groups = [int(g) for g in config["ids_destino"]]
        remove_groups = groups_remove.pop(chat_id)["groups_to_remove"]
        merged = list(set(old_groups) - set(int(g) for g in remove_groups))
        merged_string = [str(g) for g in merged]
        config["ids_destino"] = merged_string
    try:
        await event.message.delete()
    except Exception:
        pass
    buttons = []
    row = []
    for i in range(1 , len(configs)+1):
        row.append(Button.inline(str(i) , data=f"select:{i-1}"))
        if len(row) == 4:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([Button.inline("🎯 He terminado de actualizar" , data = f"update_finished")])
    await bot.send_message(
        chat_id,
        "🔢 Selecciona el número de la configuración que quieres actualizar:",
        buttons=buttons
    )
@bot.on(events.CallbackQuery(pattern = r'^interval:(\d+)$'))
async def interval(event):
    await event.answer()
    chat_id = event.chat_id
    idx = int(event.data.decode().split(":" , 1)[1])
    pending_edit[chat_id] = {"field": "interval" , "idx" :idx}
    await event.respond("✏️ Envía el nuevo intervalo en minutos:")
@bot.on(events.NewMessage(func=lambda e:
    e.chat_id in pending_edit and
    pending_edit[e.chat_id]["field"] == "interval" and
    e.text and e.text.isdigit()
    ))
async def on_interval_input(event):
    chat_id = event.chat_id
    nuevo_valor = int(event.text.strip())
    edit = pending_edit.pop(chat_id)
    idx = edit["idx"]
    pending_configs[chat_id][idx]["interval"] = nuevo_valor
    button = Button.inline("Regresar a las configuraciones" , data = f"go_back:{idx}")
    await event.respond("Intervalo actualizado" , buttons = button)
@bot.on(events.CallbackQuery(pattern = r'^message:(\d+)$'))
async def message(event):
    await event.answer()
    chat_id = event.chat_id
    idx = int(event.data.decode().split(":" , 1)[1])
    pending_edit[chat_id] = {"field": "message" , "idx" : idx}
    await event.respond("✏️ Envía la nueva descripción o mensaje")
@bot.on(events.NewMessage(func = lambda e: e.chat_id in pending_edit and pending_edit[e.chat_id]["field"] == "message" and e.text))
async def on_message_input(event):
    chat_id = event.chat_id
    new_Value = event.text.strip()
    edit = pending_edit.pop(chat_id)
    idx = edit["idx"]
    pending_configs[chat_id][idx]["mensaje"]["texto"] = new_Value
    button = Button.inline("Regresar a las configuraciones" , data = f"go_back:{idx}")
    await event.respond("Descripción o mensaje actualizados " , buttons = button)
@bot.on(events.CallbackQuery(pattern = r'^destinos:(\d+)$'))
async def destinities(event):
    await event.answer()
    chat_id = event.chat_id
    idx = int(event.data.decode().split(":" , 1)[1])
    pending_edit[chat_id] = { "field" : "destinos" , "idx": idx}
    textos : list[str] = ["✅ Agregar" , "❌ Eliminar"]
    data : list[str] = [f"agregar:{idx}" , f"eliminar:{idx}"]
    buttons = []
    row = []
    for t , d in zip(textos , data):
        row.append(Button.inline(t , data = d))
    buttons.append(row)
    await bot.send_message(
        chat_id,
        "🔢 Selecciona la opción que deseas realizar ",
        buttons = buttons
    )
@bot.on(events.CallbackQuery(pattern = r'^agregar:(\d+)$'))
async def AddNewDestinities(event):
    chat_id = event.chat_id
    idx = int(event.data.decode().split(":" , 1)[1])
    configs = pending_configs.get(chat_id)
    config = configs[idx]
    token = config["sessionToken"]
    client = TelegramClient(StringSession(token) , api_id , api_hash)
    await client.connect()
    if not await client.is_user_authorized():
        await event.answer("⚠️ Usuario no autorizado, no se pueden obtener los grupos." , alert = True)
        return
    groups = await MessageProcces.telegramService.cache_groups(client)
    await client.disconnect()
    for gid in config["ids_destino"]:
        ent = groups.get(int(gid))
        if ent :
            groups.pop(int(gid) , None)
    await event.respond("Por favor espere a que se muestren todos los grupos y presione el boton agregar en los grupos que desee agregar a la configuración.\n"
                        "Despues que termine presione el botón 🔙 Back ")
    if chat_id not in groups_add:
        groups_add[chat_id] = { "groups_to_add" : [] }
    for i in groups.values():
        text = i.title
        ent_id = next(k for k , v in groups.items() if v.id == i.id)
        button = [Button.inline("✅ Agregar" , data=f"toggle_add:{ent_id}")]
        await event.respond(text , buttons = button)
    button = Button.inline("Regresar a las configuraciones" , data = f"go_back:{idx}")
    await event.respond("🎯 He terminado de agregar los nuevos grupos" ,buttons = button)  
    
@bot.on(events.CallbackQuery(pattern = r'^toggle_add:(\S+)'))
async def update_add_groups(event):
    chat_id = event.chat_id
    group_id = event.data.decode().split(":" , 1)[1]
    groups_to_add = groups_add[chat_id]
    if group_id in groups_to_add["groups_to_add"]:
        groups_to_add["groups_to_add"].remove(group_id)
        newText = "✅ Agregar"
    else:
        groups_to_add["groups_to_add"].append(group_id)
        newText = "❌ Eliminar"
    try:
        await event.edit(buttons = [[Button.inline(newText , data =f"toggle_add:{group_id}")]])
    except Exception as e:
        if "Content of the message was not modified" in str(e):
            pass
        else:
            print("Error al editar el mensaje: ", e)
    await event.answer("¡Actualizado!")
     
@bot.on(events.CallbackQuery(pattern = r'^eliminar:(\d+)'))
async def DeleteNewDestinities(event):
    chat_id = event.chat_id
    idx = int(event.data.decode().split(":" , 1)[1])
    configs = pending_configs.get(chat_id)
    config = configs[idx]
    token = config["sessionToken"]
    client = TelegramClient(StringSession(token) , api_id , api_hash)
    await client.connect()
    if not await client.is_user_authorized():
        await event.answer("⚠️ Usuario no autorizado, no se pueden obtener los grupos." , alert = True)
        return
    groups = await MessageProcces.telegramService.cache_groups(client)
    await client.disconnect()
    if chat_id not in groups_remove:
        groups_remove[chat_id] = {"groups_to_remove" : [] }
    for i in config["ids_destino"]:
        if groups.get(int(i)):
            ent = groups.get(int(i))
            text = ent.title
            button = Button.inline("❌ Eliminar" , data = f'toggle_remove:{i}')
            await event.respond(text , buttons = button)
    button = Button.inline("Regresar a las configuraciones" , data = f"go_back:{idx}")
    await event.respond("🎯 He terminado de eliminar los grupos" ,buttons = button) 
@bot.on(events.CallbackQuery(pattern = r'^toggle_remove:(\S+)'))
async def update_remove_groups(event):
    chat_id = event.chat_id
    group_id = event.data.decode().split(":" ,1)[1]
    groups_to_remove = groups_remove[chat_id]
    if group_id not in groups_to_remove:
        groups_to_remove["groups_to_remove"].append(group_id)
        newText = "✅ Agregar"
    else:
        groups_to_remove["groups_to_remove"].remove(group_id)
        newText = "❌ Eliminar"
    try:
        await event.edit(buttons = [[Button.inline(newText , data = f"toggle_remove:{group_id}")]])
    except Exception as e:
        if "Content of the message was not modified" in str(e):
            pass
        else:
            print("Error al editar el mensaje: ", e)
    await event.answer("¡Actualizado!")
@bot.on(events.CallbackQuery(pattern = r'^update_finished$'))
async def update_finished(event):
    chat_id = event.chat_id
    if chat_id in pending_configs:
        configs = pending_configs.pop(chat_id)
        token = await auth_manager.get_token(chat_id)
        if not token:
            await event.answer("El usuario no esta conectado , por favor conectese al bot y comience de nuevo" , alert = True)
            return
        headers = {
            'Authorization' : f"Bearer {token}",
            'Content-Type' : 'application/json'
        }
        api_url = f"https://apibotmassive-production.up.railway.app/configuracio-mensaje/{chat_id}"
        status_code , response_data = await processMessage().update_configs(api_url , configs , headers)
        if status_code != 200:
            await event.answer("⚠️ No pude actualizar las configuraciones (código {}).".format(status_code) , alert = True)
            return
        await event.respond("✅ Configuraciones actualizadas correctamente.")
        
@bot.on(events.NewMessage(pattern = "/deleteconfig" ))
async def deleteConfigs(event):
    chat_id = event.chat_id
    token = await auth_manager.get_token(chat_id)
    if not token:
        await event.respond("El usuario no esta conectado , por favor conectese al bot y comience de nuevo")
        return
    headers = {
        'Authorization' : f"Bearer {token}",
        'Content-Type' : 'application/json'
    }
    status , configs = await processMessage().GetMessagesToUpdate(f"https://apibotmassive-production.up.railway.app/configuracio-mensaje/GetconfigurationforUser/{chat_id}" , headers)
    if status != 200:
        await event.respond("⚠️ No pude obtener las configuraciones (código {}).".format(status))
        return
    if len(configs) == 0:
        await event.respond("No tienes configuraciones activas.")
        return
    session_token = configs[0]["sessionToken"]
    client = TelegramClient(StringSession(session_token) , api_id , api_hash)
    await client.connect()
    if not await client.is_user_authorized():
        await event.respond("⚠️ Usuario no autorizado, no se pueden obtener los grupos.")
        return
    groups = await MessageProcces.telegramService.cache_groups(client)
    await client.disconnect()
    for idx , cfg in enumerate(configs , start=1):
        total = len(configs)
        nombres = []
        for gid in cfg["ids_destino"]:
            try:
                ent = groups.get(int(gid))
                if not ent:
                    ent = await client.get_entity(int(gid))
                nombres.append(ent.title)
            except Exception:
                nombres.append(f"{gid} (No encontrado)")
        destinos_str = "\n-".join(nombres)
        text = cfg["mensaje"].get("texto" , "")
        caption = (
            f"📋 Ìndice: {idx}/{total}\n"
            f"⏱ Intervalo: {cfg['interval']} minutos\n"
            f"🎯 Destinos: \n{destinos_str}\n"
            f"📝 Mensaje: {text}"
        )
        media_path = cfg["mensaje"].get("media")
        if media_path:
            try:
                await bot.send_file(chat_id , file = media_path , caption = caption)
            except Exception as e:
                await event.respond(caption + "\n\n❌ No pude adjuntar la imagen")
                print(f"Error enviando media '{media_path}': {e}")
        else:
            await event.respond(caption)
    pending_configs[chat_id] = configs
    text : list[str] = ["🗑️ Eliminar una" , "🗑️ Eliminar todas"]
    data : list[str] = ["deleteOne" , "deleteAll"]
    buttons = []
    row = []
    for t , z in zip(text , data):
        row.append(Button.inline( t , data = z))
    buttons.append(row)
    await bot.send_message(
        chat_id,
        "🔢 Selecciona la opción que deseas realizar ",
        buttons = buttons
    )
@bot.on(events.CallbackQuery(pattern = r"^deleteOne$"))
async def start_delete_one(event):
    chat_id = event.chat_id
    configs = pending_configs[chat_id]
    buttons = []
    row = []
    for i , _ in enumerate(configs , start = 1):
        row.append(Button.inline( str(i) , data = f"select_config_to_delete:{i-1}"))
        if len(row) == 4:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    await event.respond("🔢 Selecciona el índice de la configuración que quieres eliminar" , buttons = buttons)
@bot.on(events.CallbackQuery(pattern = r'^select_config_to_delete:(\d+)$'))
async def select_config_to_delete(event):
    chat_id = event.chat_id
    idx = int(event.data.decode().split(":",1)[1])
    config = pending_configs[chat_id][idx]
    id_config = config["idConfig"]
    text: list[str] = ["🗑️ Eliminar" , "❌ No eliminar"]
    data: list[str] = [f"yes:{id_config}" , f"no"]
    buttons = []
    for t , d in zip(text , data):
        buttons.append(Button.inline(t , data = d))
    await event.respond(f"Esta seguro de eliminar la configuracion {idx+1}" , buttons = buttons)
@bot.on(events.CallbackQuery(pattern = r'^yes:([a-f0-9-]+)$'))
async def delete_one(event):
    chat_id = event.chat_id
    id_config = event.data.decode().split(":",1)[1]
    token = await auth_manager.get_token(chat_id)
    if not token:
        await event.respond("El usuario no esta conectado , por favor conectese al bot y comience de nuevo")
        return
    headers = {
        'Authorization' : f"Bearer {token}",
        'Content-Type' : 'application/json'
    }
    status , response = await processMessage().delete_one_config(f"https://apibotmassive-production.up.railway.app/configuracio-mensaje/DeleteOneConfiguration/{id_config}" , headers)
    if status == 200:
        text = response.get("message" , "Configuración eliminada correctamente")
        await event.respond(f"✅ {text}")
    else:
        text = response.get("message" , "Configuración no encontrada ")
        await event.respond(f"🔍🙈 {text}")
@bot.on(events.CallbackQuery(pattern = r"^no$"))
async def Not_delete(event):
    await event.respond("Por favor envíe el comando para la acción que desee realizar")
@bot.on(events.CallbackQuery(pattern = r"^deleteAll$"))
async def Start_delete_all(event):
    text : list[str] = ["🗑️ Eliminar" , "❌ No eliminar"]
    data : list[str] = ["yes" ,"no"]
    buttons = []
    for t , d in zip(text , data):
        buttons.append(Button.inline(t , data = d))
    await event.respond("Esta seguro de eliminar todas sus configuraciones" , buttons = buttons)
@bot.on(events.CallbackQuery(pattern = r'^yes$'))
async def Delete_all(event):
    chat_id = event.chat_id
    token = await auth_manager.get_token(chat_id)
    if not token:
        await event.respond("El usuario no esta conectado , por favor conectese al bot y comience de nuevo")
        return
    headers = {
        'Authorization' : f"Bearer {token}",
        'Content-Type' : 'application/json'
    }
    code , response = await processMessage().Delete_all_config(f"https://apibotmassive-production.up.railway.app/configuracio-mensaje/DeleteAllConfigurations/{chat_id}" , headers = headers)
    if code == 200:
        text = response.get("message" , "Configuraciones eliminadas correctamente")
        await event.respond(f"✅ {text}")
    else:
        text = response.get("message" , "Error al eliminar las configuraciones")
        await event.respond(f"❌ {text}")
@bot.on(events.NewMessage(pattern = "/pause"))
async def pause(event):
    chat_id = event.chat_id
    token = await auth_manager.get_token(chat_id)
    if not token:
        await event.respond("El usuario no esta conectado , por favor conectese al bot y comience de nuevo")
        return 
    headers = {
        'Authorization' :f'Bearer {token}',
        'Content_Type': 'application/json'
    }
    code , configs = await processMessage().GetConfigsEnable(f"https://apibotmassive-production.up.railway.app/configuracio-mensaje/GetEnableConfigurations/{chat_id}" , headers = headers)
    if code != 200:
        await event.respond("⚠️ No pude obtener las configuraciones (código {}).".format(status))
        return
    if len(configs) == 0:
        await event.respond("No tienes configuraciones activas.")
        return 
    session_token = configs[0]["sessionToken"]
    client = TelegramClient(StringSession(session_token) , api_id , api_hash)
    await client.connect()
    groups = await MessageProcces.telegramService.cache_groups(client)
    await client.disconnect()
    for idx , cfg in enumerate(configs , start=1):
        total = len(configs)
        nombres = []
        for gid in cfg["ids_destino"]:
            try:
                ent = groups.get(int(gid))
                if not ent:
                    ent = await client.get_entity(int(gid))
                nombres.append(ent.title)
            except Exception:
                nombres.append(f"{gid} (No encontrado)")
        destinos_str = "\n-".join(nombres)
        text = cfg["mensaje"].get("texto" , "")
        caption = (
            f"📋 Ìndice: {idx}/{total}\n"
            f"⏱ Intervalo: {cfg['interval']} minutos\n"
            f"🎯 Destinos: \n{destinos_str}\n"
            f"📝 Mensaje: {text}"
        )
        media_path = cfg["mensaje"].get("media")
        if media_path:
            try:
                await bot.send_file(chat_id , file = media_path , caption = caption)
            except Exception as e:
                await event.respond(caption + "\n\n❌ No pude adjuntar la imagen")
                print(f"Error enviando media '{media_path}': {e}")
        else:
            await event.respond(caption)
    pending_configs[chat_id] = configs
    text : list[str] = ["⏸️ Pausar una" , "⏸️ Pausar todas"]   
    data : list[str] = ["pauseOne" , "pauseAll"]
    buttons = []
    for t , d in zip(text , data ):
        buttons.append(Button.inline(t ,data = d))
    await event.respond("🔢 Selecciona la opción que deseas realizar " , buttons = buttons)
@bot.on(events.CallbackQuery(pattern = r"^pauseOne$"))
async def start_pause_one(event):
    chat_id = event.chat_id
    configs = pending_configs[chat_id]
    buttons = []
    row = []
    for c , _ in enumerate(configs ,start = 1):
        row.append(Button.inline(str(c) , data = f"select_config_to_pause:{c-1}"))
        if len(row) == 4:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    await event.respond("🔢 Selecciona el índice de la configuración que deseas pausar" , buttons = buttons)
@bot.on(events.CallbackQuery(pattern = r'^select_config_to_pause:(\d+)$'))
async def select_config_to_pause(event):
    chat_id = event.chat_id
    idx = int(event.data.decode().split(":" , 1)[1])
    config = pending_configs[chat_id][idx]
    id_config = config["idConfig"]
    text : list[str] = ["⏸️ Pausar" , "❌ No pausar"]
    data : list[str] = [f"yes_pause:{id_config}", "no"]
    buttons = []
    for t , d in zip(text , data):
        buttons.append(Button.inline( t , data = d))
    await event.respond(f"¿Estás seguro de pausar la configuración {idx+1}?" , buttons = buttons)
@bot.on(events.CallbackQuery(pattern = r'^yes_pause:([a-f0-9-]+)$'))
async def end_pause(event):
    chat_id = event.chat_id
    id_config = event.data.decode().split(":" , 1)[1]
    token = await auth_manager.get_token(chat_id)
    if not token:
        await event.respond("El usuario no esta conectado , por favor conectese al bot y comience de nuevo")
        return
    headers = {
        'Authorization' : f"Bearer {token}",
        'Content_Type' : 'application/json'
    }
    code , response = await processMessage().pause_one_config(f"https://apibotmassive-production.up.railway.app/configuracio-mensaje/DisableOneConfiguration/{id_config}" , headers = headers)
    if code == 200:
        text = response.get("message" , "Configuración pausada correctamente")
        await event.respond(f"✅ {text}")
    else:
        text = response.get("message" , "Error al pausar la configuración")
        await event.respond(f"❌ {text}")
@bot.on(events.CallbackQuery(pattern = r'^pauseAll$'))
async def Pause_all(event):
    buttons = []
    text : list[str] = ["⏸️ Pausar" , "❌ No pausar"]
    data : list[str] = ["yes_pause_all" , "no"]
    for t , d in zip(text , data ):
        buttons.append(Button.inline( t , data= d))
    await event.respond("¿Estás seguro de pausar todas las configuraciones?" , buttons = buttons)
@bot.on(events.CallbackQuery(pattern = r'^yes_pause_all$'))
async def end_pause_all(event):
    chat_id = event.chat_id
    token = await auth_manager.get_token(chat_id)
    if not token:
        await event.respond("El usuario no esta conectado , por favor conectese al bot y comience de nuevo")
        return 
    headers = {
        'Authorization' : f"Bearer {token}",
        'Content_Type' : 'application/json'
    }
    code , response = await processMessage().pause_all_configs(f"https://apibotmassive-production.up.railway.app/configuracio-mensaje/DisableAllConfigurations/{chat_id}" ,headers = headers)
    if code == 200:
        text = response.get("message" , "Configuraciones pausadas correctamente")
        await event.respond(f"✅ {text}")
    else:
        text = response.get("message" , "Error al pausar las configuraciones")
        await event.respond(f"❌ {text}")
@bot.on(events.NewMessage(pattern = "/play"))
async def play_configs(event):
    chat_id = event.chat_id
    token = await auth_manager.get_token(chat_id)
    if not token:
        await event.respond("El usuario no esta conectado ,por favor conectese al bot y comience de nuevo")
        return 
    headers = {
        'Authorization' : f"Bearer {token}",
        'Content_Type' : 'application/json'
    }
    code , configs = await processMessage().getConfigsDisabled(f"https://apibotmassive-production.up.railway.app/configuracio-mensaje/GetDisableConfigurations/{chat_id}" , headers)
    if code != 200:
        await event.respond("⚠️ No pude obtener las configuraciones (código {}).".format(status))
        return
    if len(configs) == 0:
        await event.respond("No tienes configuraciones pausadas")
        return
    session_token = configs[0]["sessionToken"]
    client = TelegramClient(StringSession(session_token) , api_id , api_hash)
    await client.connect()
    groups = await MessageProcces.telegramService.cache_groups(client)
    await client.disconnect()
    for idx , cfg in enumerate(configs , start = 1):
        total = len(configs)
        nombres = []
        for gid in cfg["ids_destino"]:
            try:
                ent = groups.get(int(gid))
                nombres.append(ent.title)
            except:
                nombres.append(f"{gid} no encontrado")
        destinos_str = "\n-".join(nombres)
        text = cfg["mensaje"].get("texto" , "")
        caption = (
            f"📋 Ìndice: {idx}/{total}\n"
            f"⏱ Intervalo: {cfg['interval']} minutos\n"
            f"🎯 Destinos: \n{destinos_str}\n"
            f"📝 Mensaje: {text}"
        )
        media_path = cfg["mensaje"].get("media")
        if media_path:
            try:
                await bot.send_file(chat_id , file = media_path , caption = caption)
            except Exception as e:
                await event.respond(caption + "\n\n❌ No pude adjuntar la imagen")
                print(f"Error enviando media '{media_path}': {e}")
        else:
            await event.respond(caption)
    pending_configs[chat_id] = configs
    buttons = []
    text : list[str] = ["▶️ Reanudar una" , "▶️ Reanudar todas"]
    data : list[str] = ["play_one" , "play_all"]
    for t , d in zip(text , data ):
        buttons.append(Button.inline( t , data = d))
    await event.respond("🔢 Selecciona la opción que deseas realizar" , buttons = buttons)
@bot.on(events.CallbackQuery(pattern = r'^play_one$'))
async def play_one(event):
    chat_id = event.chat_id
    buttons = []
    row = []
    configs = pending_configs[chat_id]
    for c , _ in enumerate(configs , start = 1):
        row.append(Button.inline(str(c) , data = f"select_config_to_play:{c-1}"))
        if len(row) == 4:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    await event.respond("🔢 Selecciona el índice de la configuración que deseas pausar" , buttons = buttons)
@bot.on(events.CallbackQuery(pattern = r'^select_config_to_play:(\d+)$'))
async def start_play_one(event):
    chat_id = event.chat_id
    idx = int(event.data.decode().split(":" , 1)[1])
    config = pending_configs[chat_id][idx]
    id_config = config["idConfig"]
    buttons = []
    text : list[str] = ["▶️ Reanudar" , "❌ No reanudar"]
    data : list[str] = [f"yes_play:{id_config}" , "no"]
    for t , d in zip(text , data ):
        buttons.append(Button.inline( t , data = d))
    await event.respond(f"¿Estás seguro de pausar la configuración {idx+1}?" , buttons = buttons)
@bot.on(events.CallbackQuery(pattern = r'^yes_play:([a-f0-9-]+)$'))
async def end_play_one(event):
    chat_id = event.chat_id
    token = await auth_manager.get_token(chat_id)
    id_config = event.data.decode().split(":", 1)[1]
    if not token:
        await event.respond("No estás conectado ,por favor conectese al bot y comience de nuevo.")
        return
    headers = {
        'Authorization' : f"Bearer {token}",
        'Content_Type' : 'application/json'
    }
    code , response = await processMessage().play_one_config(f"https://apibotmassive-production.up.railway.app/configuracio-mensaje/EnableOneConfiguration/{id_config}" , headers= headers)
    if code == 200:
        text = response.get("message" , "Configuración reanudada correctamente.")
        await event.respond(f"✅ {text}")
    else:
        text = response.get("message" , "Error al reanudar la configuración")
        await event.respond(f"❌ {text}")
@bot.on(events.CallbackQuery(pattern = r'^play_all$'))
async def start_play_all(event):
    buttons = []
    text : list[str] = ["▶️ Reanudar" , "❌ No reanudar"]
    data : list[str] = ["yes_play_all" , "no"]
    for t , d in zip(text , data):
        buttons.append(Button.inline(t , data = d))
    await event.respond("¿Estás seguro de reanudar todas sus configuraciones?" , buttons = buttons)
@bot.on(events.CallbackQuery(pattern = r'^yes_play_all$'))
async def end_play_all(event):
    chat_id = event.chat_id
    token = await auth_manager.get_token(chat_id)
    if not token:
        await event.respond("No estás conectado , por favor conectese al bot y comience de nuevo")
        return 
    headers = {
        'Authorization' : f"Bearer {token}",
        'Content_Type' : 'application/json'
    }
    code , response = await processMessage().play_all_configs(f"https://apibotmassive-production.up.railway.app/configuracio-mensaje/EnableAllConfigurations/{chat_id}" , headers = headers)
    if code == 200:
        text = response.get("message" , "Configuraciones reanudadas correctamente")
        await event.respond(f"✅ {text}")
    else:
        text = response.get("message" , "Error al reanudar las configuraciones")
        await event.respond(f"❌ {text}")
@bot.on(events.NewMessage(pattern="/createinstancetowhatsapp"))
async def ConnectToWhatsapp(event):
    chat_id = event.chat_id
    text = "Por favor, para conectarse a WhatsApp, escriba un nombre para su instancia"
    if chat_id in instance_name_whatsapp:
        instance_name_whatsapp.pop(chat_id)
    instance_name_whatsapp[chat_id] = {
        "field": "instance", 
        "status": "waiting_for_name"
    }
    await event.respond(text)
@bot.on(events.NewMessage(
    func=lambda e: (
        e.chat_id in instance_name_whatsapp and 
        instance_name_whatsapp[e.chat_id].get("status") == "waiting_for_name" and 
        e.text and 
        not e.text.startswith('/')
    )
))
async def SendDataToApiForWhatsapp(event):
    chat_id = event.chat_id
    if chat_id not in instance_name_whatsapp:
        return
    if instance_name_whatsapp[chat_id].get("status") != "waiting_for_name":
        return
    text = event.text.strip()
    instance_name_whatsapp[chat_id]["status"] = "processing"
    try:
        data = {
            "InstanceName": text,
            "UserTelegramId": chat_id
        }
        token = await auth_manager.get_token(chat_id)
        if not token:
            event.respond("No esta conectado al bot , por favor conectese y comience de nuevo")
            return
        headers = {
        'Authorization' : f"Bearer {token}",
        'Content_Type' : 'application/json'
        }
        print(token)
        code, response = await processWhatsapp().Conect_To_Whatsapp("https://apibotmassive-production.up.railway.app/instance-whatsapp", data , headers)
        if code == 401:
            await event.respond("El usuario no esta conectado , por favor conectese al bot y comience de nuevo")
            return 
        if code != 201:
            print(code)
            await event.respond("No se pudo crear la instancia")
            return
        
        if "base64" not in response:
            await event.respond("Error: No se recibió código QR")
            return
        
        base64_image = response.get('base64','').split(',')[1] if "," in response["base64"] else response["base64"]
        image_bytes = base64.b64decode(base64_image)
        image_IO = BytesIO(image_bytes)
        image_IO.name = "qr_whatsapp.png"
        image_IO.seek(0)
        
        await event.respond(
            "📱 Por favor escanee este código QR con su aplicación de WhatsApp en la sección 'Vincular dispositivos' para conectar su cuenta y espere a que el dispositivo termine de sincronizar su cuenta con la aplicacion para comenzar a utilizar las funcionalidades",
            file=image_IO
        ) 
    except Exception as e:
        await event.respond(f"Error: {str(e)}")
    finally:
        if chat_id in instance_name_whatsapp:
            instance_name_whatsapp.pop(chat_id)
@bot.on(events.NewMessage(pattern = "/beginprocesstoconfigwhatsapp"))
async def BeginProcess(event):
    chat_id = event.chat_id
    whatsapp_config[chat_id] = {
        "chat_id" : chat_id,
        "ids_destino" : [],
        "caption" : "",
        "intervalo" : 0,
        "awaiting_message" : True
    }
    await event.respond("Envia el mensaje (texto ,imagen) que deseas reenviar ,por favor solo imagenes jpg");
@bot.on(events.NewMessage(func = lambda e:(e.chat_id in whatsapp_config and whatsapp_config[e.chat_id].get("awaiting_message" , False) and (e.text or e.message.media) and not e.out)))
async def getMessage(event):
    chat_id = event.chat_id 
    if event.text.startswith('/'):
        whatsapp_config[chat_id]["awaiting_message"] = True
        return
    whatsapp_config[chat_id]["awaiting_message"] = False
    description = event.message.message if event.message.message else None
    if event.text:
        whatsapp_config[chat_id]["caption"] = event.text
        whatsapp_config[chat_id]["imagen"] = None
    elif description:
        whatsapp_config[chat_id]["caption"] = description
    if event.message.media:
        whatsapp_config[chat_id]["imagen"] = await event.message.download_media(bytes)
    token = await auth_manager.get_token(chat_id)
    if not token:
        event.respond("No esta conectado al bot , por favor conectese y comience de nuevo")
        return
    headers = {
        'Authorization' : f"Bearer {token}",
        'Content_Type' : 'application/json'
    }
    status_code , response = await processWhatsapp().GetInstanceName(f"https://apibotmassive-production.up.railway.app/instance-whatsapp/{chat_id}" , headers)
    if status_code == 401:
        await event.respond("El usuario no esta conectado , por favor conectese al bot y comience de nuevo")
        return 
    if status_code != 200:
        await event.respond("La instancia no se encuentra")
        return
    instance_name = response
    code , res = await processWhatsapp().Get_Groups(f"https://apibotmassive-production.up.railway.app/massive-forward/getGroups/{instance_name}" , headers)
    if code == 401:
        await event.respond("El usuario no esta conectado , por favor conectese al bot y comience de nuevo")
        return 
    if code != 200:
        await event.respond("La instancia no se encuentra ")
        return
    if len(res) == 0:
        await event.respond("Usted no tiene grupos de Whatsapp")
        return
    print(res)
    whatsapp_config[chat_id]["available_groups"] = res
    await event.respond("Por favor espere a que se muestren todos los grupos y presione el boton agregar en cada grupo hacia el cual desee reenviar el mensaje.\n"
                        "Despues que termine presione el boton 🎯 He terminado")
    for i in res:
        if i.get('subject'):
            text = i.get('subject')
            idx = i.get('id')
            button = [Button.inline("✅ Agregar" , data = f"toggle_whatsapp:{idx}")]
            await event.respond(text , buttons = button)
    button = [Button.inline("🎯 He terminado" , data = f"end_whatsapp")]
    await event.respond("Si ya terminó de seleccionar los grupos por favor presione el botón " , buttons = button)
@bot.on(events.CallbackQuery(pattern = r'toggle_whatsapp(\S+)'))
async def AddAndQuitGroups(event):
    chat_id = event.chat_id
    idx = event.data.decode().split(':',1)[1]
    config = whatsapp_config.get(chat_id)
    if not config:
        await event.respond("Ya la configuración finalizó")
        return
    if idx in config['ids_destino']:
        config['ids_destino'].remove(idx)
        newText = "✅ Agregar"
    else:
        config['ids_destino'].append(idx)
        newText = "❌ Eliminar"
    try:
        await event.edit(buttons=[[Button.inline(newText, data=f"toggle_whatsapp:{idx}")]])
    except Exception as e:
        if "Content of the message was not modified" in str(e):
            pass
        else:
            print("Error al editar el mensaje:", e)
    await event.answer("¡Actualizado!")
@bot.on(events.CallbackQuery(pattern = "end_whatsapp"))
async def GetIntervalToWhatsapp(event):
    chat_id = event.chat_id
    if chat_id not in whatsapp_config:
        await event.respond("Ya la configuración finalizó")
    await event.respond("Ahora ,por favor envie el intervalo de reenvio en minutos ")
@bot.on(events.NewMessage(func = lambda e: (e.chat_id in whatsapp_config and e.text and e.text.isdigit())))
async def Finish_process_to_whatsapp(event):
    chat_id = event.chat_id
    data = {
        "chat_id": chat_id,
        "ids_destino": whatsapp_config[chat_id]['ids_destino'],
        "caption" : whatsapp_config[chat_id]['caption'],
        "intervalo" : int(event.text),
        "imagen" : whatsapp_config[chat_id]['imagen']
    }
    token = await auth_manager.get_token(chat_id)
    if not token:
        event.respond("No esta conectado al bot , por favor conectese y comience de nuevo")
        return
    headers = {
        'Authorization' : f"Bearer {token}",
        'Content_Type' : 'application/json'
    }
    status_code ,response = await processWhatsapp().CreateConfigToWhatsapp("https://apibotmassive-production.up.railway.app/massive-forward/createConfig" , data , headers)
    if status_code == 401:
        await event.respond("El usuario no esta conectado , por favor conectese al bot y comience de nuevo")
        return 
    if status_code != 201:
        del whatsapp_config[chat_id]
        await event.respond("Hubo un error al crear la configuración , por favor comience con el proceso de nuevo")
        return
    del whatsapp_config[chat_id]
    await event.respond("Configuración creada correctamente ,se reenviará automáticamente")
    
    
# Iniciar el bot
if __name__ == "__main__":
    print("Bot iniciado...")
    loop = asyncio.get_event_loop()
    loop.create_task(MessageProcess())
    ''' threading.Thread(target= monitor_payments , daemon = True).start() '''
    bot.run_until_disconnected()
