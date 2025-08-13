from sqlalchemy import create_engine
from models import Base

# Create the SQLite database
engine = create_engine("sqlite:///career.db")
Base.metadata.create_all(engine)

print("Database created successfully!")
