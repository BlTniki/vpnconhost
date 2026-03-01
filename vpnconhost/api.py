import logging
from flask import jsonify, request, Response
from dataclasses import asdict

from vpnconhost import peer_service, peers_bp
from vpnconhost.exceptions import EntityValidationFailedException

logger = logging.getLogger(__name__)


@peers_bp.route('/peers/<string:peer_id>', methods=['GET'])
def api_get_peer(peer_id: str):
    """Получить информацию о пире по ID."""
    logger.info("GET /peers/%s - Retrieving peer", peer_id)
    peer = peer_service.get_peer(peer_id)

    if peer is None:
        logger.info("GET /peers/%s - Peer not found", peer_id)
        return jsonify({
            'error': 'Not Found',
            'message': f'Peer with id={peer_id} not found'
        }), 404

    logger.info("GET /peers/%s - Peer retrieved successfully", peer_id)
    return jsonify({
        'peer': asdict(peer)
    }), 200


@peers_bp.route('/peers', methods=['POST'])
def api_create_peer():
    """Создать нового пира."""
    data = request.json
    if not data:
        logger.warning("POST /peers - No JSON data provided")
        raise EntityValidationFailedException('JSON data required')

    peer_id = data.get('peer_id')
    peer_ip = data.get('peer_ip')
    is_activated = data.get('is_activated', False)

    if not peer_id or not peer_ip:
        logger.warning("POST /peers - Missing required fields: peer_id or peer_ip")
        raise EntityValidationFailedException('Fields peer_id and peer_ip are required')

    logger.info("POST /peers - Creating peer: peer_id=%s, peer_ip=%s", peer_id, peer_ip)
    peer = peer_service.create_peer(peer_id, peer_ip, is_activated)

    logger.info("POST /peers - Peer created successfully: %s", peer_id)
    return jsonify({
        'message': 'Peer created successfully',
        'peer': asdict(peer)
    }), 201


@peers_bp.route('/peers/<string:peer_id>', methods=['DELETE'])
def api_delete_peer(peer_id: str):
    """Удалить пира по ID."""
    logger.info("DELETE /peers/%s - Deleting peer", peer_id)
    peer_service.delete_peer(peer_id)

    logger.info("DELETE /peers/%s - Peer deleted successfully", peer_id)
    return jsonify({
        'message': 'Peer deleted successfully',
        'peer_id': peer_id
    }), 200


@peers_bp.route('/peers/<string:peer_id>/activate', methods=['POST'])
def api_activate_peer(peer_id: str):
    """Активировать пира."""
    logger.info("POST /peers/%s/activate - Activating peer", peer_id)
    peer_service.switch_peer(peer_id, True)

    logger.info("POST /peers/%s/activate - Peer activated successfully", peer_id)
    return jsonify({
        'message': 'Peer activated successfully',
        'peer_id': peer_id,
        'is_activated': True
    }), 200


@peers_bp.route('/peers/<string:peer_id>/deactivate', methods=['POST'])
def api_deactivate_peer(peer_id: str):
    """Деактивировать пира."""
    logger.info("POST /peers/%s/deactivate - Deactivating peer", peer_id)
    peer_service.switch_peer(peer_id, False)

    logger.info("POST /peers/%s/deactivate - Peer deactivated successfully", peer_id)
    return jsonify({
        'message': 'Peer deactivated successfully',
        'peer_id': peer_id,
        'is_activated': False
    }), 200


@peers_bp.route('/peers/<string:peer_id>/download', methods=['GET'])
def api_download_peer(peer_id: str):
    """Скачать конфигурацию пира."""
    logger.info("GET /peers/%s/download - Downloading peer configuration", peer_id)
    conf = peer_service.get_peer_conf(peer_id)

    if conf is None:
        logger.info("GET /peers/%s/download - Peer configuration not found", peer_id)
        return jsonify({
            'error': 'Not Found',
            'message': f'Configuration for peer with id={peer_id} not found'
        }), 404

    logger.info("GET /peers/%s/download - Configuration retrieved successfully", peer_id)
    return Response(
        conf,
        mimetype='text/plain',
        headers={
            'Content-Disposition': f'attachment; filename={peer_id}.conf'
        }
    ), 200


@peers_bp.route('/peers/sync', methods=['POST'])
def api_sync_all_peers():
    """Синхронизировать всех пиров из БД в WireGuard."""
    logger.info("POST /peers/sync - Syncing all peers to WireGuard")
    peer_service.sync_all_peers()

    logger.info("POST /peers/sync - All peers synced successfully")
    return jsonify({
        'message': 'All peers synced to WireGuard successfully'
    }), 200
