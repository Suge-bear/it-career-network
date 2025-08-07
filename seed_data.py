from models import Base, CareerPath
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite:///data.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db = Session()

paths = [
    CareerPath(id="helpdesk", title="Help Desk Technician", requirements="Customer service,Basic networking,Windows OS,Ticketing systems"),
    CareerPath(id="sysadmin", title="System Administrator", requirements="Windows Server,Linux CLI,Virtualization,Active Directory"),
    CareerPath(id="cloud", title="Cloud Engineer", requirements="AWS,GCP,Azure,Python,Containers")
]

db.add_all(paths)
db.commit()
