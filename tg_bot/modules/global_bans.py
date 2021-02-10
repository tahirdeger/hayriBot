import html
from io import BytesIO
from typing import Optional, List

from telegram import Message, Update, Bot, User, Chat, ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import run_async, CommandHandler, MessageHandler, Filters
from telegram.utils.helpers import mention_html

import tg_bot.modules.sql.global_bans_sql as sql
from tg_bot import dispatcher, OWNER_ID, SUDO_USERS, SUPPORT_USERS, STRICT_GBAN
from tg_bot.modules.helper_funcs.chat_status import user_admin, is_user_admin
from tg_bot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from tg_bot.modules.helper_funcs.filters import CustomFilters
from tg_bot.modules.helper_funcs.misc import send_to_list
from tg_bot.modules.sql.users_sql import get_all_chats

GBAN_ENFORCE_GROUP = 6

GBAN_ERRORS = {
    "Kullanıcı sohbetin yöneticisidir",
    "Sohbet bulunamadı",
    "Sohbet üyesini yasaklamak için yeterli hakkın yok",
    "Kullanıcı katılımcı değil",
    "ID geçersiz",
    "Grup sohbeti devre dışı bırakıldı",
    "Bir davetliyi atıyor olması gerekir",
    "Sohbet yöneticisi gerekli",
    "Yalnızca grubun sahibi grup yöneticilerini atabilir",
    "Kanal özel",
    "Sohbette değil"
}

UNGBAN_ERRORS = {
    "Kullanıcı sohbetin yöneticisi",
    "Sohbet bulunamadı",
    "Sohbet üyesini yasaklamak için yeterli hakkın yok",
    "Kullanıcı katılımcı değil",
    "Yöntem yalnızca süper grup ve kanal sohbetleri için kullanılabilir",
    "Sohbette değil",
    "Kanal özel",
    "Sohbet yöneticisi gerekli",
    "ID geçersiz",
}


