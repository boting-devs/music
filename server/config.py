from os import getenv


accesslog = "logs/access.log"
bind = f"{getenv('SERVER_BIND')}:{getenv('SERVER_PORT')}"
errorlog = "logs/error.log"
