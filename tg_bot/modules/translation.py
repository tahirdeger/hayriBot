from telegram import Update, Bot
from telegram.ext import CommandHandler
from tg_bot import dispatcher

import json
from pprint import pprint
from ibm_watson import LanguageTranslatorV3
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

authenticator = IAMAuthenticator('kGVQ8CrGoEQKkCQcIkhqu-I9EbJypmocv2Yk2wxlbPHt')
language_translator = LanguageTranslatorV3(
    version='2018-05-01',
    authenticator=authenticator
)

language_translator.set_service_url('https://api.eu-gb.language-translator.watson.cloud.ibm.com/instances/991db3f0-f0de-4c50-8dd5-415a9b8e74ce')

def translatetr(bot: Bot, update: Update):
    if update.effective_message.reply_to_message:
        msg = update.effective_message.reply_to_message
        words = msg.text
        translation = language_translator.translate(
            text= words,
            model_id='tr-en').get_result()        
        #print(json.dumps(translation, indent=2, ensure_ascii=False))
        curr_string = translation["translations"][0]["translation"]
        print(curr_string)
        update.effective_message.reply_text(curr_string)

def translatein(bot: Bot, update: Update):
    if update.effective_message.reply_to_message:
        msg = update.effective_message.reply_to_message
        words = msg.text
        translation = language_translator.translate(
            text= words,
            model_id='en-tr').get_result()        
        #print(json.dumps(translation, indent=2, ensure_ascii=False))
        curr_string = translation["translations"][0]["translation"]
        print(curr_string)
        update.effective_message.reply_text(curr_string)

__help__ = """
 - /cevirtr: Bir mesajı yanıtlayın, dilbilgisi düzeltilmiş bir versiyonla size ingilizcesini vereyim. Bu kıyağımı unutmayın
 - /cevirin: Bir mesajı yanıtlayın, dilbilgisi düzeltilmiş bir versiyonla size Türkçe'sini vereyim. Bu kıyağımı da unutmayın
"""

__mod_name__ = "İngilizce çeviri"


TRANSLATE_TR_HANDLER = CommandHandler('cevirtr', translatetr)
TRANSLATE_EN_HANDLER = CommandHandler('cevirin', translatein)

dispatcher.add_handler(TRANSLATE_TR_HANDLER)
dispatcher.add_handler(TRANSLATE_EN_HANDLER)