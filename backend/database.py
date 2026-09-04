import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

# Use SQLite for the hackathon
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(ROOT, 'flowguard.db')}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def initialize_database() -> None:
    """Create tables and add columns needed by upgraded demo databases."""
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    user_columns = {column["name"] for column in inspector.get_columns("users")}
    with engine.begin() as connection:
        if "email" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR"))
        if "phone" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email_unique ON users(email)"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_phone_unique ON users(phone)"))
        transaction_columns = {column["name"] for column in inspector.get_columns("transactions")}
        for name in ("category", "description", "source"):
            if name not in transaction_columns:
                connection.execute(text(f"ALTER TABLE transactions ADD COLUMN {name} VARCHAR"))

# Dependency for FastAPI endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
