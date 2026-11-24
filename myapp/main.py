
import os
from datetime import datetime, timedelta, timezone
from sqlalchemy import update
import jwt
from jwt.exceptions import InvalidTokenError
from dotenv import load_dotenv

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pwdlib import PasswordHash

from myapp.database import Base, engine, get_db
from myapp.models import Vehicle, Drivers, User , Ride , Bookings   
from myapp.schemas import (
    VehicleCreate,
    VehicleResponse,
    DriverCreate,
    DriverResponse,
    UserCreate,
    UserResponse,
    UserLogin,
    UserUpdate,
    RideCreate,
    RideResponse ,
    BookingCreate,
    BookingResponse
)

# ==================== JWT CONFIGURATION ====================

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY is missing from .env")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

bearer_scheme = HTTPBearer()


def create_access_token(user_id: int):
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expire,
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


# ==================== AUTHENTICATION ====================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        user_id = int(payload["sub"])

    except (InvalidTokenError, ValueError, KeyError, TypeError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    current_user = db.query(User).filter(
        User.id == user_id
    ).first()

    if current_user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    if not current_user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Your account is inactive",
        )

    return current_user


# ==================== FASTAPI CONFIGURATION ====================

app = FastAPI(title="FleetFlow API")

password_hash = PasswordHash.recommended()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


# ==================== HOME API ====================

@app.get("/")
def home():
    return {"message": "FleetFlow API is running"}


# ==================== VEHICLE APIs ====================

@app.post("/vehicles", response_model=VehicleResponse)
def create_vehicle(
    vehicle: VehicleCreate,
    db: Session = Depends(get_db),
):
    existing = db.query(Vehicle).filter(
        Vehicle.registration_number == vehicle.registration_number
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Vehicle registration already exists",
        )

    new_vehicle = Vehicle(**vehicle.model_dump())

    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)

    return new_vehicle


@app.get("/vehicles", response_model=list[VehicleResponse])
def get_vehicles(db: Session = Depends(get_db)):
    return db.query(Vehicle).order_by(Vehicle.id).all()


@app.put("/vehicles/{vehicle_id}")
def update_vehicle(
    vehicle_id: int,
    vehicle: VehicleCreate,
    db: Session = Depends(get_db),
):
    db_vehicle = db.query(Vehicle).filter(
        Vehicle.id == vehicle_id
    ).first()

    if db_vehicle is None:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found",
        )

    db_vehicle.registration_number = vehicle.registration_number
    db_vehicle.model = vehicle.model
    db_vehicle.status = vehicle.status

    db.commit()
    db.refresh(db_vehicle)

    return db_vehicle


@app.delete("/vehicles/{vehicle_id}")
def delete_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
):
    db_vehicle = db.query(Vehicle).filter(
        Vehicle.id == vehicle_id
    ).first()

    if db_vehicle is None:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found",
        )

    db.delete(db_vehicle)
    db.commit()

    return {"message": "Vehicle deleted successfully"}


# ==================== DRIVER APIs ====================

@app.get("/driver", response_model=list[DriverResponse])
def get_drivers(db: Session = Depends(get_db)):
    return db.query(Drivers).order_by(Drivers.id).all()


@app.post("/driver", response_model=DriverResponse)
def create_driver(
    driver: DriverCreate,
    db: Session = Depends(get_db),
):
    existing_driver = db.query(Drivers).filter(
        Drivers.phone_no == driver.phone_no
    ).first()

    if existing_driver:
        raise HTTPException(
            status_code=409,
            detail="Driver phone number already exists",
        )

    new_driver = Drivers(**driver.model_dump())

    db.add(new_driver)
    db.commit()
    db.refresh(new_driver)

    return new_driver


# ==================== SIGNUP API ====================

@app.post("/signup", response_model=UserResponse, status_code=201)
def signup(
    user: UserCreate,
    db: Session = Depends(get_db),
):
    existing_user = db.query(User).filter(
        User.email == user.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )

    hashed_password = password_hash.hash(user.password)

    new_user = User(
        name=user.name,
        email=user.email,
        password_hash=hashed_password,
        role=user.role,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# ==================== USER MANAGEMENT APIs ====================

@app.get("/allusers", response_model=list[UserResponse])
def getusers(db: Session = Depends(get_db)):
    return db.query(User).filter(User.role=="user").order_by(User.id.asc()).all()


@app.delete("/deleteuser/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    existing_user = db.query(User).filter(
        User.id == user_id
    ).first()

    if existing_user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    db.delete(existing_user)
    db.commit()

    return {
        "message": "User deleted successfully",
        "user_id": user_id,
    }


@app.patch("/users/{user_id}/status", response_model=UserResponse)
def toggle_user_status(
    user_id: int,
    db: Session = Depends(get_db),
):
    existing_user = db.query(User).filter(
        User.id == user_id
    ).first()

    if existing_user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    existing_user.is_active = not existing_user.is_active

    db.commit()
    db.refresh(existing_user)

    return existing_user


# ==================== EDIT MY PROFILE API ====================

@app.patch("/users/me", response_model=UserResponse)
def update_my_profile(
    profile_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    update_data = profile_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="Provide at least one field to update",
        )

    if "name" in update_data and update_data["name"] is None:
        raise HTTPException(
            status_code=422,
            detail="Name cannot be null",
        )

    if "email" in update_data and update_data["email"] is None:
        raise HTTPException(
            status_code=422,
            detail="Email cannot be null",
        )

    if "email" in update_data:
        existing_email = db.query(User).filter(
            User.email == update_data["email"],
            User.id != current_user.id,
        ).first()

        if existing_email:
            raise HTTPException(
                status_code=409,
                detail="Email already registered",
            )

    for field, value in update_data.items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)

    return current_user


