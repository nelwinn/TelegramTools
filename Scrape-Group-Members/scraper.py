import sys
import csv
import time
import asyncio
import datetime
from dateutil.tz import gettz
from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.errors.rpcerrorlist import *
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import UserStatusOnline
from telethon.tl.types import UserStatusRecently

PROXY = None  # or, example: "111.111.111.111:4047"
PROXY_TYPE = 'socks5'
PROXYUSERNAME = None
PROXYPASSWORD = None

TELEGRAM_PHONE_NUMBER = "917025"
API_ID = 153  # Getfrom my.telegram/org
API_HASH = "YOUR API HASH"  # Getfrom my.telegram/org


async def scrapeUsers(phone, api_id, api_hash, proxy):
    global target_group
    global group_username

    if PROXY:
        proxy_host, proxy_port = PROXY.split(":")
        proxy = dict(proxy_type=PROXY_TYPE,
                     addr=proxy_host, port=int(proxy_port))
    else:
        proxy = None

    print('Attempting login for', phone)
    client = TelegramClient(
        str(phone), api_id, api_hash, timeout=10, proxy=proxy)

    try:
        await client.connect()
        if not await client.is_user_authorized():
            await client.send_code_request(phone)
            await client.sign_in(phone, input('Enter the code: '))
    except SessionPasswordNeededError:
        await client.sign_in(phone, password=input("Enter your password: "))
    except Exception as e:
        print(str(e))
        return
    print('\t' + str(phone), "connected")

    try:
        ent = await client.get_entity(group_username)
        if ent.left == True:
            print('\tNot a member, trying to join group...')
            await client(JoinChannelRequest(ent))
            print('\t Joined the group, sleeping for 15 seconds...')
            time.sleep(15)
    except Exception as e:  # Error from telegram, nothing else to do now
        print(str(e))
        return

    print('\tScraping...')
    try:
        members_scraped = await client.get_participants(ent, aggressive=True)
    except Exception as e:
        print(str(e))
        return  # Error from telegram, nothing else to do now

    with open("scraped-users.csv", "w", encoding='UTF-8') as f:
        writer = csv.writer(f, delimiter=",", lineterminator="\n")
        writer.writerow(['username', 'user id', 'access hash',
                        'name', 'group', 'group id', 'group_username'])
        for user in members_scraped:
            if option == 1:
                if not (isinstance(user.status, UserStatusOnline) or isinstance(user.status, UserStatusRecently)):
                    continue
            elif option == 2:
                now = datetime.datetime.now(tz=gettz("UTC"))
                try:
                    last_online = user.status.was_online
                except Exception as e:  # User having non exact last seen time like recently.
                    continue
                diff = now - last_online
                timeobj = datetime.timedelta(
                    days=diff.days, seconds=diff.seconds)
                seconds = timeobj.total_seconds()
                hours = divmod(seconds, 3600)
                if not hours[0] in range(x, y):
                    continue
            elif option == 3:
                now = datetime.datetime.now(tz=gettz("UTC"))
                try:
                    last_online = user.status.was_online
                except Exception as e:  # User having non exact last seen time like recently.
                    continue
                diff = now - last_online
                if not diff.days in range(x, y):
                    continue
            username = user.username if user.username else ""
            first_name = user.first_name
            last_name = user.last_name if user.last_name else ""
            name = (first_name + ' ' + last_name).strip()
            writer.writerow([username, user.id, user.access_hash,
                            name, ent.title, ent.id, ent.username])

    print('Sucessfully stored scraped csv file for', phone)
    await client.disconnect()
    sys.exit()

if __name__ == '__main__':
    group_username = input('Enter the username of group to scrape:  ')
    asyncio.set_event_loop(asyncio.SelectorEventLoop())
    loop = asyncio.get_event_loop()

    option = input("""
        1. Online and recently active users
        2. Active during X - Y hours
        3. Active during X - Y days
        4. All Users
        """)
    option = int(option)
    if option == 2:
        x, y = input("Enter the hours in the format X - Y:    ").split('-')
        x = int(x.strip())
        y = int(y.strip())
    if option == 3:
        x, y = input("Enter the days in the format X - Y:    ").split('-')
        x = int(x.strip())
        y = int(y.strip())

    loop.run_until_complete(scrapeUsers(
        TELEGRAM_PHONE_NUMBER, API_ID, API_HASH, proxy=PROXY))
