import os
import config
import messages
import logger
import re
import base64
import schedule
import datetime
import time
import threading

from cryptography.fernet import Fernet

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

log = logger.getLogger(__name__)
bot = None

active_users = []
users_data = []
users_keys = {}

HELP, LIST, GET_KEY, START_GET_RECIPIENT, GET_RECIPIENT, GET_LETTER, START_DELETE, GET_DELETE_RECIPIENT, CONFIRM_DELETE = range(9)

def setup_workdir():
    try:
        os.mkdir(config.WORKDIR)
    except FileExistsError:
        pass

def scheduled_job():
    today = datetime.date.today()
    if today.day != 31 or today.month != 12:
        return

    sendout_and_delete_messages()

def sendout_and_delete_messages():
    for root, dirs, files in os.walk(config.WORKDIR):
        for fname in files:
            if fname.startswith("text"):
                with open(os.path.join(root, fname), 'rb') as f:
                    content = f.read()
                    match = re.compile(r'text(.+?)#(.+?).enc').match(fname)
                    From = match.group(1)
                    To = match.group(2)
                    content = "Message from anonymous:\n\n" + decrypt_content(content, users_keys[From])
                    sendMessageViaUserId(int(To), content)
                    log.info("Sent letter from {} to {}".format(From, To))

    for root, dirs, files in os.walk(config.WORKDIR):
        for fname in files:
            if os.path.exists(os.path.join(root, fname)):
                os.remove(os.path.join(root, fname))

def encrypt_message(msg, key):
    msg = msg.encode('utf-8')
    f = Fernet(key)
    new_message = f.encrypt(msg)

    return new_message

def decrypt_content(msg, key):
    f = Fernet(key)
    new_message = f.decrypt(msg)

    return new_message.decode('utf-8')

def prepare_keyboard(lst):
    res = []
    tmp = []
    for item in lst:
        item = getUserDict(item)
        if len(tmp) == 2:
            res.append(tmp)
            tmp = []

        if len(tmp) == 1 or len(tmp) == 0:
            if item['username'] != "":
                string = item['username'] + ' - ' + item['firstname']
            else:
                string = item['name']
            tmp.append(string)

    res.append(tmp)

    return res

def getUserDict(text):
    for user in users_data:
        if user['userid'] == text or user['username'] == text or user['name'] == users_data:
            return user

def getUser(update):
    return update.message.from_user

def sendMessageViaUserId(userid, text):
    bot.sendMessage(chat_id=userid, text=text)

def reply_to_user(update, text):
    update.message.reply_text(text, parse_mode='MarkdownV2')

def reply_with_keyboard(update, keyboard, text=''):
    update.message.reply_text(
            text,
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )

def write_active_users_to_file():
    with open('active_users', 'w') as f:
        f.write('\n'.join(active_users))

def add_userid_to_file(userid):
    if userid not in active_users:
        active_users.append(userid)
        write_active_users_to_file()

def notify_other_active_users(userid, name):
    for user in active_users:
        if userid == user:
            continue
        sendMessageViaUserId(user, "The {} has joined the bot, you can send him/her a secret message".format(name))
        log.debug("The user with id {} is notified about {}".format(user, name))

def getName(userid):
    for userdict in users_data:
        if userdict['userid'] == userid:
            return userdict['name']

def get_and_save_encryption_key(update, context):
    key = update.message.text.split('\n')[0].encode('utf-8')
    orig_key = key
    while len(key) < 32:
        key += orig_key
    
    key = key[:32]
    new_key = base64.b64encode(key)
    user = update.message.from_user
    users_keys[str(user['id'])] = new_key

    reply_to_user(update, "Thanks\\! I'll use this key to encrypt the messages so that even the author of the bot won't be able to read them\\!")

    return ConversationHandler.END

def simple_send():
    for user in active_users:
        sendMessageViaUserId(user, "Hello!")

def setup_schedule():
    schedule.every().day.at("18:01").do(scheduled_job)
    while True:
        schedule.run_pending()
        time.sleep(1)

