import os

from flask import Flask, jsonify

from app import unzip, doc2html, thumbnail, health
from . import mdb, sendfile

CONFIG_NAME_MAPPER = {
    'dev': 'config.DevConfig',
    'test': 'config.TestConfig',
    'production': 'config.ProductionConfig',
}


def create_app(env_name='dev', **kwargs):
    config_name = env_name if env_name else os.environ.get('FLASK_ENV')
    assert config_name in CONFIG_NAME_MAPPER, "Unknown environment name: {}".format(config_name)

    # create app
    app = Flask(__name__, **kwargs)

    # load config
    app.config.from_object(CONFIG_NAME_MAPPER[config_name])

    # init extensions
    mdb.MDB(app, app.config['MDB_POOL_SIZE'])
    sendfile.Sendfile(app)

    # register blueprints
    app.register_blueprint(health.views.blueprint)
    app.register_blueprint(unzip.views.blueprint)
    app.register_blueprint(doc2html.views.blueprint)
    app.register_blueprint(thumbnail.views.blueprint)

    # register error handlers
    def errorhandler(error):
        app.logger.exception("Unexpected Error")
        resp = jsonify({"error": str(error)})
        resp.status_code = 500
        return resp

    app.errorhandler(Exception)(errorhandler)

    return app
