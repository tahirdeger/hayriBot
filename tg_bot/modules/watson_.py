import json
from pprint import pprint
import requests
from telegram import Update, Bot
from telegram.ext import CommandHandler

from tg_bot import dispatcher
from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator


authenticator = IAMAuthenticator('api_Key')
assistant = AssistantV2(
    version='2020-04-01',
    authenticator = authenticator
)

assistant.set_service_url('service_url')

def konus(bot: Bot, update: Update):
    if update.effective_message:
        msg = update.effective_message
        words = msg.text
        if len(words) > 3:
            response = assistant.message_stateless(
                assistant_id='asistant_id',
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
