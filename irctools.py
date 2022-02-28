import logging
logger = logging.getLogger('__main__.' + __name__)

def chat(sock, msg, CHAN):
    # this was not written by me
    """
    Send a chat message to the server.
    Keyword arguments:
    sock -- the socket over which to send the message
    msg  -- the message to be sent
    """
    sock.send(f"PRIVMSG {CHAN} :{msg}\r\n".encode("utf-8"))
    return True


def ping(sock):
    sock.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
    logger.info("PING")
    return True


def pong(sock):
    sock.send("PING :tmi.twitch.tv\r\n".encode("utf-8"))
