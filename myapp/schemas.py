
from pydantic import BaseModel, ConfigDict , EmailStr, Field 
from datetime import datetime
from typing import Literal

class VehicleCreate(BaseModel):
    registration_number: str
    model: str
    status: str = "Available"


class VehicleResponse(BaseModel):
    id: int
    registration_number: str
    model: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class DriverCreate(BaseModel):
    driver_name:str
    phone_no:str
    license_no:str
    status:str = "Available"

class DriverResponse(BaseModel):

    id:int
    driver_name:str
    phone_no:str
    license_no:str
    status:str 

    model_config =ConfigDict(from_attributes=True)


# Signup Schema
class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Literal["user", "driver"] = "user"

# Login Schema
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Response Schema
class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    is_active: bool

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    name:str | None = Field(default=None , min_length=2, max_length=100)
    email:EmailStr | None


class RideCreate(BaseModel):
    title: str = Field(min_length=3, max_length=100)
    source: str = Field(min_length=2, max_length=100)
    destination: str = Field(min_length=2, max_length=100)
    departure_time: datetime
    price: float = Field(gt=0)
    available_seats: int = Field(ge=1)
    driver_id: int
    vehicle_id: int


class RideResponse(BaseModel):
    id: int
    title: str
    source: str
    destination: str
    departure_time: datetime
    price: float
    available_seats: int
    status: str
    driver_id: int
    vehicle_id: int
    driver_name: str | None = None
    vehicle_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class BookingCreate(BaseModel):
    ride_id: int
    seats_booked: int = Field(gt=0)

class BookingResponse(BaseModel):
    id: int
    user_id: int
    ride_id: int
    seats_booked: int
    total_price: float
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)