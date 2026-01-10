from datetime import timedelta
class Config:
    SECRET_KEY="ABC123"
    SQLALCHEMY_DATABASE_URI="sqlite:///users.db"
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    JWT_SECRET_KEY="jwt_secret"
    JWT_ACCESS_EXPIRES=timedelta(minutes=1)
    JWT_REFRESH_TOKEN_EXPIRES=timedelta(days=7)
    