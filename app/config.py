class Config(object):
    SECRET_KEY = '0d6ba14fc678f6ccda715b8b7ddc11f2'
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif'}
    MAX_CONTENT_LENGTH = 16 * 1000 * 1000
    S3BUCKET = 'ece1779bucket'
    FRONTEND_PORT= 5000
    
