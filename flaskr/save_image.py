import secrets
import os
from PIL import Image
from flask import current_app as app


def save_pic(picture, avatar=True):
    """Saves an image to disk"""
    file_name = secrets.token_hex(8) + os.path.splitext(picture.filename)[1]
    if not os.path.isdir(os.path.join(app.root_path, 'static')):
        os.mkdir(os.path.join(app.root_path, "static"))
        os.mkdir(os.path.join(app.root_path, "static/images"))
        os.mkdir(os.path.join(app.root_path, "static/images/avatars"))
        os.mkdir(os.path.join(app.root_path, "static/images/autres"))
    if not os.path.isdir(os.path.join(app.root_path, 'static/images')):
        os.mkdir(os.path.join(app.root_path, "static/images"))
        os.mkdir(os.path.join(app.root_path, "static/images/avatars"))
        os.mkdir(os.path.join(app.root_path, "static/images/autres"))
    if not os.path.isdir(os.path.join(app.root_path, 'static/images/avatars')):
        os.mkdir(os.path.join(app.root_path, "static/images/avatars"))
    if not os.path.isdir(os.path.join(app.root_path, 'static/images/autres')):
        os.mkdir(os.path.join(app.root_path, "static/images/autres"))
    file_path = os.path.join(app.root_path, "static/images/avatars",
                             file_name) if avatar else os.path.join(app.root_path, "static/images/autres", file_name)
    picture = Image.open(picture)
    if avatar:
        picture.thumbnail((200, 200))
    picture.save(file_path)
    return file_name
