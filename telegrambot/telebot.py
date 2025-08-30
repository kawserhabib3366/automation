import requests


#https://api.telegram.org/bot7339400168:AAGWQcOL6epjVOMDfFtLHTwPNro17aK2yoY/getUpdates


# Replace with your actual bot token and chat ID
BOT_TOKEN = '7339400168:AAGWQcOL6epjVOMDfFtLHTwPNro17aK2yoY'
CHAT_ID = '-1002917123957'
MESSAGE = 'Hello from my bot!'

# Telegram API endpoint
url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'



def tel_alert(message):
    try:
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
        payload = {
            'chat_id': CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        res = requests.post(url, data=payload)
        print("Response:", res.json())
    except Exception as e:
        print('Error:', e)

tel_alert(MESSAGE)