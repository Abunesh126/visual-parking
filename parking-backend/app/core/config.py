DB_USER = "root"
DB_PASSWORD = "password"   # change to your real password
DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_NAME = "parking_db"

SQLALCHEMY_DATABASE_URI = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
