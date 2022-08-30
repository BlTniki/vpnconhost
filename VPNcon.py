import json
import confManipulate as Conf
import DBCRUD as DB
import CheckIsDataCorrect as Check
import TokensManegment
from logging.handlers import WatchedFileHandler
from flask import Flask, jsonify, request, make_response, send_from_directory, render_template, redirect, url_for, Response

app = Flask(__name__)

with open("appconf.txt") as f:
    auth = f.readline().strip()
    workDir = f.readline().strip()
    ipAddress = f.readline().strip()
    testMode = True if f.readline().strip() == "YES" else False

# Setup logging
try:
    handler = WatchedFileHandler(f"{workDir}VPNcon.log")
    app.logger.addHandler(handler)
    print(f"Logging setupted")
except Exception as e:
    print(e)
    print("im in windows?")


@app.route("/test")
def test():
    print(request.json)
    return jsonify(request.json)


@app.route('/')
def redirectToDocs():
    return redirect(url_for("getDoc"))


@app.route('/api/1.0/peers', methods=['GET'])
def getAllPeers():
    if not request.headers.get("Auth") == auth:
        return "Incorrect auth", 401
    try:
        peers = DB.allPeersREAD()
    except Exception as e:
        e = e.args
        return e[0], e[1]

    return Response(json.dumps([peers[key] for key in peers]), mimetype="application/json")


@app.route('/api/1.0/peers/<peerId>', methods=['GET'])
def getPeer(peerId):
    if not request.headers.get("Auth") == auth:
        return "Incorrect auth", 401

    try:
        peer = DB.peerREAD(peerId)
    except Exception as e:
        e = e.args
        return e[0], e[1]

    return jsonify(peer), 200


@app.route('/api/1.0/peers', methods=['POST'])
def postPeer():
    if not request.headers.get("Auth") == auth:
        return "Incorrect auth", 401

    # Checking for json body
    if not request.headers.get("Content-Type") == "application/json":
        return 'Bad request', 400
    peer = request.json

    # Valid request body
    if not "peerId" in peer.keys() or not "peerIp" in peer.keys():
        return jsonify({'error': 'Bad request'}), 400

    peerId = peer["peerId"]
    peerIp = peer["peerIp"]

    if not Check.isPeerIdCorrect(peerId):
        return 'Wrong peerId', 400
    if not Check.isPeerIpCorrect(peerIp):
        return 'Wrong peerIp', 400

    # generate peer's keys
    peer["peerPrivateKey"] = Conf.createPeerPrivateKey(peerId)
    peer["peerPublicKey"] = Conf.createPeerPublicKey(peerId)

    # add peer to database
    try:
        DB.peerCREATE(peer)
    except Exception as e:
        e = e.args
        return e[0], e[1]

    # generating peer conf file and adding to wireguard
    Conf.createPeerConf(peerId, peerIp, peer["peerPrivateKey"])
    Conf.addPeerToVPN(peerId, peerIp, peer["peerPublicKey"])

    return jsonify(peer), 200


@app.route('/api/1.0/peers', methods=['PUT'])
def updatePeer():
    if not request.headers.get("Auth") == auth:
        return "Incorrect auth", 401

    # Checking for json body
    if not request.headers.get("Content-Type") == "application/json" or len(request.json) is 0:
        return 'Bad request', 400
    peer = request.json
    # valid peerIp if we have one
    if peer["peerIp"] and not Check.isPeerIpCorrect(peer["peerIp"]):
        return 'Wrong peerIp', 400

    # Updating peer in database
    try:
        peer = DB.peerUPDATE(peer)
    except Exception as e:
        e = e.args
        return e[0], e[1]

    peerId = peer["peerId"]
    peerIp = peer["peerIp"]

    # Updating allowed-ips and config for this peer
    Conf.removePeerFromVPN(peerId, peer['peerPublicKey'])
    Conf.createPeerConf(peerId, peerIp, peer['peerPublicKey'])
    Conf.addPeerToVPN(peerId, peerIp, peer['peerPrivateKey'])

    return jsonify(peer), 200


@app.route('/api/1.0/peers/<peerId>', methods=['DELETE'])
def deletePeer(peerId):
    if not request.headers.get("Auth") == auth:
        return "Incorrect auth", 401

    # Deleting peer from database
    try:
        peer = DB.peerDELETE(peerId)
    except Exception as e:
        e = e.args
        return e[0], e[1]

    Conf.removePeerFromVPN(peerId, peer['peerPublicKey'])
    Conf.deleteConfAndKeys(peerId)

    return "Success", 200


@app.route('/api/1.0/conf/<token>', methods=['GET'])
def returnPeerConf(token):
    try:
        peerId = TokensManegment.returnPayloadByToken(token)
    except Exception as e:
        e = e.args
        return e[0], e[1]
    if testMode:
        return "Success"
    filename = f'{peerId}.conf'
    directory = f'{workDir}peersConf/'
    response = make_response(send_from_directory(directory, filename, as_attachment=True))
    return response


@app.route('/api/1.0/conf/<peerId>', methods=['POST'])
def generateTokenForDownloadConfig(peerId):
    if not request.headers.get("Auth") == auth:
        return "Incorrect auth", 401
    try:
        DB.peerREAD(peerId)
        token = TokensManegment.generateTokenForPayload(peerId)
    except Exception as e:
        e = e.args
        return e[0], e[1]

    return token, 200


@app.route("/api/1.0/logs", methods=["GET"])
def getLogs():
    if not request.headers.get("Auth") == auth:
        return "Incorrect auth", 401
    with open("VPNcon.log", "r") as file:
        string = file.read()
        return string


@app.route("/api/1.0/logs", methods=["DELETE"])
def deleteLogs():
    if not request.headers.get("Auth") == auth:
        return "Incorrect auth", 401
    with open("VPNcon.log", "w") as file:
        return "Success", 200


@app.route("/api/1.0/appconf", methods=["GET"])
def getAppConf():
    if not request.headers.get("Auth") == auth:
        return "Incorrect auth", 401
    with open("appconf.txt", "r") as file:
        string = file.read()
        return string


@app.route("/api/1.0/doc", methods=["GET"])
def getDoc():
    scroll = request.args.get("scroll")
    return render_template("doc.html", scroll=scroll)


if __name__ == "__main__":
    app.run(debug=True)
