import http

from flask import Blueprint, request
from flask.helpers import make_response, send_file

from app.km_audio.km_audio import KmAudio

blueprint = Blueprint('km_audio', __name__, url_prefix='/km_audio')


@blueprint.route('/build/<uid>')
def km_audio_build(uid):
    km = KmAudio(uid, request.args.get('language'))
    if km.run():
        return make_response("ok", http.HTTPStatus.OK)
    else:
        return make_response("missing info", 404)


@blueprint.route('/file/<uid>')
def km_audio_file(uid):
    km = KmAudio(uid, request.args.get('language'))
    if km.run():
        return send_file(km.path, mimetype="audio/mpeg", conditional=True)
    else:
        return make_response("missing info", 404)
