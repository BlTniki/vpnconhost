#!/bin/bash
export PATH="/usr/bin:$PATH"
sudo wg set wg0 peer vK2gOVvgf+KX9H68hlcZ01Z9aO6pBCCLtBhnty6+OXc= remove
sudo rm /root/VPNcon/clientsConf/test.conf
sudo rm /root/VPNcon/keys/testPublic.key
sudo rm /root/VPNcon/keys/testPrivate.key