import json

# configure database
try:
    f = open('peers.json')
except IOError as e:
    print(u'peers.json not exist, creating...')
    with open("peers.json", "w") as f:
        peers = {
            "foo": {
                "peerId": "foo",
                "peerIp": "0.0.0.0",
                "peerPrivateKey": "Private_bar",
                "peerPublicKey": "Public_bar",
                "isActivated" : True
            }
        }
        json.dump(peers, f, indent=4)
else:
    with f:
        print(u'peers.json exist')
        f.close()



def saveDatabase(peers: dict):
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
def peerREAD(peerId: str):
    peers = allPeersREAD()
    try:
        peer = peers[peerId]
    except KeyError:
        raise Exception("Peer not found", 404)
    return peer


# create new peer in database
def peerCREATE(peer: dict):
    peers = allPeersREAD()

    if peer["peerId"] in peers.keys():
        raise Exception("This peerId has already taken", 400)

    for key in peers:
        if peers[key]['peerIp'] == peer["peerIp"]:
            raise Exception("This peerIp has already taken", 400)

    peers[peer["peerId"]] = peer
    saveDatabase(peers)
    return peer


# update peer
def peerUPDATE(newPeer: dict):
    peers = allPeersREAD()
    oldPeer = peerREAD(newPeer["peerId"])

    if "peerIp" in newPeer and newPeer["peerIp"] is not None:
        for key in peers:
            if peers[key]['peerIp'] == newPeer["peerIp"]:
                raise Exception("This peerIp has already taken", 400)
        oldPeer["peerIp"] = newPeer["peerIp"]

    peers[oldPeer["peerId"]] = oldPeer
    saveDatabase(peers)
    return oldPeer


def peerDELETE(peerId: str):
    peers = allPeersREAD()
    try:
        peer = peers.pop(peerId)
    except KeyError as e:
        print(e)
        raise Exception("Peer not found", 404)

    saveDatabase(peers)
    return peer


def setActivationForPeer(peerId: str, isActivated: bool):
    peers = allPeersREAD()
    if peerId not in peers:
        raise Exception("Peer not found", 404)

    peers[peerId]["isActivated"] = isActivated
    saveDatabase(peers)
    return peers[peerId]
