from os import getenv

if uri := getenv("DB_URI"):
    db_url = uri  # dev
else:
    db_name = "vibr"  # prod

name = "vibr"
colors = [0xFF00E1, 0xDA00FF, 0x8000FF, 0x2500FF, 0x008FFF]
logchannel = 939853360289419284

with open("vibr/init.sql") as f:
    database_init = f.read()
