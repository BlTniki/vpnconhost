from flask import jsonify, request, Blueprint

from vpnconhost.db import auto_transaction

bp = Blueprint('api', __name__)


bp.route('/peers/<int:peer_id>', methods=['GET'])
@auto_transaction()
def api_get_peer(peer_id: int):
    pass


bp.route('/peers', methods=['POST'])
@auto_transaction()
def api_create_peer():
    data = request.json
    if not data:
        return jsonify({'error': 'JSON data required'}), 400
    pass


bp.route('/peers/<int:peer_id>', methods=['DELETE'])
@auto_transaction()
def api_delete_peer(peer_id: int):
    pass


def _switch_peer(peer_id: int, new_state: bool):
    pass


bp.route('/peers/<int:peer_id>/activate', methods=['POST'])
@auto_transaction()
def api_activate_peer(peer_id: int):
    _switch_peer(peer_id, True)
    return jsonify({'status': 'activated'})


bp.route('/peers/<int:peer_id>/deactivate', methods=['POST'])
@auto_transaction()
def api_deactivate_peer(peer_id: int):
    _switch_peer(peer_id, False)
    return jsonify({'status': 'deactivated'})

bp.route('/peers/<int:peer_id>/download', methods=['GET'])
@auto_transaction()
def api_download_peer(peer_id: int):
    pass