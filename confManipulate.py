import subprocess
import os

with open("appconf.txt") as f:
    auth = f.readline().strip();
    workDir = f.readline().strip();
    ipAddress = f.readline().strip();
    testMode = True if f.readline().strip() == "YES" else False;


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


else:
    def createPeerPrivateKey(peerId=str):
        genPrivateCmd = f'sudo wg genkey |  tee {workDir}/keys/{peerId}Private.key'
        with open(f'{workDir}tmpScripts/{peerId}TmpScript.sh', 'w') as f:
            f.write(f'#!/bin/bash\nexport PATH="/usr/bin/:$PATH"\n{genPrivateCmd}')
        os.chmod(f'{workDir}tmpScripts/{peerId}TmpScript.sh', 0o777)
        try:
            stdout = subprocess.check_output(f'{workDir}tmpScripts/{peerId}TmpScript.sh', shell=True, stderr=subprocess.STDOUT).decode('utf-8')
        except subprocess.CalledProcessError as e:
            raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))

        return stdout[:-1]


    def createPeerPublicKey(peerId=str):
        genPublicCmd = f'sudo cat {workDir}keys/{peerId}Private.key | wg pubkey | tee {workDir}keys/{peerId}Public.key'
        with open(f'{workDir}tmpScripts/{peerId}TmpScript.sh', 'w') as f:
            f.write(f'#!/bin/bash\nexport PATH="/usr/bin/:$PATH"\n{genPublicCmd}')
        os.chmod(f'{workDir}tmpScripts/{peerId}TmpScript.sh', 0o777)
        try:
            stdout = subprocess.check_output(f'{workDir}tmpScripts/{peerId}TmpScript.sh', shell=True, stderr=subprocess.STDOUT).decode('utf-8')
        except subprocess.CalledProcessError as e:
            raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))

        return stdout[:-1]


    def createPeerConf(peerId=str, peerIp=str, peerPrivateKey=str):
        str = f"[Interface]\nPrivateKey = {peerPrivateKey}\nAddress = {peerIp}\nDNS = 8.8.8.8, 8.8.4.4\n[Peer]\nPublicKey = fNMyUeM9jLy0CRJ209mBW65mXm7RM0QY6JF0SIH+2gE=\nAllowedIPs = 0.0.0.0/0, ::/0\nEndpoint = {ipAddress}\n"
        with open(f"{workDir}peersConf/{peerId}.conf", "w") as fconf:
            fconf.write(str)


    def addPeerToVPN(peerId=str, peerIp=str, peerPublicKey=str):
        cmd = f'sudo wg set wg0 peer {peerPublicKey} allowed-ips {peerIp}/32'
        with open(f'{workDir}tmpScripts/{peerId}TmpScript.sh', 'w') as f:
            f.write(f'#!/bin/bash\nexport PATH="/usr/bin:$PATH"\n{cmd}')
        os.chmod(f'{workDir}tmpScripts/{peerId}TmpScript.sh', 0o777)
        try:
            stdout = subprocess.check_output(f'{workDir}tmpScripts/{peerId}TmpScript.sh', shell=True, stderr=subprocess.STDOUT).decode('utf-8')
        except subprocess.CalledProcessError as e:
            raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))

        return stdout


    def removePeerFromVPN(peerId=str, peerPublicKey=str):
        cmd = f'sudo wg set wg0 peer {peerPublicKey} remove\nrm /root/VPNcon/peersConf/{peerId}.conf\nsudo rm /root/VPNcon/keys/{peerId}Public.key\nsudo rm /root/VPNcon/keys/{peerId}Private.key'
        with open(f'{workDir}tmpScripts/{peerId}TmpScript.sh', 'w') as f:
            f.write(f'#!/bin/bash\nexport PATH="/usr/bin:$PATH"\n{cmd}')
        os.chmod(f'{workDir}tmpScripts/{peerId}TmpScript.sh', 0o777)
        try:
            stdout = subprocess.check_output(f'{workDir}tmpScripts/{peerId}TmpScript.sh', shell=True,
                                             stderr=subprocess.STDOUT).decode('utf-8')
        except subprocess.CalledProcessError as e:
            raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))

        return True


if __name__ == "__main__":
    name = 'test'
    ip = '10.8.0.10'
    x = createPeerPrivateKey(name)
    y = createPeerPublicKey(name)
    print("=======================================")
    print(x, y)
    #createPeerConf(name, ip, x)
    #addPeerToVPN(ip, y)
