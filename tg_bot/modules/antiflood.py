import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import Filters, MessageHandler, CommandHandler, run_async
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher
from tg_bot.modules.helper_funcs.chat_status import is_user_admin, user_admin, can_restrict
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.sql import antiflood_sql as sql

FLOOD_GROUP = 3


@run_async
@loggable
def check_flood(bot: Bot, update: Update) -> str:
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]

    if not user:  # ignore channels
        return ""

    # ignore admins
    if is_user_admin(chat, user.id):
        sql.update_flood(chat.id, None)
        return ""

    should_ban = sql.update_flood(chat.id, user.id)
    if not should_ban:
        return ""

    try:
        chat.kick_member(user.id)
        msg.reply_text("Böyle ağzına geleni söylemek, seriye bağlamak biraz ayıp olmuyor mu?? "
                       "Bana verilen yetkiye göre seni durdurmak zorundayım.")

        return "<b>{}:</b>" \
               "\n#BANNED" \
               "\n<b>Vatandaş:</b> {}" \
               "\nseriye bağladı, durdurulması gerekiyordu.".format(html.escape(chat.title),
                                             mention_html(user.id, user.first_name))

    except BadRequest:
        msg.reply_text("Burada insanları tekmeleyemem, önce bana izin ver! O zamana kadar, seri mesajı devre dışı bırakacağım.")
        sql.set_flood(chat.id, 0)
        return "<b>{}:</b>" \
               "\n#INFO" \
               "\nTekme izinlerine sahip değilsiniz, bu nedenle seri mesaj önleyici otomatik olarak devre dışı bırakıldı.".format(chat.title)


@run_async
@user_admin
@can_restrict
@loggable
def set_flood(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    if len(args) >= 1:
        val = args[0].lower()
        if val == "kapat" or val == "yok" or val == "0":
            sql.set_flood(chat.id, 0)
            message.reply_text("Seri mesaj devre dışı bırakıldı.")

        elif val.isdigit():
            amount = int(val)
            if amount <= 0:
                sql.set_flood(chat.id, 0)
                message.reply_text("Seri mesaj devre dışı bırakıldı.")
                return "<b>{}:</b>" \
                       "\n#SETFLOOD" \
                       "\n<b>Yönetici:</b> {}" \
                       "\nDevre dışı bırakıldı.".format(html.escape(chat.title), mention_html(user.id, user.first_name))

            elif amount < 3:
                message.reply_text("Seri mesaj ayarı, 0 (devre dışı) veya 3'ten büyük bir sayı olmalıdır!")
                return ""

            else:
                sql.set_flood(chat.id, amount)
                message.reply_text("Seri mesaj limiti şuna ayarlandı: {}".format(amount))
                return "<b>{}:</b>" \
                       "\n#SETFLOOD" \
                       "\n<b>Yönetici:</b> {}" \
                       "\nSeri mesaj ayarlandı:  <code>{}</code>.".format(html.escape(chat.title),
                                                                    mention_html(user.id, user.first_name), amount)

        else:
            message.reply_text("Tanınmayan argüman - lütfen girdiğiniz bilgiler şunlar olsun - sayı , 'kapat' , 'yok'.")

    return ""


@run_async
def flood(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]

    limit = sql.get_flood_limit(chat.id)
    if limit == 0:
        update.effective_message.reply_text("Şu anda seri mesaj kontrolünü uygulamıyorum!")
    else:
        update.effective_message.reply_text(
            "Art arda {} mesajdan fazlasını gönderen kullanıcıları şu anda yasaklıyorum".format(limit))


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    limit = sql.get_flood_limit(chat_id)
    if limit == 0:
        return "Mevcut bir seri mesaj limiti *yok*"
    else:
        return "Seri mesaj limiti `{}` adettir. Fazlasını yazarsanız bozuşuruz.".format(limit)


__help__ = """
 - /serimesaj: Mevcut taşkın kontrol ayarını alın

*Sadece yöneticiler:*
 - /serimesajayarla <sayi/'yok'/'kapat'>: Seri mesaj ayarlarını etkinleştirir veya devre dışı bırakır
"""

__mod_name__ = "Seri Mesaj"

FLOOD_BAN_HANDLER = MessageHandler(Filters.all & ~Filters.status_update & Filters.group, check_flood)
SET_FLOOD_HANDLER = CommandHandler("serimesajayarla", set_flood, pass_args=True, filters=Filters.group)
FLOOD_HANDLER = CommandHandler("serimesaj", flood, filters=Filters.group)

dispatcher.add_handler(FLOOD_BAN_HANDLER, FLOOD_GROUP)
dispatcher.add_handler(SET_FLOOD_HANDLER)
dispatcher.add_handler(FLOOD_HANDLER)
