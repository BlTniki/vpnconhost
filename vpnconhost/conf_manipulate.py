"""
Этот модуль я писал когда был новичком в Python и Linux.
Я оставил этот модуль с минимальными изменениями, так как он работает и мне лень его переписывать.
"""

import subprocess
import os

from vpnconhost.config import Config



if Config.WIREGUARD_MOCK_MODE:
    def createPeerPrivateKey(peerId:str):
        return "private_lol_kek"


    def createPeerPublicKey(peerId:str):
        return "public_lol_kek"


    def createPeerConf(peerId:str, peerIp:str, peerPrivateKey:str):
        return None


    def addPeerToVPN(peerId:str, peerIp:str, peerPublicKey:str):
        return "Success"


    def removePeerFromVPN(peerId:str, peerPublicKey:str):
        return True


    def deleteConfAndKeys(peerId:str):
        return True

    def getPeerConfPath(peerId:str):
        return f"./peersConf/{peerId}.conf"


else:
    def createPeerPrivateKey(peerId:str):
        cmd = f'{Config.SUDO_CMD}wg genkey |  tee {Config.WORK_DIR}/keys/{peerId}Private.key'
        return runTmpScript(peerId, cmd)[:-1]


    def createPeerPublicKey(peerId:str):
        cmd = f'{Config.SUDO_CMD}cat {Config.WORK_DIR}keys/{peerId}Private.key | wg pubkey | tee {Config.WORK_DIR}keys/{peerId}Public.key'
        return runTmpScript(peerId, cmd)[:-1]


    def createPeerConf(peerId:str, peerIp:str, peerPrivateKey:str):
        if Config.OBFUSCATOR_IP == "null":
            str = f"[Interface]\nPrivateKey = {peerPrivateKey}\nAddress = {peerIp}\nDNS = {Config.WIREGUARD_DNS}\n[Peer]\nPublicKey = {Config.WIREGUARD_PUBLIC_KEY}\nAllowedIPs = 0.0.0.0/0, ::/0\nEndpoint = {Config.WIREGUARD_ADDRESS}\n"
        else:
            str = f"[Interface]\nPrivateKey = {peerPrivateKey}\nAddress = {peerIp}\nDNS = {Config.WIREGUARD_DNS}\n[Peer]\nPublicKey = {Config.WIREGUARD_PUBLIC_KEY}\nAllowedIPs = 0.0.0.0/0, ::/0\nEndpoint = {Config.OBFUSCATOR_IP}\n"
        with open(f"{Config.WORK_DIR}peersConf/{peerId}.conf", "w") as fconf:
            fconf.write(str)


    def addPeerToVPN(peerId:str, peerIp:str, peerPublicKey:str):
        cmd = f'{Config.SUDO_CMD}wg set wg0 peer {peerPublicKey} allowed-ips {peerIp}/32'
        return runTmpScript(peerId, cmd)


    def deleteConfAndKeys(peerId:str):
        cmd = f'{Config.SUDO_CMD}rm {Config.WORK_DIR}peersConf/{peerId}.conf\n{Config.SUDO_CMD}rm {Config.WORK_DIR}keys/{peerId}Public.key\n{Config.SUDO_CMD}rm {Config.WORK_DIR}keys/{peerId}Private.key'
        runTmpScript(peerId, cmd)

        return True

    def removePeerFromVPN(peerId:str, peerPublicKey:str):
        cmd = f'{Config.SUDO_CMD}wg set wg0 peer {peerPublicKey} remove'
        runTmpScript(peerId, cmd)

        return True

    def runTmpScript(peerId:str, cmd:str):
        with open(f'{Config.WORK_DIR}tmpScripts/{peerId}TmpScript.sh', 'w') as f:
            f.write(f'#!/bin/bash\nexport PATH="/usr/bin:$PATH"\n{cmd}')
        os.chmod(f'{Config.WORK_DIR}tmpScripts/{peerId}TmpScript.sh', 0o777)
        try:
            stdout = subprocess.check_output(f'{Config.WORK_DIR}tmpScripts/{peerId}TmpScript.sh', shell=True,
                                             stderr=subprocess.STDOUT).decode('utf-8')
        except subprocess.CalledProcessError as e:
            raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
        return stdout

    def getPeerConfPath(peerId:str):
        return f"{Config.WORK_DIR}peersConf/{peerId}.conf"


if __name__ == "__main__":
    name = 'test'
    ip = '10.8.0.10'
    x = createPeerPrivateKey(name)
    y = createPeerPublicKey(name)
    print("=======================================")
    print(x, y)
    #createPeerConf(name, ip, x)
    #addPeerToVPN(ip, y)
