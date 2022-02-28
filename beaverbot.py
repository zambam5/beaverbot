# noinspection PyUnresolvedReferences
import cfgzam as cfg
import time, logging, random, json, requests, socket, re
import spotipy
import spotipy.util as util
from messages import MessageHandler
import song_requests as sr
from irctools import chat, ping

# noinspection PyUnresolvedReferences

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
handler = logging.FileHandler('beaver.log', mode='w')
formatter = logging.Formatter('''%(asctime)s -
                              %(name)s - %(levelname)s - %(message)s''')
handler.setFormatter(formatter)
logger.addHandler(handler)

Messages = MessageHandler(cfg.CHAN)
s = None #only here to make the linter happy

def connect(HOST, PORT):
    global s
    s = None
    try:
        s.close()
    except:
        pass
    s = socket.socket()
    try:
        s.connect((HOST, PORT))
    except ConnectionAbortedError:
        logger.info('Connection Failed')


def login(sock, PASS, NICK, CHAN):
    sock.send("PASS {}\r\n".format(PASS).encode("utf-8"))
    sock.send("NICK {}\r\n".format(NICK).encode("utf-8"))
    test = sock.recv(1024).decode("utf-8")
    logger.info(test)

    sock.send("JOIN {}\r\n".format(CHAN).encode("utf-8"))
    test = sock.recv(1024).decode("utf-8")
    logger.info(test)

    sock.send("CAP REQ :twitch.tv/tags\r\n".encode("utf-8"))
    test = sock.recv(1024).decode("utf-8")
    logger.info(test)
    sock.send("CAP REQ :twitch.tv/commands\r\n".encode("utf-8"))
    test = sock.recv(1024).decode("utf-8")
    logger.info(test)


def exponential_backoff():
    global s
    count = 1
    while True:
        try:
            connect(cfg.HOST, cfg.PORT)
            login(s, cfg.PASS, cfg.NICK, cfg.CHAN)
            return True
        except socket.error:
            time.sleep(count)
            count = count*2


command_switch = {
        '!clearplaylist': lambda : sr.clear_playlist(s, messagedict),
        '!requeue': lambda : sr.requeue(s, messagedict),
        '!modqueue': lambda : sr.mod_queue(s, messagedict),
        '!song': lambda : sr.now_playing(s, messagedict)
}

#message type RECONNECT
def reconnect(HOST, PORT, PASS, NICK, CHAN):
    global s
    connect(HOST, PORT)
    login(s, PASS, NICK, CHAN)


#message type HOSTTARGET
def host(sock, message):
    target = message['host target']
    if target == '-':
        return False
    else:
        return chat(s, f"If the host broke on your end, here is the link: https://twitch.tv/{target}", cfg.CHAN)


#message type PRIVMSG
def PRIVMSG(mtesting, messagedict):
    userid = messagedict['user-id']
    username = messagedict['user-id']
    if 'custom-reward-id' in messagedict.keys():
        reward_switch = {
            '16f48209-c3b9-4a32-9143-109a2802a162': lambda : sr.song_requests(s, messagedict, cfg.URL)
        }
        mtesting = reward_switch.get(messagedict['custom-reward-id'], lambda : False)()
    elif messagedict['actual message'].startswith('!'):
        word_list = messagedict['actual message'].split(" ")
        command = word_list[0]
        mtesting = command_switch.get(command, lambda : False)()
    return mtesting

#message type: userstate, clearchat, clearmsg, notice, roomstate, usernotice, whisper
def the_rest(): return False

message_switch = {
            "WHISPER": lambda : the_rest(),
            "PRIVMSG": lambda : PRIVMSG(mtesting, messagedict),
            "USERNOTICE": lambda : the_rest(),
            "USERSTATE": lambda : the_rest(),
            "CLEARCHAT": lambda : the_rest(),
            "CLEARMSG": lambda : the_rest(),
            "HOSTTARGET": lambda : host(s, messagedict),
            "NOTICE": lambda : the_rest(),
            "ROOMSTATE": lambda : the_rest(),
            "PING": lambda : ping(s),
            "RECONNECT": lambda : reconnect(cfg.HOST, cfg.PORT, cfg.PASS, cfg.NICK, cfg.CHAN)
        }

if __name__ == "__main__":


    connect(cfg.HOST, cfg.PORT)
    login(s, cfg.PASS, cfg.NICK, cfg.CHAN)
    chan = cfg.CHAN[1:]
    t = time.time()
    timer, timeq = time.time(), time.time()
    timecheck = False
    cd = 15
    while True:
        try:
            response = s.recv(8192).decode("utf-8")
        except ConnectionResetError:
            print("timed out, attempting reconnect")
            exponential_backoff()
            continue
        except:
            continue
        if response == "":
            continue
        messagelist = Messages.splitmessages(response)
        for message in messagelist:
            try:
                mtesting = False
                try:
                    messagedict = Messages.message_dict_maker(message)
                except:
                    logging.exception(response)
                    continue
                if not messagedict:
                    print('bad message')
                    continue
                else:
                    mtesting = message_switch.get(messagedict['message type'], lambda : False)()
                if mtesting:
                    time.sleep(1/(100/30))
            except:
                print(message)
                logger.exception("Error processing message:" + message)
