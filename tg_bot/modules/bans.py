import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import run_async, CommandHandler, Filters
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher, BAN_STICKER, LOGGER
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_ban_protected, can_restrict, \
    is_user_admin, is_user_in_chat
from tg_bot.modules.helper_funcs.extraction import extract_user_and_text
from tg_bot.modules.helper_funcs.string_handling import extract_time
from tg_bot.modules.log_channel import loggable


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def ban(bot: Bot, update: Update, args: List[str]) -> str:
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

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Yöneticilieri yasaklamak mı?? Keşke mümkün olsa...")
        return ""

    if user_id == bot.id:
        message.reply_text("Tabi ki de kendimi yasaklamam, deli miyim ben?")
        return ""

    log = "<b>{}:</b>" \
          "\n#BANNED" \
          "\n<b>Yönetici:</b> {}" \
          "\n<b>Kullanıcı:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                       mention_html(user.id, user.first_name),
                                                       mention_html(member.user.id, member.user.first_name),
                                                       member.user.id)
    if reason:
        log += "\n<b>Sebep:</b> {}".format(reason)

    try:
        chat.kick_member(user_id)
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text("Yasaklandı!")
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Yasaklandı!', quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Olmaz olamaz. O kullanıcıyı yasaklayamam")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def temp_ban(bot: Bot, update: Update, args: List[str]) -> str:
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
            message.reply_text("Bu kullanıcıyı göremedim")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Yöneticileri yasaklayabilmeyi gerçekten çok isterdim...")
        return ""

    if user_id == bot.id:
        message.reply_text("Tabi ki de kendimi yasaklamayacağım, delirdin mi?")
        return ""

    if not reason:
        message.reply_text("Bu kullanıcıyı yasaklamak için bir zaman belirtmediniz!")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    bantime = extract_time(message, time_val)

    if not bantime:
        return ""

    log = "<b>{}:</b>" \
          "\n#TEMP BANNED" \
          "\n<b>Yönetici:</b> {}" \
          "\n<b>Kullanıcı:</b> {} (<code>{}</code>)" \
          "\n<b>Zaman:</b> {}".format(html.escape(chat.title),
                                     mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name),
                                     member.user.id,
                                     time_val)
    if reason:
        log += "\n<b>Sebep:</b> {}".format(reason)

    try:
        chat.kick_member(user_id, until_date=bantime)
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text("Yasaklandı! Kullanıcı {} için yasaklanacak.".format(time_val))
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text("Yasaklandı! Kullanıcı {} için yasaklanacak.".format(time_val), quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Yok artık !, O kullanıcıyı yasaklayamam.")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def kick(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Bu kullanıcıyı bulamıyorum")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id):
        message.reply_text("Gerçekten yöneticileri tekmelemeyi dilerdim ama olmaazz...")
        return ""

    if user_id == bot.id:
        message.reply_text("Evet, bunu yapmayacağım..")
        return ""

    res = chat.unban_member(user_id)  # unban on current user = kick
    if res:
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text("Kovuldu!")
        log = "<b>{}:</b>" \
              "\n#KICKED" \
              "\n<b>Yönetici:</b> {}" \
              "\n<b>Kullanıcı:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                           mention_html(user.id, user.first_name),
                                                           mention_html(member.user.id, member.user.first_name),
                                                           member.user.id)
        if reason:
            log += "\n<b>Sebep:</b> {}".format(reason)

        return log

    else:
        message.reply_text("Yok daha neler, o kullanıcıyı tekmeleyemem.")

    return ""


@run_async
@bot_admin
@can_restrict
def kickme(bot: Bot, update: Update):
    user_id = update.effective_message.from_user.id
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("Keşke yapabilsem ... ama sen bir yöneticisin.")
        return

    res = update.effective_chat.unban_member(user_id)  # unban on current user = kick
    if res:
        update.effective_message.reply_text("Sorun yok.")
    else:
        update.effective_message.reply_text("Haa? Yapamam :/")


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def unban(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Bu kullanıcıyı bulamıyorum !")
            return ""
        else:
            raise

    if user_id == bot.id:
        message.reply_text("Burada olmasaydım kendimi nasıl kaldırırdım...?")
        return ""

    if is_user_in_chat(chat, user_id):
        message.reply_text("Zaten sohbette olan birinin yasağını neden kaldırmaya çalışıyorsun?")
        return ""

    chat.unban_member(user_id)
    message.reply_text("Evet, bu kullanıcı katılabilir!")

    log = "<b>{}:</b>" \
          "\n#UNBANNED" \
          "\n<b>Yönetici:</b> {}" \
          "\n<b>Kullanıcı:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                       mention_html(user.id, user.first_name),
                                                       mention_html(member.user.id, member.user.first_name),
                                                       member.user.id)
    if reason:
        log += "\n<b>Sebep:</b> {}".format(reason)

    return log


__help__ = """
 - /benikov: Komutu yazan kullanıcı gruptan atılır.

*Sadece Yöneticiler:*
 - /yasakla <kullanıcı>: Kullanıcıyı yasaklar. (@kullanıcı, veya mesajı cevaplayarak)
 - /zyasakla <kullanıcı> z(m/h/d): Kullanıcıyı z kadar süre yasaklar. (@kullanıcı veya mesajı cevaplayarak). m = dakika, h = saat, d = gün.
 - /yasakkaldir <kullanıcı>: Kullanıcının yasağını kaldırır. (@kullanıcı veya mesajı cevaplayarak)
 - /kov <kullanıcı>: Kullanıcıyı gruptan kovar, (@kullanıcı veya mesajı cevaplayarak)
"""

__mod_name__ = "Yasaklama"

BAN_HANDLER = CommandHandler("yasakla", ban, pass_args=True, filters=Filters.group)
TEMPBAN_HANDLER = CommandHandler(["zyasakla", "tempban"], temp_ban, pass_args=True, filters=Filters.group)
KICK_HANDLER = CommandHandler("kov", kick, pass_args=True, filters=Filters.group)
UNBAN_HANDLER = CommandHandler("yasakkaldir", unban, pass_args=True, filters=Filters.group)
KICKME_HANDLER = DisableAbleCommandHandler("benikov", kickme, filters=Filters.group)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(TEMPBAN_HANDLER)
dispatcher.add_handler(KICK_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)
dispatcher.add_handler(KICKME_HANDLER)
