import json
from secrets import token_hex as generateToken

try:
    f = open('validTokens.json')
except IOError as e:
    print(u'validTokens.json not exist, creating...')
    with open("validTokens.json", "w") as f:
        validTokens = dict()
        json.dump(validTokens, f, indent=4)
else:
    with f:
        print(u'validTokens.json exist')
        f.close()


def validTokensSave(validTokens):
    try:
        with open("validTokens.json", "w") as f:
            json.dump(validTokens, f, indent=4)
    except IOError:
        raise Exception("Internal Server Error", 500)


def validTokensRead():
    try:
        with open('validTokens.json') as f:
            validTokens = json.load(f)
    except IOError:
        raise Exception("Internal Server Error", 500)
    return validTokens


def generateTokenForPayload(payload):
    validTokens = validTokensRead()
    token = generateToken(32)
    validTokens[token] = payload
    validTokensSave(validTokens)
    return token


def returnPayloadByToken(token):
    validTokens = validTokensRead()
    try:
        payload = validTokens[token]
        return payload
    except KeyError as e:
        raise Exception("Wrong token", 400)