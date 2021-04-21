import html
import re
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, MessageHandler, Filters, run_async

import tg_bot.modules.sql.blacklist_sql as sql
from tg_bot import dispatcher, LOGGER
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import user_admin, user_not_admin
from tg_bot.modules.helper_funcs.extraction import extract_text
from tg_bot.modules.helper_funcs.misc import split_message

BLACKLIST_GROUP = 11

BASE_BLACKLIST_STRING = "Mevcut <b>kara listedeki</b> kelimeler:\n"


@user_admin
@run_async
def blacklist(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]

    all_blacklisted = sql.get_chat_blacklist(chat.id)

    filter_list = BASE_BLACKLIST_STRING

    if len(args) > 0 and args[0].lower() == 'copy':
        for trigger in all_blacklisted:
            filter_list += "<code>{}</code>\n".format(html.escape(trigger))
    else:
        for trigger in all_blacklisted:
            filter_list += " - <code>{}</code>\n".format(html.escape(trigger))

    split_text = split_message(filter_list)
    for text in split_text:
        if text == BASE_BLACKLIST_STRING:
            msg.reply_text("Burada kara listeye alınmış mesaj yok!")
            return
        msg.reply_text(text, parse_mode=ParseMode.HTML)


@run_async
@user_admin
def add_blacklist(bot: Bot, update: Update):
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


@run_async
@user_admin
def unblacklist(bot: Bot, update: Update):
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    words = msg.text.split(None, 1)
    if len(words) > 1:
        text = words[1]
        to_unblacklist = list(set(trigger.strip() for trigger in text.split("\n") if trigger.strip()))
        successful = 0
        for trigger in to_unblacklist:
            success = sql.rm_from_blacklist(chat.id, trigger.lower())
            if success:
                successful += 1

        if len(to_unblacklist) == 1:
            if successful:
                msg.reply_text("Tetikleyici <code>{}</code> kara listeden kaldırıldı!".format(html.escape(to_unblacklist[0])),
                               parse_mode=ParseMode.HTML)
            else:
                msg.reply_text("Bu kara listeye alınmış bir tetikleyici değil...!")

        elif successful == len(to_unblacklist):
            msg.reply_text(
                "Tetikleyici <code>{}</code> kara listeden kaldırıldı.".format(
                    successful), parse_mode=ParseMode.HTML)

        elif not successful:
            msg.reply_text(
                "Bu tetikleyicilerin hiçbiri mevcut olmadığı için kaldırılmadılar.".format(
                    successful, len(to_unblacklist) - successful), parse_mode=ParseMode.HTML)

        else:
            msg.reply_text(
                "Tetikleyici <code>{}</code> kara listeden kaldırıldı. {} yoktu,  "
                "bu yüzden kaldırılmadı.".format(successful, len(to_unblacklist) - successful),
                parse_mode=ParseMode.HTML)
    else:
        msg.reply_text("Kara listeden hangi kelimeleri çıkarmak istediğini söyle.")


@run_async
@user_not_admin
def del_blacklist(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]
    to_match = extract_text(message)
    if not to_match:
        return

    chat_filters = sql.get_chat_blacklist(chat.id)
    for trigger in chat_filters:
        pattern = r"( |^|[^\w])" + re.escape(trigger) + r"( |$|[^\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            try:
                message.delete()
            except BadRequest as excp:
                if excp.message == "Message to delete not found":
                    pass
                else:
                    LOGGER.exception("Error while deleting blacklist message.")
            break


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    blacklisted = sql.num_blacklist_chat_filters(chat_id)
    return "Kara listeye alınmış {} kelime var.".format(blacklisted)


def __stats__():
    return "{} sohbet genelinde {} kara liste kelimesi oldu.".format(sql.num_blacklist_filters(),
                                                            sql.num_blacklist_filter_chats())


__mod_name__ = "Kelime karaliste"

__help__ = """
Kara listeler, bir grupta belirli kelimelerin söylenmesini durdurmak için kullanılır. Bu kelimelerden her bahsedildiğinde, \
hemen o mesaj silinir. Bazen bunu uyarı filtreleriyle eşleştirmek iyi bir kombinasyondur!

*Not:* Kara listeler grup yöneticilerini etkilemez.

*Sadece yöneticiler:*
 - /karaliste: Kara listeye alınmış mevcut kelimleleri gösterir.
 - /eklekaraliste <tetikleyici>: Kara listeye bir tetikleyici ekleyin. Her satır bir tetikleyici olarak kabul edilir, dolayısıyla farklı \
satırlar birden fazla tetikleyici eklemenize izin verir.
 - /kaldirkaraliste <tetikleyici>: Kara listeden tetikleyicileri kaldırın. Aynı satırsonu mantığı burada da geçerlidir, böylece \
aynı anda birden fazla tetikleyici kullanılmış olur
 - /silkaraliste <tetikleyici>: Bir önceki ile aynı.
"""

BLACKLIST_HANDLER = DisableAbleCommandHandler("karaliste", blacklist, filters=Filters.group, pass_args=True,
                                              admin_ok=True)
ADD_BLACKLIST_HANDLER = CommandHandler("eklekaraliste", add_blacklist, filters=Filters.group)
UNBLACKLIST_HANDLER = CommandHandler(["kaldirkaraliste", "silkaraliste"], unblacklist, filters=Filters.group)
BLACKLIST_DEL_HANDLER = MessageHandler(
    (Filters.text | Filters.command | Filters.sticker | Filters.photo) & Filters.group, del_blacklist, edited_updates=True)

dispatcher.add_handler(BLACKLIST_HANDLER)
dispatcher.add_handler(ADD_BLACKLIST_HANDLER)
dispatcher.add_handler(UNBLACKLIST_HANDLER)
dispatcher.add_handler(BLACKLIST_DEL_HANDLER, group=BLACKLIST_GROUP)
