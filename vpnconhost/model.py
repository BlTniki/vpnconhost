from typing import Any
from dataclasses import dataclass

from vpnconhost.db import DataModel


@dataclass(frozen=True)
class Peer(DataModel):
    """Модель пира."""
    peer_id: str
    peer_ip: str
    peer_public_key: str
    peer_private_key: str
    is_activated: bool

    @staticmethod
    def from_raw(raw: tuple[Any, ...]) -> 'Peer':
        """Создаёт экземпляр `Peer` из сырых данных, полученных из БД.
        Args:
            raw (tuple[Any, ...]): Сырые данные из БД.

        Returns:
            Peer: Экземпляр `Peer`.
        Raises:
            ValueError: Если поля не приводятся к нужным типам.
        """
        fields = Peer.get_model_fields()
        data = dict(zip(fields, raw))
        try:
            peer_id = str(data['peer_id'])
            peer_ip = str(data['peer_ip'])
            peer_public_key = str(data['peer_public_key'])
            peer_private_key = str(data['peer_private_key'])
            is_activated = bool(data['is_activated'])
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"Invalid data for Peer: {data}"
            ) from exc

        return Peer(
            peer_id=peer_id,
            peer_ip=peer_ip,
            peer_public_key=peer_public_key,
            peer_private_key=peer_private_key,
            is_activated=is_activated
        )
