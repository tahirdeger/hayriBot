import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher, LOGGER
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_admin, can_restrict
from tg_bot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from tg_bot.modules.helper_funcs.string_handling import extract_time
from tg_bot.modules.log_channel import loggable


@run_async
@bot_admin
@user_admin
@loggable
def mute(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("Ya sessize almam için bir kullanıcı adı vermen ya da sesi kapatılacak birine cevap vermen gerekecek.")
        return ""

    if user_id == bot.id:
        message.reply_text("Kendimi susturamıyorum!!")
        return ""

    member = chat.get_member(int(user_id))

    if member:
        if is_user_admin(chat, user_id, member=member):
            message.reply_text("Korkarım bir yöneticinin konuşmasını durduramıyorum!")

        elif member.can_send_messages is None or member.can_send_messages:
            bot.restrict_chat_member(chat.id, user_id, can_send_messages=False)
            message.reply_text("Susturdu!")
            return "<b>{}:</b>" \
                   "\n#MUTE" \
                   "\n<b>Yönetici:</b> {}" \
                   "\n<b>Kullanıcı:</b> {}".format(html.escape(chat.title),
                                              mention_html(user.id, user.first_name),
                                              mention_html(member.user.id, member.user.first_name))

        else:
            message.reply_text("Zaten susturulmuş!")
    else:
        message.reply_text("Bu kullanıcı sohbette değil!")

    return ""


@run_async
@bot_admin
@user_admin
@loggable
def unmute(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("Sesi açmak için bana bir kullanıcı adı vermeniz veya sesi açılacak birine cevap vermeniz gerekecek.")
        return ""

    member = chat.get_member(int(user_id))

    if member:
        if is_user_admin(chat, user_id, member=member):
            message.reply_text("Bu bir yönetici, ne yapmamı bekliyorsun?")
            return ""

        elif member.status != 'kicked' and member.status != 'left':
            if member.can_send_messages and member.can_send_media_messages \
                    and member.can_send_other_messages and member.can_add_web_page_previews:
                message.reply_text("Bu kullanıcının zaten konuşma hakkı var.")
                return ""
            else:
                bot.restrict_chat_member(chat.id, int(user_id),
                                         can_send_messages=True,
                                         can_send_media_messages=True,
                                         can_send_other_messages=True,
                                         can_add_web_page_previews=True)
                message.reply_text("Parmak bağları çözüldü! Tekrarı olmaz İnşallah:)")
                return "<b>{}:</b>" \
                       "\n#UNMUTE" \
                       "\n<b>Yönetici:</b> {}" \
                       "\n<b>Kullanıcı:</b> {}".format(html.escape(chat.title),
                                                  mention_html(user.id, user.first_name),
                                                  mention_html(member.user.id, member.user.first_name))
    else:
        message.reply_text("Bu kullanıcı sohbette bile değil "
                           "sesini açmak onları zaten yaptıklarından daha fazla konuşturmayacak")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def temp_mute(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Bir kullanıcıya atıfta bulunmuyorsunuz.")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Kullanıcıyı bulamadım")
            return ""
        else:
            raise

    if is_user_admin(chat, user_id, member):
        message.reply_text("Yöneticileri susturamam, atarlar beni gardaş...")
        return ""

    if user_id == bot.id:
        message.reply_text("Kendimi nasıl susturayım gardaş?")
        return ""

    if not reason:
        message.reply_text("Bu kullanıcının sesini kapatmak için bir zaman belirtmediniz!")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    mutetime = extract_time(message, time_val)

    if not mutetime:
        return ""

    log = "<b>{}:</b>" \
          "\n#TEMP MUTED" \
          "\n<b>Yönetici:</b> {}" \
          "\n<b>Kullanıcı:</b> {}" \
          "\n<b>Süre:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name), time_val)
    if reason:
        log += "\n<b>Sebep:</b> {}".format(reason)

    try:
        if member.can_send_messages is None or member.can_send_messages:
            bot.restrict_chat_member(chat.id, user_id, until_date=mutetime, can_send_messages=False)
            message.reply_text("{} için susturuldu!".format(time_val))
            return log
        else:
            message.reply_text("Zaten susturulmuş.")

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text("{} için yoksayıldı!".format(time_val), quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR muting user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Bu kullanıcıyı susturamıyorum.")

    return ""


__help__ = """
*Sadece yöneticiler:*
 - /sustur <kullanıcı>: Bir kullanıcıyı susturur. Cevap olarak da kullanılabilir, cevaplanan kullanıcıyı susturabilir.
 - /zamanlisustur <kullanıcı> zaman(m/h/d): Kullanıcıyı bir süre susturur. (Elle veya mesaja cevap vererek). m = dakika, h = saat, d = gün.
   Örn: /zamanlisustur @kullanici 1m
        /zsustur @kullanici 1d
 - /izinver <kullanıcı>: bir kullanıcının sesini açar. Cevap olarak da kullanılabilir, cevaplanan kullanıcıya izin verir.
"""

__mod_name__ = "Susturma"

MUTE_HANDLER = CommandHandler("sustur", mute, pass_args=True, filters=Filters.group)
UNMUTE_HANDLER = CommandHandler("izinver", unmute, pass_args=True, filters=Filters.group)
TEMPMUTE_HANDLER = CommandHandler(["zamanlisustur", "zsustur"], temp_mute, pass_args=True, filters=Filters.group)

dispatcher.add_handler(MUTE_HANDLER)
dispatcher.add_handler(UNMUTE_HANDLER)
dispatcher.add_handler(TEMPMUTE_HANDLER)
