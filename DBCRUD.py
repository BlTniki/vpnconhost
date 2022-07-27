import json

# configure database
try:
    f = open('peers.json')
except IOError as e:
    print(u'peers.json not exist, creating...')
    with open("peers.json", "w") as f:
        peers = {
            "foo": {
                "Private key": "bar",
                "Public key": "bar",
                "Ip address": "kek"
            }
        }
        json.dump(peers, f, indent=4)
else:
    with f:
        print(u'peers.json exist')
        f.close()



def saveDatabase(peers):
    try:
        with open("peers.json", "w") as f:
            json.dump(peers, f, indent=4)
    except IOError:
        raise Exception("Internal Server Error", 500)


# return all peers in database
def allPeersREAD():
    try:
        with open('peers.json') as f:
            peers = json.load(f)
    except IOError:
        raise Exception("Internal Server Error", 500)
    return peers


# return existing peer in database or raise exception
def peerREAD(peerId):
    peers = allPeersREAD()
    try:
        peer = peers[peerId]
    except KeyError:
        raise Exception("Peer not found", 404)
    return peer


# create new peer in database
def peerCREATE(peerId, ipEnd, peerPrivateKey, peerPublicKey):
    peers = allPeersREAD()

    if peerId in peers.keys():
        raise Exception("This peerId has already taken", 400)


    ipEnd = int(ipEnd)
    peerIp = f'10.8.0.{ipEnd}'
    for key in peers.keys():
        if peers[key]['Ip address'] == peerIp:
            raise Exception("This peerIp has already taken", 400)

    peers[peerId] = {'Private key': f'{peerPrivateKey}', 'Public key': f'{peerPublicKey}',
                     'Ip address': peerIp}

    saveDatabase(peers)
    return peers[peerId]


# update peer
def peerUPDATE(peerId, ipEnd=None, peerPrivateKey=None, peerPublicKey=None):
    peers = allPeersREAD()
    peer = peerREAD(peerId)

    if ipEnd:
        peerIp = f'10.8.0.{ipEnd}'
        for key in peers.keys():
            if peers[key]['Ip address'] == peerIp:
                raise Exception("This peerIp has already taken", 400)
        peer["Ip address"] = peerIp

    peers[peerId] = peer
    saveDatabase(peers)
    return peers[peerId]


def peerDELETE(peerId):
    peers = allPeersREAD()
    try:
        peer = peers.pop(peerId)
    except KeyError as e:
        print(e)
        raise Exception("Peer not found", 404)

    saveDatabase(peers)
    return peer
