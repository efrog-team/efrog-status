from os import environ
from telebot import TeleBot
from dotenv import load_dotenv
from requests import get
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from threading import Thread
from socket import create_connection

app = FastAPI()

@app.get("/keep-alive")
def keep_alive():
    return {}

load_dotenv('.env')
BOT_TOKEN = environ.get('BOT_TOKEN')
bot = TeleBot(BOT_TOKEN)

notification_list = {
    int(environ.get('ADMIN_ID')): True
}

last_status = {
    'proxy': True,
    'api': True,
    'auth': True,
    'frontend': True,
    'hub': True
}

def get_status():
    proxy_status = True
    try:
        sock = create_connection((environ.get('SERVER_IP'), 80), timeout=1)
        sock.close()
    except:
        proxy_status = False
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
    hub_status = True
    try:
        hub_status = get(environ.get('HUB_URL'),timeout=1).status_code < 500
    except:
        hub_status = False
    return {
        'proxy': proxy_status,
        'api': api_status,
        'auth': auth_status,
        'frontend': frontend_status,
        'hub': hub_status
    }

@app.get("/", response_class=HTMLResponse)
def root():
    status = get_status()
    return '<div style="font-size: 18px; font-family: monospace;">' + '<br>'.join([
        f"<span>Proxy ({environ.get('SERVER_IP')}:80):<br>{'✅ Accessible' if status['proxy'] else '❌ Inaccessible'}</span>",
        f"<span>API ({environ.get('API_URL')}):<br>{'✅ Accessible' if status['api'] else '❌ Inaccessible'}</span>",
        f"<span>Auth ({environ.get('AUTH_URL')}):<br>{'✅ Accessible' if status['auth'] else '❌ Inaccessible'}</span>",
        f"<span>Front-end ({environ.get('FRONTEND_URL')}):<br>{'✅ Accessible' if status['frontend'] else '❌ Inaccessible'}</span>",
        f"<span>Hub ({environ.get('HUB_URL')}):<br>{'✅ Accessible' if status['hub'] else '❌ Inaccessible'}</span>"
    ]) + '</div>'

def send_status(id, status):
    bot.send_message(id, '\n'.join([
        f"Proxy ({environ.get('SERVER_IP')}:80):\n{'✅ Accessible' if status['proxy'] else '❌ Inaccessible'}",
        f"API ({environ.get('API_URL')}):\n{'✅ Accessible' if status['api'] else '❌ Inaccessible'}",
        f"Auth ({environ.get('AUTH_URL')}):\n{'✅ Accessible' if status['auth'] else '❌ Inaccessible'}",
        f"Front-end ({environ.get('FRONTEND_URL')}):\n{'✅ Accessible' if status['frontend'] else '❌ Inaccessible'}",
        f"Hub ({environ.get('HUB_URL')}):\n{'✅ Accessible' if status['hub'] else '❌ Inaccessible'}"
    ]), disable_web_page_preview=True)

def check_status():
    global last_status
    status = get_status()
    if status != last_status:
        for id in notification_list:
            send_status(id, status)
    last_status = status

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

Thread(target=bot.infinity_polling, daemon=True).start()