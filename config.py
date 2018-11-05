import os


class Config(object):
    """Base configuration."""

    BASE_DIR = os.environ.get('BASE_DIR', 'assets')
    LINKER_URL = os.environ.get('LINKER_URL', 'https://cdn.kabbalahmedia.info/')
    PUBLIC_PATH = os.environ.get('PUBLIC_PATH', '/assets')

    MDB_URL = os.environ.get('MDB_URL', 'postgres://localhost/mdb?sslmode=disable')
    MDB_POOL_SIZE = int(os.environ.get('MDB_POOL_SIZE', '2'))

    # Warning: symlinks don't work, see https://superuser.com/a/1089693
    SOFFICE_BIN = os.environ.get('SOFFICE_BIN', '/Applications/LibreOffice.app/Contents/MacOS/soffice')

    FFMPEG_BIN = os.environ.get('FFMPEG_BIN', '/usr/bin/ffmpeg')

    print('BASE_DIR: %s' % (BASE_DIR))
    print('LINKER_URL: %s' % (LINKER_URL))
    print('PUBLIC_PATH: %s' % (PUBLIC_PATH))
    print('MDB_URL: %s' % (MDB_URL))
    print('MDB_POOL_SIZE: %s' % (MDB_POOL_SIZE))
    print('SOFFICE_BIN: %s' % (SOFFICE_BIN))
    print('FFMPEG_BIN: %s' % (FFMPEG_BIN))


class ProductionConfig(Config):
    """Production configuration."""

    ENV = 'production'
    DEBUG = False
    USE_X_SENDFILE = True


class DevConfig(Config):
    """Development configuration."""

    ENV = 'dev'
    DEBUG = True


class TestConfig(Config):
    """Test configuration."""

    TESTING = True
    DEBUG = True
