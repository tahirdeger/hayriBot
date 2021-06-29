from tg_bot.sample_config import Config


class Development(Config):
    OWNER_ID = ID
    OWNER_USERNAME = "tahirdeger"
    API_KEY = "api_key"
    SQLALCHEMY_DATABASE_URI = 'postgresql_uri'
    MESSAGE_DUMP = '-1234567890' # some group chat that your bot is a member of
    USE_MESSAGE_DUMP = True
    SUDO_USERS = [ID]  # List of id's for users which have sudo access to the bot.
    LOAD = []
    NO_LOAD = []

