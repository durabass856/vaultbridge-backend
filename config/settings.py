import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MYSQL_HOST = "hopper.proxy.rlwy.net"
    MYSQL_USER = "root"
    MYSQL_PASSWORD = "jYBGMcVWIApiuxGdHKOROGcToipUwoWv"
    MYSQL_DB = "railway"
    MYSQL_PORT = 14181

    MYSQL_CURSORCLASS = "DictCursor"
