import logging
from typing import Any
from vpnconhost.db import auto_transaction, get_db_executor, UniqueConstraintError

from .model import Peer

logger = logging.getLogger(__name__)


@auto_transaction()
def get_peer(peer_id: str) -> Peer | None:
    executor = get_db_executor()
    result = executor.execute(
        "SELECT * FROM peers WHERE peer_id = :peer_id",
        **{"peer_id": peer_id}
    )
    if len(result) > 1:
        raise ValueError(f"Multiple peers found with id={peer_id}")
    logger.debug("Peer found: %s", result)
    return Peer.from_raw(result[0])

@auto_transaction()
def create_peer(peer: Peer) -> None:
    executor = get_db_executor()
    query = f"""
        INSERT INTO peers ({Peer.get_model_fields_joined()})
        VALUES (:peer_id, :peer_ip, :peer_public_key, :peer_private_key, :is_activated)
    """
    params: dict[str, Any] = {
        'peer_id': peer.peer_id,
        'peer_ip': peer.peer_ip,
        'peer_public_key': peer.peer_public_key,
        'peer_private_key': peer.peer_private_key,
        'is_activated': peer.is_activated
    }
    