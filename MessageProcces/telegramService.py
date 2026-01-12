from telethon import TelegramClient
from telethon.sessions import StringSession
import asyncio
from file_manager import FileManager

async def ReSend_Message(api_id , api_hash , id_user ,session_token , message):
    print(f"📤 Conectando con {id_user} para reenviar mensaje...")
    client = TelegramClient(StringSession(session_token) , api_id , api_hash)
    try : 
        await client.connect()
        if not await client.is_user_authorized():
            print(f"⚠️ Usuario {id_user} no está autorizado, omitiendo mensaje.")
            return
        text = message["mensaje"].get("texto", "")
        get_media = message["mensaje"].get("media" , None)
        fileManager = FileManager()
        media = None
        if get_media is not None:
            media = get_media
        ids_destino = message["ids_destino"]
        Send_Task = []
        groups_cache = await cache_groups(client)
        for group_id in ids_destino:
            print(f"📨 Enviando mensaje a {group_id}...")
            entity = groups_cache.get(int(group_id))
            print(f"📨 Enviando mensaje a {entity}")
            if entity:
                print(f"📨 Enviando mensaje a {entity.title}")
            if media:
                Send_Task.append(client.send_file(entity , media , caption=text))
            else :
                Send_Task.append(client.send_message(entity , text))
        await asyncio.gather(*Send_Task)
        print(f"✅ Mensaje reenviado a {len(ids_destino)} grupos.")
    except Exception as e:
        print(f"❌ Error al reenviar mensaje: {e}")
    finally :
        client.disconnect()
async def cache_groups(client):
    dialogs = await client.get_dialogs()
    return {
        dialog.id: dialog.entity
        for dialog in dialogs
        if dialog.is_group
    }


