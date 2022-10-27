from os import getenv


version = "1.0.0"

if uri := getenv("DB_URI"):
    db_url = uri
elif host := getenv("DB_HOST"):
    db_host = host
    db_port = getenv("DB_PORT")
else:
    db_name = "vibr"

name = "vibr"
colors = [0xFF00E1, 0xDA00FF, 0x8000FF, 0x2500FF, 0x008FFF]
logchannel = 939853360289419284
vote_channel = 946324179605684235

with open("vibr/init.sql") as f:
    database_init = f.read()
