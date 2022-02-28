from datetime import datetime
import logging

logger = logging.getLogger('__main__.' + __name__)

class MessageHandler():
    def __init__(self, chan):
        self.chan = chan
    

    def splitmessages(self, response):
        messages = response.splitlines()
        return messages
    

    def message_dict_maker(self, message):
        messagedict = dict()
        if message.startswith('PING'):
            messagedict['message type'] = 'PING'
            messagedict['time'] = datetime.now()
            return messagedict
        elif 'user-type=' in message:
            messagelist1 = message.split('user-type=')
            messagelist = messagelist1[0].split(';')
            for item in messagelist:
                items = item.split('=')
                try:
                    messagedict[items[0]] = items[1]
                except IndexError:
                    messagedict[items[0]] = ''
            if "PRIVMSG" in messagelist1[1]:
                messagedict['message type'] = "PRIVMSG"
                firstsplit = messagelist1[1].split(" " + self.chan + " :")
                if firstsplit[0].startswith('mod :'):
                    namestrip = firstsplit[0][5:]
                else:
                    namestrip = firstsplit[0][2:]
                name = namestrip.split('!')[0]
                messagedict['name'] = name
                messagedict['actual message'] = firstsplit[1].strip(":")
            elif "WHISPER" in messagelist1[1]:
                print("whisper")
                messagedict['message type'] = "WHISPER"
            elif "PRIV1MSG" in messagelist1[1]:
                messagedict['message type'] = "PRIVMSG"
                firstsplit = messagelist1[1].split(" " + self.chan + " :")
                messagedict['actual message'] = firstsplit[1].strip(':')
            elif "USERNOTICE" in messagelist1[1]:
                messagedict['message type'] = "USERNOTICE"
            elif "USERSTATE" in messagelist1[1]:
                messagedict['message type'] = "USERSTATE"
            return messagedict
        if message.startswith('badge'):
            return False
        messagelist1 = message.split(' ')
        print(messagelist1)
        if messagelist1[1] == "HOSTTARGET":
            messagedict['message type'] = 'HOSTTARGET'
            messagedict['host target'] = messagelist1[3].strip(':')
        elif messagelist1[1] == "RECONNECT":
            messagedict['message type'] = 'RECONNECT'
        elif messagelist1[2] == "NOTICE":
            messagedict['message type'] = "NOTICE"
        elif messagelist1[2] == "CLEARCHAT":
            messagedict['message type'] = "CLEARCHAT"
        elif messagelist1[2] == "ROOMSTATE":
            messagedict['message type'] = "ROOMSTATE"
        elif messagelist1[2] == "CLEARMSG":
            print('here')
            messagedict['message type'] = "CLEARMSG"
        return messagedict