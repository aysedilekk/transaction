import os

SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://transaction:transaction2024@localhost/transaction"

ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30 minutes
ALGORITHM = "HS256"
JWT_SECRET_KEY = os.environ['JWT_SECRET_KEY']
