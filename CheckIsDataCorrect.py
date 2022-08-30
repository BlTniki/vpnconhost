import re

with open("appconf.txt") as f:
    auth = f.readline().strip()


def authentication(password):
    if password == auth:
        return True
    else:
        return False


def isPeerIdCorrect(peerId):
    tpl = '[A-Za-z0-9]+_[0-9]+'
    # checking for a string, for the emptiness of the parsing result and that the parsing matches the peerID
    if not isinstance(peerId, str) or len(re.findall(tpl, peerId)) == 0 or re.findall(tpl, peerId)[0] is not peerId:
        return False
    return True


def isPeerIpCorrect(peerIp):
    tpl = "(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
    # check is peerIp is string
    if not isinstance(peerIp, str):
        return False
    result = re.match(tpl, peerIp)
    # check is result is not a NoneType and result match completely matches peerIp
    if not result or result.group() is not peerIp:
        return False
    ipEnd = int(result.group(4))
    if ipEnd < 1 or ipEnd > 254:
        return False

    return True
