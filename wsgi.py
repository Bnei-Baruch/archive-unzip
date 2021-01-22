import os

from app.app import create_app

# from werkzeug.debug import DebuggedApplication

app = create_app(os.environ.get('FLASK_ENV', 'production'))

# Set DEBUG True and uncomment rows below to see logger.info/debug/error
# in standard output of wsgi application.
DEBUG = False
# app.debug = DEBUG
# app.config['DEBUG'] = DEBUG
# app.wsgi_app = DebuggedApplication(app.wsgi_app, DEBUG)
# app.config.from_object('config')
# app.config.update(DEBUG=DEBUG)
# app.config['DEBUG'] = DEBUG

if __name__ == '__main__':
    app.run(debug=DEBUG)
