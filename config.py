from secrets import token_urlsafe

class Config(object):
    TESTING = True
    DEBUG = True
    DEVELOPMENT = True
    FLASK_ENV = 'development'
    SECRET_KEY = token_urlsafe(16)

    # Use SQLAlchemy with mysql-connector on your Docker MySQL (port 3308)
    SQLALCHEMY_DATABASE_URI = (
    "mysql+pymysql://meals_user:MealsPwd!123@127.0.0.1:3308/meals?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False