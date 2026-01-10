from flask import Blueprint

from .service import PeerService, PeerServiceCRUD

peer_service: PeerService = PeerServiceCRUD()

peers_bp = Blueprint('peers_api', __name__)

from .api import *