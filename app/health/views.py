from flask import Blueprint
from flask.json import jsonify

blueprint = Blueprint('health', __name__)


@blueprint.route('/health_check')
def health_check():
    return jsonify({'status': 'ok'})
