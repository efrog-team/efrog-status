import os
import telebot
import dotenv
import subprocess
import requests
from apscheduler.schedulers.background import BackgroundScheduler

if os.environ.get('PROD') is None:
	dotenv.load_dotenv('.env')
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

notification_list = {
    os.environ.get('ADMIN_ID'): True
}
#subprocess.run(['ping', '-n' if os.name == 'nt' else '-c', '1', os.environ.get('SERVER_IP')], stdout=subprocess.DEVNULL).returncode == 0
def get_status():
    return {
        'server': True,
        'api': requests.get(os.environ.get('API_URL')).status_code < 500,
        'auth': requests.get(os.environ.get('AUTH_URL')).status_code < 500,
        'frontend': requests.get(os.environ.get('FRONTEND_URL')).status_code < 500
    }

def send_status(id, status):
    bot.send_message(id, "\n".join([
        f"Server ({os.getenv('SERVER_IP')}): {'✅ Accessible' if status['server'] else '❌ Inaccessible'}",
        f"API ({os.getenv('API_URL')}): {'✅ Accessible' if status['api'] else '❌ Inaccessible'}",
        f"Auth ({os.getenv('AUTH_URL')}): {'✅ Accessible' if status['auth'] else '❌ Inaccessible'}",
        f"Front-end ({os.getenv('FRONTEND_URL')}): {'✅ Accessible' if status['frontend'] else '❌ Inaccessible'}"
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
    bot.send_message(message.from_user.id, 'You are added to a notification list')

@bot.message_handler(commands=['check_notification'])
def check_notification(message):
    if message.from_user.id in notification_list:
        bot.send_message(message.from_user.id, 'You are in a notification list')
    else:
        bot.send_message(message.from_user.id, 'You are not in a notification list')

@bot.message_handler(commands=['remove_notification'])
def remove_notification(message):
    if message.from_user.id in notification_list:
        del notification_list[message.from_user.id]
        bot.send_message(message.from_user.id, 'You are removed from a notification list')
    else:
        bot.send_message(message.from_user.id, 'You are not in a notification list')

bot.infinity_polling()