import confManipulate as Conf
import DBCRUD as DB
import CheckIsDataCorrect as Check
from logging.handlers import WatchedFileHandler
from flask import Flask, jsonify, request, make_response, send_from_directory

app = Flask(__name__)

with open("appconf.txt") as f:
    auth = f.readline().strip();
    workDir = f.readline().strip();
    ipAddress = f.readline().strip();
    testMode = True if f.readline().strip() == "YES" else False;


@app.before_first_request
def setup_logging():
    # Setup logging
    try:
        handler = WatchedFileHandler(f"{workDir}VPNcon.log")
        app.logger.addHandler(handler)
        print(f"Logging setupted")
    except Exception as e:
        print(e)
        print("im in windows?")


@app.route('/api/1.0/peers', methods=['GET'])
def getAllPeers():
    if not request.headers.get("Auth") == auth:
        return jsonify({'error': "Incorrect auth"}), 401
    try:
        peers = DB.allPeersREAD()
        return jsonify(peers), 200
    except Exception as e:
        e = e.args
        return jsonify({'error': e[0]}), e[1]


@app.route('/api/1.0/peers/<peerId>', methods=['GET'])
def getPeer(peerId):
    if not request.headers.get("Auth") == auth:
        return jsonify({'error': "Incorrect auth"}), 401

    try:
        peer = DB.peerREAD(peerId)
    except Exception as e:
        e = e.args
        return jsonify({'error': e[0]}), e[1]

    return jsonify({peerId: peer}), 200


@app.route('/api/1.0/peers', methods=['POST'])
def postPeer():
    if not request.headers.get("Auth") == auth:
        return jsonify({'error': "Incorrect auth"}), 401

    # Checking for json body
    if not request.headers.get("Content-Type") == "application/json":
        return jsonify({'error': 'Bad request'}), 400

    # Valid request body
    if not "peerId" in request.json.keys() or not "peerIp" in request.json.keys():
        return jsonify({'error': 'Bad request'}), 400
    peerId = request.json["peerId"]
    ipEnd = request.json["peerIp"]
    if not Check.isPeerIdCorrect(peerId):
        return jsonify({'error': 'Wrong peerId'}), 400
    if not Check.isIpEndCorrect(ipEnd):
        return jsonify({'error': 'Wrong peerIp'}), 400

    # generate peer's keys
    peerPrivateKey = Conf.createPeerPrivateKey(peerId)
    peerPublicKey = Conf.createPeerPublicKey(peerId)

    # add peer to database
    try:
        peer = DB.peerCREATE(peerId, ipEnd, peerPrivateKey, peerPublicKey)
    except Exception as e:
        e = e.args
        return jsonify({'error': e[0]}), e[1]

    # generating peer conf file and adding to wireguard
    peerIp = peer["Ip address"]
    Conf.createPeerConf(peerId, peerIp, peerPrivateKey)
    Conf.addPeerToVPN(peerId, peerIp, peerPublicKey)

    return jsonify({peerId: peer}), 200


@app.route('/api/1.0/peers/<peerId>', methods=['PUT'])
def updatePeer(peerId):
    if not request.headers.get("Auth") == auth:
        return jsonify({'error': "Incorrect auth"}), 401

    # Checking for json body
    if not request.headers.get("Content-Type") == "application/json":
        return jsonify({'error': 'Bad request'}), 400

    # Getting new states for peer from request body if in body new state
    ipEnd = request.json["peerIp"] if "peerIp" in request.json.keys() else None
    peerPrivateKey = request.json["peerPrivateKey"] if "peerPrivateKey" in request.json.keys() else None
    peerPublicKey = request.json["peerPublicKey"] if "peerPublicKey" in request.json.keys() else None

    # Valid request body only if state not None
    if ipEnd != None and not Check.isIpEndCorrect(ipEnd):
        return jsonify({'error': 'Wrong peerIp'}), 400

    # Updating peer in database
    try:
        peer = DB.peerUPDATE(peerId, ipEnd=ipEnd, peerPrivateKey=peerPrivateKey, peerPublicKey=peerPublicKey)
    except Exception as e:
        e = e.args
        return jsonify({'error': e[0]}), e[1]

    peerIp = peer["Ip address"]

    # Updating allowed-ips and config for this peer
    Conf.removePeerFromVPN(peerId, peer['Public key'])
    Conf.createPeerConf(peerId, peerIp, peer['Private key'])
    Conf.addPeerToVPN(peerId, peerIp, peer['Public key'])

    return jsonify({peerId: peer})


@app.route('/api/1.0/peers/<peerId>', methods=['DELETE'])
def deletePeer(peerId):
    if not request.headers.get("Auth") == auth:
        return jsonify({'error': "Incorrect auth"}), 401
    # Deleting peer from database
    try:
        peer = DB.peerDELETE(peerId)
    except Exception as e:
        e = e.args
        return jsonify({'error': e[0]}), e[1]

    Conf.removePeerFromVPN(peerId, peer['Public key'])
    Conf.deleteConfAndKeys(peerId)

    return jsonify({'result': True})


@app.route('/api/1.0/download_conf/<peerId>', methods=['GET'])
def return_peerConf(peerId):
    if not request.headers.get("Auth") == auth:
        return jsonify({'error': "Incorrect auth"}), 401
    if testMode:
        return "success"
    try:
        DB.peerREAD(peerId)
    except Exception as e:
        e = e.args
        return jsonify({"error": e[0]}), e[1]
    filename = f'{peerId}.conf'
    directory = f'{workDir}peersConf/'
    response = make_response(send_from_directory(directory, filename, as_attachment=True))
    return response


@app.route("/api/1.0/logs", methods=["GET"])
def get_logs():
    with open("VPNcon.log", "r") as f:
        str = f.read()
        return str


@app.route("/api/1.0/logs", methods=["DELETE"])
def del_logs():
    with open("VPNcon.log", "w") as f:
        None
    return jsonify({"result": "success"}), 200


if __name__ == "__main__":
    app.run(debug=True)
