import os
import json
from PIL import Image, ImageDraw, ImageFont

class Users:
    def __init__(self, user_folder='users', image_folder='images') -> None:
        self.users = {}
        self.user_folder = user_folder
        self.image_folder = image_folder

    def get(self, id):
        if id in self.users.keys():
            return self.users[id]
        path = f'{self.user_folder}/{id}.json'
        if os.path.exists(path):
            return json.load(open(path))
        else:
            if not os.path.exists(f'{self.image_folder}/{id}'):
                os.makedirs(f'{self.image_folder}/{id}')
            user = {
                'id': str(id),
                'status' : 'start',
                'images' : {}
            }
            self.set(user)
            return user

    def set(self, user):
        self.users[user["id"]] = user
        with open(f'{self.user_folder}/{user["id"]}.json', 'w') as f:
            json.dump(user, f)

    def add_image(self, user_id, image):
        user = self.get(user_id)
        dimensions = max(Image.open(image['path']).convert("RGBA").size)
        user['images'][image['message']] = {'path' : image['path'], 'size' : 600/dimensions}
        self.set(user)
        return show_image_sizes(user['images'][image['message']])

    def delete_image(self, user_id, message_id):
        user = self.get(user_id)
        os.remove(user['images'][str(message_id)]['path'])
        del user['images'][str(message_id)]
        self.set(user)

    def change_image(self, user_id, message_id, increase):
        step = 1.2
        if not increase:
            step = 0.8
        user = self.get(user_id)
        user['images'][str(message_id)]['size'] *= step
        self.set(user)
        return show_image_sizes(user['images'][str(message_id)])

    def set_status(self, user_id, status):
        user = self.get(user_id)
        user['status'] = status
        self.set(user)



def show_image_sizes(image_data):
    path = image_data['path']
    size_multiplier = image_data['size']
    original_pixel_mm = 0.1
    target_width_mm = 800 * original_pixel_mm  # 800 пикселей соответствуют 80 мм (8 см)
    target_height_mm = 800 * original_pixel_mm  # 800 пикселей соответствуют 80 мм (8 см)

    # Загрузка исходного изображения
    original_image = Image.open(path).convert("RGBA")
    original_width, original_height = original_image.size

    # Вычисление новых размеров изображения с учётом мультиплаера
    new_width = int(original_width * size_multiplier * original_pixel_mm * 10)
    new_height = int(original_height * size_multiplier * original_pixel_mm * 10)

    # Изменение размера изображения
    resized_image = original_image.resize((new_width, new_height), Image.ANTIALIAS)

    # Создание нового изображения с белым фоном
    background_image = Image.new('RGBA', (800, 800), (255, 255, 255, 255))
    bg_w, bg_h = background_image.size

    # Расчет позиции для вставки изображения по центру
    offset = ((bg_w - new_width) // 2, (bg_h - new_height) // 2)
    background_image.paste(resized_image, offset, resized_image)

    # Добавление текста с размерами
    draw = ImageDraw.Draw(background_image)
    try:
        font = ImageFont.truetype('arial.ttf', size=20)
    except IOError:
        font = ImageFont.load_default()

    # Размеры фона в см
    background_size_text = "8 x 8 см"
    # Размеры изображения в см
    image_size_text = f"{new_width/100:.1f} x {new_height/100:.1f} см"

    draw.text((10, bg_h - 30), background_size_text, fill=(0,0,0,255), font=font)
    draw.text((bg_w - 150, 10), image_size_text, fill=(0,0,0,255), font=font)

    # # Сохранение итогового изображения
    # new_path = path.split('.')[0] + '_resized_and_overlayed.png'
    # background_image.save(new_path)
    # print(f'Image saved as {new_path}')

    return background_image
