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
        msg = update.effective_message
        words = msg.text
        if len(words) > 3:
            response = assistant.message_stateless(
                assistant_id='136209fb-0888-44d3-9c70-c4824fa542dd',
                input={
                    'message_type': 'text',
                    'text': words
                }
            ).get_result()

            curr_string=response["output"]["generic"][0]["text"]
            print(curr_string)
            update.effective_message.reply_text(curr_string)
    else:
        msg.reply_text("Benimle konuşmak istediğini açıkça söyle, çekinme!.")

__help__ = """
Hayri'nin yapay zekası ile sohbet edin.. Ne gibi??
Sorular sorun
Düşüncenizi paylaşın
Bakalım ne tepki alacaksınız??
 - /hayri <Cümleniz veya sorunuz>
"""

__mod_name__ = "Konuş Hayri"

KONUSHAYRI_HANDLER = CommandHandler('hayri', konus)

dispatcher.add_handler(KONUSHAYRI_HANDLER)
