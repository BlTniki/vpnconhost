import re

with open("appconf.txt") as f:
    auth = f.readline().strip();
    workDir = f.readline().strip();
    ipAddress = f.readline().strip();
    testMode = True if f.readline().strip() == "YES" else False;


def authentication(password):
    if password == auth:
        return True
    else:
        return False


def isPeerIdCorrect(peerId):
    tpl = '^[A-Za-z0-9]+'
    if not isinstance(peerId, str) or len(re.findall(tpl, peerId)) == 0 or len(re.findall(tpl, peerId)[0]) != len(peerId):
        return False
    return True

def isIpEndCorrect(ipEnd):
    if not isinstance(ipEnd, int) or ipEnd < 1 or ipEnd > 254:
        return False
    return True