def setup():
    global bot
    setup_workdir()
    updater = Updater(config.BOTTOKEN, use_context=True)
    bot = updater.bot
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start), 
            CommandHandler('help', gethelp),
            CommandHandler('list', list_active_users),
            CommandHandler('letter', letter),
            CommandHandler('delete', start_delete),
            CommandHandler('send', send_messages),
            ],
        states = {
            GET_KEY: [MessageHandler(Filters.text, get_and_save_encryption_key)],
            GET_RECIPIENT: [MessageHandler(Filters.text, get_recipient)],
            GET_LETTER: [MessageHandler(Filters.text, get_message)],
            GET_DELETE_RECIPIENT: [MessageHandler(Filters.text, get_delete_recipient)],
            CONFIRM_DELETE: [MessageHandler(Filters.regex(r'^(Yes|No)'), confirm_delete_message)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(conv_handler)

    t = threading.Thread(target=setup_schedule, args=())
    t.start()

    updater.start_polling()
    updater.idle()


def start(update: Update, context: CallbackContext) -> int:
    user = getUser(update)
    log.info("User with userid {} and username {} connected to bot".format(user['id'], user['username']))
    add_userid_to_file(str(user['id']))

    context.user_data['letter_to'] = []
    userdict = {
            'userid': str(user['id']),
            'username': user['username'],
            'firstname': user['first_name'],
            'lastname': user['last_name'],
            'name': user.full_name
    }
    notify_other_active_users(userdict['userid'], userdict['name'])

    users_data.append(userdict)
    reply_to_user(update, messages.START)

    return GET_KEY

def gethelp(update, context):
    reply_to_user(update, messages.HELP)
    return ConversationHandler.END

def list_active_users(update, context):
    userlist = ""
    for user in active_users:
        userlist += "\\+ " + getName(user)

    prepared_message = \
        "Okay, these people are ready to accept secret letters:\n" + userlist

    reply_to_user(update, prepared_message)
    return ConversationHandler.END

def letter(update, context):
    keyboard = prepare_keyboard(active_users)
    log.debug("The keyboard looks like this: {}".format(keyboard))
    reply_with_keyboard(update, keyboard, messages.PROMPT_TO_GET_RECIPIENT)

    return GET_RECIPIENT

def get_recipient(update, context):
    text = update.message.text.split(" - ")[0]
    userdict = getUserDict(text)
    if userdict is not None:
        context.user_data['recipient'] = userdict['userid']
        reply_to_user(update, messages.PROMPT_TO_GET_LETTER)
        return GET_LETTER
    else:
        reply_to_user(update, messages.TRY_AGAIN_RECIPIENT)
        return GET_RECIPIENT

def get_message(update, context):
    message = update.message.text
    user = update.message.from_user

    message = encrypt_message(message, users_keys[str(user['id'])])
    path = os.path.join(config.WORKDIR, "text{}#{}.enc".format(user['id'], context.user_data['recipient']))

    with open(path, 'wb') as f:
        f.write(message)
    
    reply_to_user(update, messages.GET_MESSAGE)

    letter_to = context.user_data['letter_to']
    if context.user_data['recipient'] not in letter_to:
        letter_to.append(context.user_data['recipient'])

    return ConversationHandler.END

def start_delete(update, context):
    if len(context.user_data['letter_to']) == 0:
        reply_to_user(update, messages.NO_MESSAGES_TO_DELETE)
        return ConversationHandler.END

    keyboard = prepare_keyboard(context.user_data['letter_to'])
    reply_with_keyboard(update, keyboard, text=messages.START_DELETE)

    return GET_DELETE_RECIPIENT

def get_delete_recipient(update, context):
    text = update.message.text.split(" - ")[0]
    userdict = getUserDict(text)

    if userdict is not None:
        context.user_data['delete_recipient'] = userdict['userid']
        keyboard = [['Yes', 'No']]
        reply_with_keyboard(update, keyboard, messages.CONFIRM_DELETE)

        return CONFIRM_DELETE
    else:
        keyboard = prepare_keyboard(context.user_data['letter_to'])
        reply_with_keyboard(update, keyboard, text=messages.TRY_AGAIN_DELETE_RECIPIENT)

        return GET_DELETE_RECIPIENT

def confirm_delete_message(update, context):
    text = update.message.text
    if text == "Yes":
        filename = "text{}#{}.enc".format(update.message.from_user['id'], context.user_data['delete_recipient'])
        context.user_data['letter_to'].remove(context.user_data['delete_recipient'])
        log.debug("The letter_to is {} and the context.user_data['delete_recipient'] is {}".format(context.user_data['letter_to'], context.user_data['delete_recipient']))
        context.user_data['delete_recipient'] = ''
        path = os.path.join(config.WORKDIR, filename)

        if os.path.exists(path):
            os.remove(path)
        reply_to_user(update, messages.DELETED_LETTER)
    else:
        reply_to_user(update, messages.DIDNT_DELETE)

    return ConversationHandler.END

def cancel(update, context):
    reply_to_user(update, "Okay, operation canceled.")
    return ConversationHandler.END

def send_messages(update, context):
    user = update.message.from_user
    if user['username'] != "KtlTheBest":
        reply_to_user(update, "Sorry, you are not allowed to use this command")
        return ConversationHandler.END

    sendout_and_delete_messages()
    return ConversationHandler.END

def main():
    setup()
    return

if __name__ == "__main__":
    main()
