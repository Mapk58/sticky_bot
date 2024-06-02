import telebot
import os
from user_manager import Users
from telebot import types
import time

for path in ['images', 'users', 'credentials']:
    if not os.path.exists(path):
        os.makedirs(path)

TOKEN = open('credentials/token.txt', 'r').readline().strip()
bot = telebot.TeleBot(TOKEN)

users = Users('users', 'images')

@bot.message_handler(commands=['start'], func=lambda message: users.get(message.from_user.id)['status'] == 'start')
def send_welcome(message):
    bot.reply_to(message, "Привет! Этот бот нужен, чтобы собирать все твои стикеры в стикерпак для печати. Пожалуйста, отправь первый стикер.")
    users.set_status(message.from_user.id, 'sending_images')

@bot.message_handler(commands=['start'], func=lambda message: users.get(message.from_user.id)['status'] != 'start')
def send_welcome(message):
    bot.reply_to(message, "/start")

@bot.message_handler(content_types=['document', 'sticker', 'photo'], func=lambda message: users.get(message.from_user.id)['status'] == 'sending_images')
def handle_stickers(message):
    file_id = ''
    if message.content_type == 'document' and message.document.mime_type in ['image/png', 'image/jpeg', 'image/jpg', 'image/webp', 'image/bmp']:
        file_id = message.document.file_id
    elif message.content_type == 'sticker' and not message.sticker.is_animated and not message.sticker.is_video:
        file_id = message.sticker.file_id
    elif message.content_type == 'photo':
        file_id = message.photo[-1].file_id
    # else:
    #     # bot.reply_to(message, "Если вы видите это сообщение, то что-то пошло не так. Необходима консультация специалиста.")
    #     pass

    if file_id:
        image_path = save_image(file_id, message)
        bot.delete_message(message.chat.id, message.message_id)

        markup = types.InlineKeyboardMarkup()
        buttons = [
            types.InlineKeyboardButton("🗑", callback_data=f"delete_{message.message_id}"),
            types.InlineKeyboardButton("➖", callback_data=f"size_dec_{message.message_id}"),
            types.InlineKeyboardButton("➕", callback_data=f"size_inc_{message.message_id}")
        ]
        markup.row(*buttons)
        message_sent = bot.send_photo(message.chat.id, open("error.jpg", 'rb'), reply_markup=None)
        image = users.add_image(message.chat.id, {'path' : image_path, 'message' : message_sent.message_id})
        time.sleep(1)
        bot.edit_message_media(types.InputMediaPhoto(image), message.chat.id, message_sent.message_id, reply_markup=markup)

        # message_sent = bot.send_document(message.chat.id, open(image_path, 'rb'), reply_markup=markup)

    else:
        bot.reply_to(message, "Этот тип файла не поддерживается.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_'))
def query_handler(call):
    message_id = int(call.data.split('_')[1])
    users.delete_image(call.message.chat.id, call.message.message_id)
    bot.delete_message(call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('size_'))
def query_handler(call):
    message_id = int(call.data.split('_')[2])
    increase = call.data.split('_')[1] == "inc"
    image = users.change_image(call.message.chat.id, call.message.message_id, increase)
    markup = types.InlineKeyboardMarkup()
    buttons = [
        types.InlineKeyboardButton("🗑", callback_data=f"delete_{call.message.message_id}"),
        types.InlineKeyboardButton("➖", callback_data=f"size_dec_{call.message.message_id}"),
        types.InlineKeyboardButton("➕", callback_data=f"size_inc_{call.message.message_id}")
    ]
    markup.row(*buttons)
    bot.edit_message_media(types.InputMediaPhoto(image), call.message.chat.id, call.message.message_id, reply_markup=markup)
    
@bot.message_handler(commands=['finish'], func=lambda message: users.get(message.from_user.id)['status'] == 'sending_images')
def send_welcome(message):
    bot.reply_to(message, "Пожалуйста, ожидайте...")
    users.set_status(message.from_user.id, 'waiting_for_result')
    messages = users.get(message.from_user.id)['images'].keys()
    for message_id in messages:
        bot.edit_message_reply_markup(message.chat.id, message_id, message, None)


def save_image(file_id, message):
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    image_name = os.path.join(f"images", str(message.from_user.id), f"{file_id}.png")   

    with open(image_name, 'wb') as new_file:
        new_file.write(downloaded_file)
    
    return image_name

bot.infinity_polling()