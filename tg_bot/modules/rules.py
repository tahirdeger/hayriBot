from typing import Optional

from telegram import Message, Update, Bot, User
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import BadRequest
from telegram.ext import CommandHandler, run_async, Filters
from telegram.utils.helpers import escape_markdown

import tg_bot.modules.sql.rules_sql as sql
from tg_bot import dispatcher
from tg_bot.modules.helper_funcs.chat_status import user_admin
from tg_bot.modules.helper_funcs.string_handling import markdown_parser


@run_async
def get_rules(bot: Bot, update: Update):
    chat_id = update.effective_chat.id
    send_rules(update, chat_id)


# Do not async - not from a handler
def send_rules(update, chat_id, from_pm=False):
    bot = dispatcher.bot
    user = update.effective_user  # type: Optional[User]
    try:
        chat = bot.get_chat(chat_id)
    except BadRequest as excp:
        if excp.message == "Chat not found" and from_pm:
            bot.send_message(user.id, "Bu sohbet için kurallar kısayolu düzgün ayarlanmadı! "
                                      "Yöneticilerden düzeltmelerini isteyin.")
            return
        else:
            raise

    rules = sql.get_rules(chat_id)
    text = "*{}* için belirlenmiş kurallar:\n\n{}".format(escape_markdown(chat.title), rules)

    if from_pm and rules:
        bot.send_message(user.id, text, parse_mode=ParseMode.MARKDOWN)
    elif from_pm:
        bot.send_message(user.id, "Grup yöneticileri henüz bu sohbet için herhangi bir kural belirlemedi. "
                                  "Bu kuralsız olduğu anlamına gelmez...!")
    elif rules:
        update.effective_message.reply_text(text,
                                            reply_markup=InlineKeyboardMarkup(
                                                [[InlineKeyboardButton(text="Hayri ile görüş",
                                                                       url="t.me/{}?start={}".format(bot.username,
                                                                                                     chat_id))]]))
    else:
        update.effective_message.reply_text("Grup yöneticileri henüz bu sohbet için herhangi bir kural belirlemedi. "
                                            "Bu kanunsuz olduğu anlamına gelmez...!")


@run_async
@user_admin
def set_rules(bot: Bot, update: Update):
    chat_id = update.effective_chat.id
    msg = update.effective_message  # type: Optional[Message]
    raw_text = msg.text
    args = raw_text.split(None, 1)  # use python's maxsplit to separate cmd and args
    if len(args) == 2:
        txt = args[1]
        offset = len(txt) - len(raw_text)  # set correct offset relative to command
        markdown_rules = markdown_parser(txt, entities=msg.parse_entities(), offset=offset)

        sql.set_rules(chat_id, markdown_rules)
        update.effective_message.reply_text("Bu grup için kurallar başarıyla belirlendi.")


@run_async
@user_admin
def clear_rules(bot: Bot, update: Update):
    chat_id = update.effective_chat.id
    sql.set_rules(chat_id, "")
    update.effective_message.reply_text("Kurallar silindi!")


def __stats__():
    return "{} sohbetin belirlenmiş kuralları var.".format(sql.num_chats())


def __import_data__(chat_id, data):
    # set chat rules
    rules = data.get('info', {}).get('rules', "")
    sql.set_rules(chat_id, rules)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return "Bu sohbetin kuralları belirlenmiş: `{}`".format(bool(sql.get_rules(chat_id)))


__help__ = """
 - /kurallar: Bu sohbetin kurallarını öğrenin.

*Sadece yöneticiler:*
 - /kuralkoy <Kurallarını yaz>: Bu sohbetin kurallarını belirleyin.
 - /kuraltemizle: Tüm kuralları siler.
"""

__mod_name__ = "Kurallar"

GET_RULES_HANDLER = CommandHandler("kurallar", get_rules, filters=Filters.group)
SET_RULES_HANDLER = CommandHandler("kuralkoy", set_rules, filters=Filters.group)
RESET_RULES_HANDLER = CommandHandler("kuraltemizle", clear_rules, filters=Filters.group)

dispatcher.add_handler(GET_RULES_HANDLER)
dispatcher.add_handler(SET_RULES_HANDLER)
dispatcher.add_handler(RESET_RULES_HANDLER)
