from tg_bot.sample_config import Config


class Development(Config):
    OWNER_ID = 824191257
    OWNER_USERNAME = "tahirdeger"
    API_KEY = "1565625697:AAFFDDQKy_1wj7bR9qXRS5_jyEUArrA4nbo"
    SQLALCHEMY_DATABASE_URI = 'postgres://qoxyayvnwtdvxx:e878f1743845772118f42fe7a87669d5d7d85eb79ff1644ee06b261a5cadb0ef@ec2-52-22-161-59.compute-1.amazonaws.com:5432/dbhnak49mkvs7f'
    MESSAGE_DUMP = '-1234567890' # some group chat that your bot is a member of
    USE_MESSAGE_DUMP = True
    SUDO_USERS = [824191257]  # List of id's for users which have sudo access to the bot.
    LOAD = []
    NO_LOAD = ['translation']

#
#postgresql://postgres:2580.Tahir@localhost:5432/hayribot