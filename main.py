import logging
import requests
import json
import sqlite3
from bs4 import BeautifulSoup

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

OUT_FILENAME = 'out_json'

conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def db_table_val(brand: str, title: str, product: str):
    cursor.execute('INSERT OR REPLACE INTO data (brand, title, product) VALUES (?, ?, ?)',
                   (brand, title, product))
    conn.commit()


def dump_to_json(filename, data, **kwargs):
    kwargs.setdefault('ensure_ascii', False)
    kwargs.setdefault('indent', 1)

    with open(filename, 'w') as f:
        json.dump(data, f, **kwargs)


def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Привет! Используй /get_brand <артикул> чтобы узнать бренд, /get_title '
                              '<артикул> чтобы узнать увидеть наименование товара или /get_json <артикул> чтобы '
                              'получить бренд и намиенование товара в формате json. Например - /get_title 38567378')


def alarm(context: CallbackContext) -> None:
    job = context.job
    context.bot.send_message(job.context, text='Формат артикуля - положительное целое число. Например - 145235. '
                                               'Попробуйте еще раз.')


def get_brand(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    try:
        token = int(context.args[0])
        if token < 0:
            update.message.reply_text('Артикуль не может быть отрицательным')
            return

        fmt = f'https://www.wildberries.ru/catalog/{token}/detail.aspx'
        r = requests.get(fmt)
        soup = BeautifulSoup(r.text)

        try:
            brand_text = soup.find('div', {'class': 'same-part-kt__header-wrap hide-mobile'}).find('h1', {
                'class': 'same-part-kt__header'}).find('span', {
                'data-link': 'text{:product^brandName}'}).text
            text = brand_text
            db_table_val(brand=text, title='', product='')
            update.message.reply_text(text)
        except AttributeError:
            text = 'По вашему запросу ничего не найденно'
            update.message.reply_text(text)

        context.job_queue.run_once(alarm, token, context=chat_id, name=str(chat_id))

    except (IndexError, ValueError):
        update.message.reply_text('Неправильный формат артикуля')


def get_title(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    try:
        token = int(context.args[0])
        if token < 0:
            update.message.reply_text('Артикуль не может быть отрицательным')
            return

        fmt = f'https://www.wildberries.ru/catalog/{token}/detail.aspx'
        r = requests.get(fmt)
        soup = BeautifulSoup(r.text)

        try:
            name_text = soup.find('div', {'class': 'same-part-kt__header-wrap hide-mobile'}).find('h1', {
                'class': 'same-part-kt__header'}).find('span', {
                'data-link': 'text{:product^goodsName}'}).text
            text = name_text
            db_table_val(brand='', title=text, product='')
            update.message.reply_text(text)
        except AttributeError:
            text = 'По вашему запросу ничего не найденно'
            update.message.reply_text(text)

        context.job_queue.run_once(alarm, token, context=chat_id, name=str(chat_id))

    except (IndexError, ValueError):
        update.message.reply_text('Неправильный формат артикуля')


def get_json(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    try:
        token = int(context.args[0])
        if token < 0:
            update.message.reply_text('Артикуль не может быть отрицательным')
            return

        fmt = f'https://www.wildberries.ru/catalog/{token}/detail.aspx'
        r = requests.get(fmt)
        soup = BeautifulSoup(r.text)

        try:
            json_text = soup.find('div', {'class': 'same-part-kt__header-wrap hide-mobile'}).find('h1', {
                'class': 'same-part-kt__header'}).text
            text = json_text
            db_table_val(brand='', title='', product=text)
            with open(OUT_FILENAME, 'w', encoding='utf8') as f:
                json.dump(text, f, ensure_ascii=False)
            with open(OUT_FILENAME, 'rb') as f:
                context.bot.send_document(chat_id, document=f)
        except AttributeError:
            text = 'По вашему запросу ничего не найденно'
            update.message.reply_text(text)

        context.job_queue.run_once(alarm, token, context=chat_id, name=str(chat_id))

    except (IndexError, ValueError):
        update.message.reply_text('Неправильный формат артикуля')


def main() -> None:
    updater = Updater("2132758376:AAGkW8Wx_mdoD8HBI0ER0jQjk31VsLdGkzA")

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", start))
    dispatcher.add_handler(CommandHandler("get_brand", get_brand))
    dispatcher.add_handler(CommandHandler("get_title", get_title))
    dispatcher.add_handler(CommandHandler("get_json", get_json))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
