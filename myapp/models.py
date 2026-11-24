from sqlalchemy import Column , Integer , String , Boolean ,Float , DateTime ,ForeignKey
from myapp.database import Base
from sqlalchemy.orm import relationship
class Vehicle(Base):
    __tablename__ ="vehicle"

    id = Column(Integer, primary_key=True, index=True)
    registration_number = Column(
        String(20), unique=True, nullable=False
    )
    model = Column(String(50), nullable=False)
    status = Column(String(20), default="Available")

# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

class Drivers(Base):
    __tablename__ = "drivers"

    id = Column(Integer,primary_key=True , index=True)
    driver_name = Column(String(100) ,nullable=False )
    phone_no= Column(String(10) ,unique=True, nullable=False)
    license_no = Column(String(50) , nullable=False , unique=True)
    status = Column(String(50), default="Available" ,nullable=False)

# :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


class User(Base):
    __tablename__ = "users"

    id = Column(Integer , primary_key=True , index=True)
    name = Column(String(100) , nullable=False)
    email = Column(String(250) , nullable=False , unique=True)
    password_hash= Column(String(250) , nullable=False)
    role = Column(String(50) , default="user" , nullable=False )
    is_active= Column(Boolean, nullable=False , default=True)




class Ride(Base):
    __tablename__ = "rides"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    source = Column(String(100), nullable=False)
    destination = Column(String(100), nullable=False)
    departure_time = Column(DateTime, nullable=False)
    price = Column(Float, nullable=False)
    available_seats = Column(Integer, nullable=False)
    
    driver_id = Column(Integer ,  ForeignKey(User.id),nullable=False,)
    vehicle_id= Column(Integer , ForeignKey(Vehicle.id) , nullable=False)
    
    status = Column( String(30),
    default="Not Started",
    nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    driver = relationship("User", foreign_keys=[driver_id])
    vehicle = relationship("Vehicle", foreign_keys=[vehicle_id])
