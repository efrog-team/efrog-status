from os import environ
from telebot import TeleBot
from dotenv import load_dotenv
from requests import get
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from threading import Thread
from socket import create_connection, error

app = FastAPI()

@app.get("/")
async def root():
    return {}

load_dotenv('.env')
BOT_TOKEN = environ.get('BOT_TOKEN')
bot = TeleBot(BOT_TOKEN)

notification_list = {
    int(environ.get('ADMIN_ID')): True
}

def get_status():
    server_status = True
    nginx_status = True
    try:
        sock = create_connection((environ.get('SERVER_IP'), 80), timeout=1)
        sock.close()
    except error as e:
        nginx_status = False
        if e.errno != 111:
            server_status = False
    api_status = True
    try:
        api_status = get(environ.get('API_URL'),timeout=1).status_code < 500
    except:
        api_status = False
    auth_status = True
    try:
        auth_status = get(environ.get('AUTH_URL'),timeout=1).status_code < 500
    except:
        auth_status = False
    frontend_status = True
    try:
        frontend_status = get(environ.get('FRONTEND_URL'),timeout=1).status_code < 500
    except:
        frontend_status = False
    return {
        'server': server_status,
        'nginx': nginx_status,
        'api': api_status,
        'auth': auth_status,
        'frontend': frontend_status
    }

def send_status(id, status):
    bot.send_message(id, "\n".join([
        f"Server ({environ.get('SERVER_IP')}):\n    {'✅ Accessible' if status['server'] else '❌ Inaccessible'}",
        f"NGINX ({environ.get('SERVER_IP')}:80):\n    {'✅ Accessible' if status['nginx'] else '❌ Inaccessible'}",
        f"API ({environ.get('API_URL')}):\n    {'✅ Accessible' if status['api'] else '❌ Inaccessible'}",
        f"Auth ({environ.get('AUTH_URL')}):\n    {'✅ Accessible' if status['auth'] else '❌ Inaccessible'}",
        f"Front-end ({environ.get('FRONTEND_URL')}):\n    {'✅ Accessible' if status['frontend'] else '❌ Inaccessible'}"
    ]), disable_web_page_preview=True)

def check_status():
    status = get_status()
    if False in status.values():
        for id in notification_list:
            send_status(id, status)

sched = BackgroundScheduler()
sched.add_job(check_status, trigger='cron', minute='*/30')
sched.start()

@bot.message_handler(commands=['start', 'status'])
def send_status_message(message):
    send_status(message.from_user.id, get_status())

@bot.message_handler(commands=['add_notification'])
def add_notification(message):
    notification_list[message.from_user.id] = True
    bot.send_message(message.from_user.id, 'You are added to the notification list')

@bot.message_handler(commands=['check_notification'])
def check_notification(message):
    if message.from_user.id in notification_list:
        bot.send_message(message.from_user.id, 'You are in the notification list')
    else:
        bot.send_message(message.from_user.id, 'You are not in the notification list')

@bot.message_handler(commands=['remove_notification'])
def remove_notification(message):
    if message.from_user.id in notification_list:
        del notification_list[message.from_user.id]
        bot.send_message(message.from_user.id, 'You are removed from the notification list')
    else:
        bot.send_message(message.from_user.id, 'You are not in the notification list')

Thread(target=bot.infinity_polling).start()