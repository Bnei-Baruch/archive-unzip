import os

from flask import Flask, jsonify
from flask_cors import CORS

from app import unzip, doc2html, thumbnail, health, preview, countwords, timecode, km_audio
from . import mdb, sendfile, fetchfile

CONFIG_NAME_MAPPER = {
    'development': 'config.DevConfig',
    'test': 'config.TestConfig',
    'production': 'config.ProductionConfig',
}


def create_app(env, **kwargs):
    assert env in CONFIG_NAME_MAPPER, "Unknown environment name: {}".format(env)

    # create app
    app = Flask(__name__, **kwargs)

    # load config
    app.config.from_object(CONFIG_NAME_MAPPER[env])

    # init extensions
    mdb.MDB(app, app.config['MDB_POOL_SIZE'])
    sendfile.Sendfile(app)
    fetchfile.Fetchfile(app)

    # register blueprints
    app.register_blueprint(health.views.blueprint)
    app.register_blueprint(unzip.views.blueprint)
    app.register_blueprint(doc2html.views.htmlBlueprint)
    app.register_blueprint(preview.views.htmlByBLobBlueprint)
    app.register_blueprint(doc2html.views.docxBlueprint)
    app.register_blueprint(doc2html.views.textBlueprint)
    app.register_blueprint(doc2html.views.prepareBlueprint)
    app.register_blueprint(countwords.views.countwordsBlueprint)
    app.register_blueprint(thumbnail.views.blueprint)
    app.register_blueprint(timecode.views.blueprint)
    app.register_blueprint(km_audio.views.blueprint)

    # register error handlers
    def errorhandler(error):
        app.logger.exception("Unexpected Error")
        resp = jsonify({"error": str(error)})
        resp.status_code = 500
        return resp

    app.errorhandler(Exception)(errorhandler)

    # enable CORS on lower environments.
    # in production nginx does that in front of us
    if env != "production":
        CORS(app)

    return app
