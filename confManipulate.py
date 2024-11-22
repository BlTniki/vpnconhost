import subprocess
import os

with open("appconf.txt") as f:
    auth = f.readline().strip();
    workDir = f.readline().strip();
    ipAddress = f.readline().strip();
    testMode = True if f.readline().strip() == "YES" else False;
    sudoCmd = f.readline().strip() + " ";
    dns = f.readline().strip("\n");
    serverPubKey = f.readline().strip("\n");
    obfuscatorIp = f.readline().strip("\n");



if testMode:
    print ("lol")
    def createPeerPrivateKey(peerId=str):
        return "private_lol_kek"


    def createPeerPublicKey(peerId=str):
        return "public_lol_kek"


    def createPeerConf(peerId=str, peerIp=str, peerPrivateKey=str):
        return None


    def addPeerToVPN(peerId=str, peerIp=str, peerPublicKey=str):
        return "Success"


    def removePeerFromVPN(peerId=str, peerPublicKey=str):
        return True


    def deleteConfAndKeys(peerId=str):
        return True


else:
    def createPeerPrivateKey(peerId=str):
        cmd = f'{sudoCmd}wg genkey |  tee {workDir}/keys/{peerId}Private.key'
        return runTmpScript(peerId, cmd)[:-1]


    def createPeerPublicKey(peerId=str):
        cmd = f'{sudoCmd}cat {workDir}keys/{peerId}Private.key | wg pubkey | tee {workDir}keys/{peerId}Public.key'
        return runTmpScript(peerId, cmd)[:-1]


    def createPeerConf(peerId=str, peerIp=str, peerPrivateKey=str):
        if obfuscatorIp == "null":
            str = f"[Interface]\nPrivateKey = {peerPrivateKey}\nAddress = {peerIp}\nDNS = {dns}\n[Peer]\nPublicKey = {serverPubKey}\nAllowedIPs = 0.0.0.0/0, ::/0\nEndpoint = {ipAddress}\n"
        else:
            str = f"[Interface]\nPrivateKey = {peerPrivateKey}\nAddress = {peerIp}\nDNS = {dns}\n[Peer]\nPublicKey = {serverPubKey}\nAllowedIPs = 0.0.0.0/0, ::/0\nEndpoint = {obfuscatorIp}\n"
        with open(f"{workDir}peersConf/{peerId}.conf", "w") as fconf:
            fconf.write(str)


    def addPeerToVPN(peerId=str, peerIp=str, peerPublicKey=str):
        cmd = f'{sudoCmd}wg set wg0 peer {peerPublicKey} allowed-ips {peerIp}/32'
        return runTmpScript(peerId, cmd)


    def deleteConfAndKeys(peerId=str):
        cmd = f'{sudoCmd}rm {workDir}peersConf/{peerId}.conf\n{sudoCmd}rm {workDir}keys/{peerId}Public.key\n{sudoCmd}rm {workDir}keys/{peerId}Private.key'
        runTmpScript(peerId, cmd)

        return True

    def removePeerFromVPN(peerId=str, peerPublicKey=str):
        cmd = f'{sudoCmd}wg set wg0 peer {peerPublicKey} remove'
        runTmpScript(peerId, cmd)

        return True

    def runTmpScript(peerId, cmd):
        with open(f'{workDir}tmpScripts/{peerId}TmpScript.sh', 'w') as f:
            f.write(f'#!/bin/bash\nexport PATH="/usr/bin:$PATH"\n{cmd}')
        os.chmod(f'{workDir}tmpScripts/{peerId}TmpScript.sh', 0o777)
        try:
            stdout = subprocess.check_output(f'{workDir}tmpScripts/{peerId}TmpScript.sh', shell=True,
                                             stderr=subprocess.STDOUT).decode('utf-8')
        except subprocess.CalledProcessError as e:
            raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
        return stdout

if __name__ == "__main__":
    name = 'test'
    ip = '10.8.0.10'
    x = createPeerPrivateKey(name)
    y = createPeerPublicKey(name)
    print("=======================================")
    print(x, y)
    #createPeerConf(name, ip, x)
    #addPeerToVPN(ip, y)
