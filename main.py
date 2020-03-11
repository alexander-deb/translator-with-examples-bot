import telebot
import shelve
import telegram
import requests
import os
from bs4 import BeautifulSoup
from config import TG_TOKEN

TG_TOKEN = os.getenv('TG_TOKEN')

bot = telebot.TeleBot(TG_TOKEN)

flag = False
list_of_languages = [
'🇦🇪Arabic',
'🇩🇪German',
'🇬🇧English',
'🇪🇸Spanish',
'🇫🇷French',
'🇮🇱Hebrew',
'🇯🇵Japanese',
'🇳🇱Dutch',
'🇵🇱Polish',
'🇵🇹Portuguese',
'🇷🇴Romanian',
'🇷🇺Russian',
'🇹🇷Turkish'
]

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(chat_id=message.chat.id, text='Change languages')
    with shelve.open('assets/Mods') as file:
        file[str(message.from_user.id)] = ['', '']



@bot.callback_query_handler(func=lambda call:True)
def query_handler(call):
    global flag
    if flag:
        bot.answer_callback_query(callback_query_id=call.id, text=f'You succesfully changed second language to {call.data}')
        second_language = call.data[2:]
        with shelve.open('assets/Mods') as file:
            file[str(call.from_user.id)] = [file[str(call.from_user.id)][0], second_language]
    else:
        bot.answer_callback_query(callback_query_id=call.id, text=f'You succesfully changed first language to {call.data}')
        first_language = call.data[2:]
        with shelve.open('assets/Mods') as file:
            file[str(call.from_user.id)] = [first_language, file[str(call.from_user.id)][1]]


    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)


@bot.message_handler(commands=['change_first_lang'])
def change_first_lang(message):
    global list_of_languages, flag
    markup = telebot.types.InlineKeyboardMarkup()
    for text in list_of_languages:
        button = telebot.types.InlineKeyboardButton(text=text, callback_data=text)
        markup.add(button)
    bot.send_message(chat_id=message.chat.id, text='Choose language from this list:', reply_markup=markup)
    bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    flag = False


@bot.message_handler(commands=['change_second_lang'])
def change_first_lang(message):
    global list_of_languages, flag
    markup = telebot.types.InlineKeyboardMarkup()
    for text in list_of_languages:
        button = telebot.types.InlineKeyboardButton(text=text, callback_data=text)
        markup.add(button)
    bot.send_message(chat_id=message.chat.id, text='Choose language from this list:', reply_markup=markup)
    bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

    flag = True


@bot.message_handler(content_types=["text"])
def send_message(message):
    text = translate_message(message)

    bot.send_message(
        chat_id=message.from_user.id,
        text=text,
        parse_mode=telegram.ParseMode.MARKDOWN
    )





def translate_message(message):
    with shelve.open('assets/Mods') as file:
        first_language = file[str(message.from_user.id)][0]
        second_language = file[str(message.from_user.id)][1]


    translation_text = ''
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
    }
    URL = f'https://context.reverso.net/translation/{first_language.lower()}-{second_language.lower()}/' + message.text.replace(" ", "+").lower().replace("'", "%27")
    translations_list, only_translations_list = [], []
    translation_text = ''
    example_text = f'*{second_language} examples:*\n\n'
    try:
        response = requests.get(URL, headers=headers) #  send request
        if response.status_code == 200:
            #print(response.status_code, 'OK')
            pass

    except requests.exceptions.ConnectionError:
        bot.send_message(
        chat_id=message.from_user.id,
        text='Something is wrong with the server. Contact support.'
        )
    soup = BeautifulSoup(response.text, "html.parser")  #  parse web page
    #  find translations with examples:
    translations_with_examples = soup.find_all(['div', 'a'], {"class": ['translation', 'src', 'trg']})
    #  find only translations of word:
    only_translations_of_word = soup.find_all(['div', 'a'], {"class": ['translation']})
    #  get text from html and format it:
    only_translations_list = []
    translations_with_examples_list = []
    for example in translations_with_examples:
        translations_with_examples_list.append(example.text.replace('\n', '').strip())
    for translation in only_translations_of_word:
        only_translations_list.append(translation.text.replace('\n', '').strip())
    #  we need see the result:
    translation_text = ''
    translations_with_examples_list = translations_with_examples_list[translations_with_examples_list.index(only_translations_list[-1])+1:]
    for translation in only_translations_list:
        if len(translation) > 0:
            if translation == 'Translation':
                translation_text += f'*\n{second_language} {translation.lower()}s:*\n'.title()
            else:
                translation_text += f'`{translation}\n`'

    #  format output for readable translations:
    i = 0
    for example in translations_with_examples_list:
        if len(example) > 0:
            i += 1
            if i % 2 == 1 and len(translation_text) != 10:
                example = '\n*{}:*'.format(example)
            elif i % 2 == 0 and len(translation_text) == 10:
                example = '\n*{}:*'.format(example)
            else:
                example = '`{}`'.format(example)
            if len(example_text) < 4096 < len(example_text + example + '\n'):
                bot.send_message(
                    chat_id=message.from_user.id,
                    text=example_text,
                    parse_mode=telegram.ParseMode.MARKDOWN
                )
                example_text = ''
            example_text += example + '\n'
    bot.send_message(
        chat_id=message.from_user.id,
        text=example_text,
        parse_mode=telegram.ParseMode.MARKDOWN
    )
    return translation_text


if __name__ == '__main__':
    bot.polling(none_stop=True)
