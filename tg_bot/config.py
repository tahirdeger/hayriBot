from tg_bot.sample_config import Config


class Development(Config):
    OWNER_ID = 824191257
    OWNER_USERNAME = "tahirdeger"
    API_KEY = "1565625697:AAHYIK7WIySt2mMyv1PuBI-93UqVD5Qb-WI"
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:2580.Tahir@localhost:5432/hayribot'
    MESSAGE_DUMP = '-1234567890' # some group chat that your bot is a member of
    USE_MESSAGE_DUMP = True
    SUDO_USERS = [824191257]  # List of id's for users which have sudo access to the bot.
    LOAD = []
    NO_LOAD = ['translation']

#
#postgresql://postgres:2580.Tahir@localhost:5432/hayribot