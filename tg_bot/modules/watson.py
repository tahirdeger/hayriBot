import json
from pprint import pprint
import requests
from telegram import Update, Bot
from telegram.ext import CommandHandler

from tg_bot import dispatcher
from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

authenticator = IAMAuthenticator('s4DEE-T7yliXpCwOY4DQLH-2DAHN46GIxRGlH1qa0uD7')
assistant = AssistantV2(
    version='2020-04-01',
    authenticator = authenticator
)

assistant.set_service_url('https://api.eu-gb.assistant.watson.cloud.ibm.com/')


def konus(bot: Bot, update: Update):
    if update.effective_message:
        msg = update.effective_chat
        words = msg.text.split(None, 1)
        if len(words) > 3:
            response = assistant.message_stateless(
                assistant_id='f2d87901-432b-4d62-923d-586e036bb189',
                input={
                    'message_type': 'text',
                    'text': words
                }
            ).get_result()

            curr_string=response["output"]["generic"][0]["text"]
            #print(json.dumps(response, indent=2))
            print(curr_string)
            update.effective_message.reply_text(curr_string)
        else:
            msg.reply_text("Benimle konuşmak istediğini açıkça söyle, çekinme!.")

__help__ = """
 - /hayri: Hayri'nin yapay zekası ile sohbet edin
"""

__mod_name__ = "Konuş Hayri"

KONUSHAYRI_HANDLER = CommandHandler('hayri', konus)

dispatcher.add_handler(KONUSHAYRI_HANDLER)


msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    words = msg.text.split(None, 1)
    if len(words) > 1:
        text = words[1]
        to_blacklist = list(set(trigger.strip() for trigger in text.split("\n") if trigger.strip()))
        for trigger in to_blacklist:
            sql.add_to_blacklist(chat.id, trigger.lower())

        if len(to_blacklist) == 1:
            msg.reply_text("Kara listeye <code>{}</code> eklendi!".format(html.escape(to_blacklist[0])),
                           parse_mode=ParseMode.HTML)

        else:
            msg.reply_text(
                "Kara listeye <code>{}</code> eklendi.".format(len(to_blacklist)), parse_mode=ParseMode.HTML)

    else:
        msg.reply_text("Kara listeye hangi kelimeleri eklemek istediğini söyle.")