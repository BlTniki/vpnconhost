from abc import ABC, abstractmethod
import logging
import re

from vpnconhost.db import auto_transaction
from vpnconhost.db.db import UniqueConstraintError
from vpnconhost.wg_client import WGClient

from vpnconhost.exceptions import (
    EntityAlreadyExistsException,
    EntityNotExistsException,
    EntityValidationFailedException,
)
from .crud import get_peer, create_peer, update_peer, delete_peer, get_all_peers
from .model import Peer

logger = logging.getLogger(__name__)


_PEER_ID_REGEX = r"^[A-Za-z0-9]+_[0-9]+$"
_PEER_IP_REGEX = r"^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"


def is_peer_id_correct(peer_id: str):
    if (
        len(re.findall(_PEER_ID_REGEX, peer_id)) == 0
        or re.findall(_PEER_ID_REGEX, peer_id)[0] is not peer_id
    ):
        return False
    return True


def is_peer_ip_correct(peer_ip: str):
    tpl = re.compile(_PEER_IP_REGEX)
    result = re.match(tpl, peer_ip)
    # check is result is not a NoneType and result match completely matches peerIp
    if not result or result.group() is not peer_ip:
        return False
    ip_end = int(result.group(4))
    if ip_end < 1 or ip_end > 254:
        return False

    return True


class PeerService(ABC):

    @abstractmethod
    def create_peer(
        self,
        peer_id: str,
        peer_ip: str,
        is_activated: bool,
    ) -> Peer:
        pass

    @abstractmethod
    def get_peer(self, peer_id: str) -> Peer | None:
        pass

    @abstractmethod
    def get_peer_conf(self, peer_id: str) -> str | None:
        pass

    @abstractmethod
    def switch_peer(self, peer_id: str, is_activated: bool) -> None:
        pass

    @abstractmethod
    def delete_peer(self, peer_id: str) -> None:
        pass

    @abstractmethod
    def sync_all_peers(self) -> None:
        pass


class PeerServiceCRUD(PeerService):
    @auto_transaction()
    def create_peer(
        self,
        peer_id: str,
        peer_ip: str,
        is_activated: bool,
    ) -> Peer:
        logger.info("Creating peer with id: %s", peer_id)
        if not is_peer_id_correct(peer_id):
            logger.warning("Peer ID validation failed: %s", peer_id)
            raise EntityValidationFailedException(f"Peer ID '{peer_id}' is not valid")
        if not is_peer_ip_correct(peer_ip):
            logger.warning("Peer IP validation failed: %s", peer_ip)
            raise EntityValidationFailedException(f"Peer IP '{peer_ip}' is not valid")

        peer_private_key = WGClient.create_private_key()
        peer_public_key = WGClient.create_public_key(peer_private_key)
        peer = Peer(peer_id, peer_ip, peer_public_key, peer_private_key, is_activated)

        try:
            create_peer(peer)
        except UniqueConstraintError as exc:
            logger.warning(
                "Failed to create peer, already exists: peer_id=%s, peer_ip=%s",
                peer_id,
                peer_ip,
            )
            raise EntityAlreadyExistsException(
                f"Peer with id={peer_id} and ip={peer_ip} already exists"
            ) from exc

        if is_activated:
            WGClient.add_peer_to_wg(peer_ip, peer_public_key)
        logger.info("Peer created successfully: %s", peer_id)

        return peer

    @auto_transaction()
    def get_peer(self, peer_id: str) -> Peer | None:
        logger.debug("Retrieving peer with id: %s", peer_id)
        return get_peer(peer_id)

    @auto_transaction()
    def get_peer_conf(self, peer_id: str) -> str | None:
        logger.debug("Retrieving peer conf with id: %s", peer_id)
        peer = get_peer(peer_id)
        if peer is None:
            logger.warning("Peer not found for conf: %s", peer_id)
            raise EntityNotExistsException(f"Peer with id={peer_id} not found")
        return WGClient.get_peer_conf(peer.peer_ip, peer.peer_private_key)

    @auto_transaction()
    def switch_peer(self, peer_id: str, is_activated: bool) -> None:
        logger.info("Switching peer with id: %s, to: %s", peer_id, is_activated)
        peer = get_peer(peer_id)
        if peer is None:
            logger.warning("Peer not found for update: %s", peer_id)
            raise EntityNotExistsException(f"Peer with id={peer_id} not found")
        peer = Peer(
            peer_id,
            peer.peer_ip,
            peer.peer_public_key,
            peer.peer_private_key,
            is_activated,
        )
        update_peer(peer)
        if is_activated:
            WGClient.add_peer_to_wg(peer.peer_ip, peer.peer_public_key)
        else:
            WGClient.remove_peer_from_wg(peer.peer_public_key)
        logger.info("Peer switched successfully: %s", peer_id)

    @auto_transaction()
    def delete_peer(self, peer_id: str):
        logger.info("Deleting peer with id: %s", peer_id)
        peer = get_peer(peer_id)
        if peer is None:
            logger.warning("Peer not found for update: %s", peer_id)
            raise EntityNotExistsException(f"Peer with id={peer_id} not found")
        delete_peer(peer_id)
        WGClient.remove_peer_from_wg(peer.peer_public_key)
        logger.info("Peer deleted successfully: %s", peer_id)

    @auto_transaction()
    def sync_all_peers(self) -> None:
        logger.info("Syncing all peers from database to WireGuard")
        peers = get_all_peers()
        synced_count = 0
        for peer in peers:
            if peer.is_activated:
                WGClient.add_peer_to_wg(peer.peer_ip, peer.peer_public_key)
                synced_count += 1
                logger.debug("Synced peer: %s", peer.peer_id)
        logger.info("Sync completed: %d peers synced to WireGuard", synced_count)