@run_async
def gban(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Bir kullanıcıya atıfta bulunmuyorsunuz.")
        return

    if int(user_id) in SUDO_USERS:
        message.reply_text("Küçük gözlerimden kaçmıyor ... bir yönetici savaşı! Neden birbirinizle uğraşıyorsunuz kardeşim?")
        return

    if int(user_id) in SUPPORT_USERS:
        message.reply_text("Haaha birisi bir destek kullanıcısını yasaklamaya çalışıyor! Patlamış mısır kapıp geliyorum")
        return

    if user_id == bot.id:
        message.reply_text("-_- Çok komik, Beni yasaklayacak adam daha anasının karnından doğmadı? İyi deneme.")
        return

    try:
        user_chat = bot.get_chat(user_id)
    except BadRequest as excp:
        message.reply_text(excp.message)
        return

    if user_chat.type != 'private':
        message.reply_text("Kullanıcı yok!")
        return

    if sql.is_user_gbanned(user_id):
        if not reason:
            message.reply_text("Bu kullanıcı zaten yasaklanmış; Sebebi yok, sen de bana yenisini söylemedin...")
            return

        old_reason = sql.update_gban_reason(user_id, user_chat.username or user_chat.first_name, reason)
        if old_reason:
            message.reply_text("Zaten yasaklanmış, Sebebi de şu:\n"
                               "<code>{}</code>\n"
                               "Gittim ve yeni sebebinle güncelledim!".format(html.escape(old_reason)),
                               parse_mode=ParseMode.HTML)
        else:
            message.reply_text("Bu kullanıcı zaten yasaklanmış, ancak herhangi bir neden belirlenmemiş; Gittim ve güncelledim!")

        return

    message.reply_text("*Yasak tokmağı kafaya iner* 😉")

    banner = update.effective_user  # type: Optional[User]
    send_to_list(bot, SUDO_USERS + SUPPORT_USERS,
                 "{}, şu kullanıcıyı yasakladı {} "
                 "Çünkü:\n{}".format(mention_html(banner.id, banner.first_name),
                                       mention_html(user_chat.id, user_chat.first_name), reason or "No reason given"),
                 html=True)

    sql.gban_user(user_id, user_chat.username or user_chat.first_name, reason)

    chats = get_all_chats()
    for chat in chats:
        chat_id = chat.chat_id

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            bot.kick_chat_member(chat_id, user_id)
        except BadRequest as excp:
            if excp.message in GBAN_ERRORS:
                pass
            else:
                message.reply_text("{} nedeniyle yasak yapılamadı".format(excp.message))
                send_to_list(bot, SUDO_USERS + SUPPORT_USERS, "{} nedeniyle yasak yapılamadı".format(excp.message))
                sql.ungban_user(user_id)
                return
        except TelegramError:
            pass

    send_to_list(bot, SUDO_USERS + SUPPORT_USERS, "Yasaklama tamam!")
    message.reply_text("Kişi yasaklandı.")


@run_async
def ungban(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message  # type: Optional[Message]

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("Bir kullanıcıya atıfta bulunmuyorsunuz.")
        return

    user_chat = bot.get_chat(user_id)
    if user_chat.type != 'private':
        message.reply_text("Kullanıcı yok!")
        return

    if not sql.is_user_gbanned(user_id):
        message.reply_text("Bu kullanıcı yasaklanmadı!")
        return

    banner = update.effective_user  # type: Optional[User]

    message.reply_text("Bu memlekette {} için ikinci bir şans vereceğim.".format(user_chat.first_name))

    send_to_list(bot, SUDO_USERS + SUPPORT_USERS,
                 "{} kullanıcının yasaklamasını kaldırdı {}".format(mention_html(banner.id, banner.first_name),
                                                   mention_html(user_chat.id, user_chat.first_name)),
                 html=True)

    chats = get_all_chats()
    for chat in chats:
        chat_id = chat.chat_id

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            member = bot.get_chat_member(chat_id, user_id)
            if member.status == 'kicked':
                bot.unban_chat_member(chat_id, user_id)

        except BadRequest as excp:
            if excp.message in UNGBAN_ERRORS:
                pass
            else:
                message.reply_text("{} nedeniyle yasak kaldırılamadı: ".format(excp.message))
                bot.send_message(OWNER_ID, "{} nedeniyle yasak kaldırılamadı:".format(excp.message))
                return
        except TelegramError:
            pass

    sql.ungban_user(user_id)

    send_to_list(bot, SUDO_USERS + SUPPORT_USERS, "yasak kaldırıldı!")

    message.reply_text("Kişinin yasağı kaldırıldı.")


@run_async
def gbanlist(bot: Bot, update: Update):
    banned_users = sql.get_gban_list()

    if not banned_users:
        update.effective_message.reply_text("Yasaklı kullanıcı yok! Çok nazik insanlar var şu hayatta...")
        return

    banfile = 'Bu meymenetsiz gruptan atıldı.\n'
    for user in banned_users:
        banfile += "[x] {} - {}\n".format(user["name"], user["user_id"])
        if user["reason"]:
            banfile += "Sebep: {}\n".format(user["reason"])

    with BytesIO(str.encode(banfile)) as output:
        output.name = "gbanlist.txt"
        update.effective_message.reply_document(document=output, filename="gbanlist.txt",
                                                caption="İşte şu anda yasaklanmış kullanıcıların listesi.")


def check_and_ban(update, user_id, should_message=True):
    if sql.is_user_gbanned(user_id):
        update.effective_chat.kick_member(user_id)
        if should_message:
            update.effective_message.reply_text("Bu, grup adabımıza uymayan bir insan, burada olmamalı !")


@run_async
def enforce_gban(bot: Bot, update: Update):
    # Not using @restrict handler to avoid spamming - just ignore if cant gban.
    if sql.does_chat_gban(update.effective_chat.id) and update.effective_chat.get_member(bot.id).can_restrict_members:
        user = update.effective_user  # type: Optional[User]
        chat = update.effective_chat  # type: Optional[Chat]
        msg = update.effective_message  # type: Optional[Message]

        if user and not is_user_admin(chat, user.id):
            check_and_ban(update, user.id)

        if msg.new_chat_members:
            new_members = update.effective_message.new_chat_members
            for mem in new_members:
                check_and_ban(update, mem.id)

        if msg.reply_to_message:
            user = msg.reply_to_message.from_user  # type: Optional[User]
            if user and not is_user_admin(chat, user.id):
                check_and_ban(update, user.id, should_message=False)


@run_async
@user_admin
def gbanstat(bot: Bot, update: Update, args: List[str]):
    if len(args) > 0:
        if args[0].lower() in ["ac", "evet"]:
            sql.enable_gbans(update.effective_chat.id)
            update.effective_message.reply_text("Bu grupta global yasakları etkinleştirdim. Bu seni korumaya yardımcı olacak "
                                                "Bu seni korumaya yardımcı olacak. Özellikle spam mesajcılara ve trollere karşı")
        elif args[0].lower() in ["kapat", "hayir"]:
            sql.disable_gbans(update.effective_chat.id)
            update.effective_message.reply_text("Bu grupta global yasakları devre dışı bıraktım.  "
                                                "Global yasaklar artık kullanıcılarınızı etkilemeyecek "
                                                "Trollerden ve spam gönderenlerden daha az korunacaksınız!")
    else:
        update.effective_message.reply_text("Bir ayar seçmek için bana bazı argümanlar ver! ac/evet, kapat/hayir!\n\n"
                                            "Mevcut ayarınız: {}\n"
                                            "True olduğunda, bir global yasak grubunuzda aktif hale gelecek, korumam altında olacaksınız. "
                                            "Yanlış olduğunda, gruplarda yazılan mesajlar, spam gönderenlerin insafına "
                                            "kalmış.".format(sql.does_chat_gban(update.effective_chat.id)))


def __stats__():
    return "{} global yasaklanmış kullanıcı.".format(sql.num_gbanned_users())


def __user_info__(user_id):
    is_gbanned = sql.is_user_gbanned(user_id)

    text = "Global olarak yasaklandı: <b>{}</b>"
    if is_gbanned:
        text = text.format("Evet")
        user = sql.get_gbanned_user(user_id)
        if user.reason:
            text += "\nReason: {}".format(html.escape(user.reason))
    else:
        text = text.format("Hayır")
    return text


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return "Bu sohbet * global yasak* uyguluyor: `{}`.".format(sql.does_chat_gban(chat_id))


__help__ = """
Küresel yasaklar olarak da bilinen *Global yasaklar*, bot sahipleri tarafından spam gönderenleri tüm gruplarda yasaklamak için kullanılır.\
Bu aynı zamanda sohbetlerinizi korumama yardımcı olur. Spam mesajlardan oluşan seri mesajları otomatik olarak silerim.

*Sadece Yöneticiler:*
 - /gyasakdurumu <ac/kapa/evet/hayir>: Global yasaklamaların grubunuz üzerindeki etkisini devre dışı bırakır veya mevcut ayarlarınıza geri döner.
 - /gyasaklistesi: Mevcut yasakları gösterir.
 - /gyasakla: Mesajına cevap verilen kullanıcıyı global yasaklı listesine atar
 - /gyasakiptal: Global yasaklı kullanıcıyı listeden kaldırır

"""

__mod_name__ = "Global Yasaklar"

GBAN_HANDLER = CommandHandler("gyasakla", gban, pass_args=True,
                              filters=CustomFilters.sudo_filter | CustomFilters.support_filter)
UNGBAN_HANDLER = CommandHandler("gyasakiptal", ungban, pass_args=True,
                                filters=CustomFilters.sudo_filter | CustomFilters.support_filter)
GBAN_LIST = CommandHandler("gyasaklistesi", gbanlist,
                           filters=CustomFilters.sudo_filter | CustomFilters.support_filter)

GBAN_STATUS = CommandHandler("gyasakdurumu", gbanstat, pass_args=True, filters=Filters.group)

GBAN_ENFORCER = MessageHandler(Filters.all & Filters.group, enforce_gban)

dispatcher.add_handler(GBAN_HANDLER)
dispatcher.add_handler(UNGBAN_HANDLER)
dispatcher.add_handler(GBAN_LIST)
dispatcher.add_handler(GBAN_STATUS)

if STRICT_GBAN:  # enforce GBANS if this is set
    dispatcher.add_handler(GBAN_ENFORCER, GBAN_ENFORCE_GROUP)