# ==================== LOGIN API WITH JWT ====================

@app.post("/login")
def login(
    user_data: UserLogin,
    db: Session = Depends(get_db),
):
    existing_user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    if not password_hash.verify(
        user_data.password,
        existing_user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    if not existing_user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Your account is inactive",
        )

    access_token = create_access_token(existing_user.id)

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "id": existing_user.id,
        "name": existing_user.name,
        "email": existing_user.email,
        "role": existing_user.role,
    }



@app.post("/rides", response_model=RideResponse, status_code=201)
def create_ride(
    ride: RideCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. Only admin can create rides
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin can create rides",
        )

    # 2. Check that the selected user exists and is a driver
    selected_driver = db.query(User).filter(
        User.id == ride.driver_id,
        User.role == "driver",
    ).first()

    if selected_driver is None:
        raise HTTPException(
            status_code=404,
            detail="Driver not found. Select a valid driver.",
        )
    selected_vehicle = db.query(Vehicle).filter(
    Vehicle.id == ride.vehicle_id
    ).first()

    if selected_vehicle is None:
     raise HTTPException(
        status_code=404,
        detail="Vehicle not found"
    )
    if selected_vehicle.status != "Available":
        raise HTTPException(
        status_code=400,
        detail="Vehicle is not available"
    )
    # 3. Create ride with the selected driver
    new_ride = Ride(
        title=ride.title,
        source=ride.source,
        destination=ride.destination,
        departure_time=ride.departure_time,
        price=ride.price,
        available_seats=ride.available_seats,
        driver_id=ride.driver_id,
        vehicle_id =ride.vehicle_id
    )

    # 4. Save ride to database
    db.add(new_ride)
    db.commit()
    db.refresh(new_ride)

    return new_ride

@app.get("/drivers")
def get_drivers(db: Session = Depends(get_db)):
    drivers = db.query(User).filter(
        User.role == "driver",
        User.is_active == True
    ).all()

    return drivers
    
@app.get("/rides", response_model=list[RideResponse])
def get_rides(db: Session = Depends(get_db)):
    now = datetime.now()
    rides = db.query(Ride).filter( Ride.is_active == True,
        Ride.departure_time >= now).order_by(Ride.departure_time.asc()).all()

    result = []

    for ride in rides:
        result.append({
            "id": ride.id,
            "title": ride.title,
            "source": ride.source,
            "destination": ride.destination,
            "departure_time": ride.departure_time,
            "price": ride.price,
            "available_seats": ride.available_seats,
            "status": ride.status,
            "driver_id": ride.driver_id,
            "vehicle_id": ride.vehicle_id,
            "driver_name": ride.driver.name if ride.driver else None,
            "vehicle_name": ride.vehicle.model if ride.vehicle else None
        })

    return result

@app.patch("/rides/{ride_id}/availability")
def update_ride_availability(
    ride_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ride = db.query(Ride).filter(
        Ride.id == ride_id
    ).first()

    if not ride:
        raise HTTPException(
            status_code=404,
            detail="Ride not found"
        )

    ride.is_active = is_active

    db.commit()
    db.refresh(ride)

    return {
        "message": "Ride availability updated",
        "ride_id": ride.id,
        "is_active": ride.is_active
    }

@app.post(
    "/bookings",
    response_model=BookingResponse,
    status_code=201
)
def create_booking(
    booking: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Only normal users can book rides
    if current_user.role != "user":
        raise HTTPException(
            status_code=403,
            detail="Only normal users can book rides"
        )

    # 2. Find the selected ride
    ride = db.query(Ride).filter(
        Ride.id == booking.ride_id,
        Ride.is_active == True
    ).first()

    if ride is None:
        raise HTTPException(
            status_code=404,
            detail="Ride not found or inactive"
        )

    # 3. Check that the ride has not departed
    if ride.departure_time < datetime.now():
        raise HTTPException(
            status_code=400,
            detail="This ride has already departed"
        )

    # 4. Calculate the price on the backend
    total_price = ride.price * booking.seats_booked

    try:
        # 5. Check and reserve seats in one database statement
        result = db.execute(
            update(Ride)
            .where(
                Ride.id == booking.ride_id,
                Ride.is_active == True,
                Ride.available_seats >= booking.seats_booked
            )
            .values(
                available_seats=(
                    Ride.available_seats - booking.seats_booked
                )
            )
        )

        if result.rowcount != 1:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Not enough seats available"
            )

        # 6. Create the booking for the logged-in user
        new_booking = Bookings(
            user_id=current_user.id,
            ride_id=ride.id,
            seats_booked=booking.seats_booked,
            total_price=total_price,
            status="Pending"
        )

        db.add(new_booking)
        db.commit()
        db.refresh(new_booking)

        return new_booking

    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Booking could not be created"
        )