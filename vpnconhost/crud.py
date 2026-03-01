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
    if not result:
        logger.debug("No peer found with id=%s", peer_id)
        return None
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
    try:
        executor.execute(query, **params)
        logger.debug("Peer created with id=%s", peer.peer_id)
    except UniqueConstraintError as exc:
        logger.error("Failed to create peer due to unique constraint violation: %s", exc)
        raise exc


@auto_transaction()
def update_peer(peer: Peer) -> None:
    executor = get_db_executor()
    query = """
        UPDATE peers
        SET peer_ip = :peer_ip,
            peer_public_key = :peer_public_key,
            peer_private_key = :peer_private_key,
            is_activated = :is_activated
        WHERE peer_id = :peer_id
    """
    params: dict[str, Any] = {
        'peer_id': peer.peer_id,
        'peer_ip': peer.peer_ip,
        'peer_public_key': peer.peer_public_key,
        'peer_private_key': peer.peer_private_key,
        'is_activated': peer.is_activated
    }
    try:
        executor.execute(query, **params)
        logger.debug("Peer with id=%s updated", peer.peer_id)
    except UniqueConstraintError as exc:
        logger.error("Failed to create peer due to unique constraint violation: %s", exc)
        raise exc


@auto_transaction()
def get_all_peers() -> list[Peer]:
    executor = get_db_executor()
    result = executor.execute("SELECT * FROM peers")
    if not result:
        logger.debug("No peers found in database")
        return []
    logger.debug("Found %d peers in database", len(result))
    return [Peer.from_raw(row) for row in result]


@auto_transaction()
def delete_peer(peer_id: str) -> None:
    executor = get_db_executor()
    query = "DELETE FROM peers WHERE peer_id = :peer_id"
    params = {'peer_id': peer_id}
    executor.execute(query, **params)
    logger.debug("Peer with id=%s deleted", peer_id)
