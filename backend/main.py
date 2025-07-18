from fastapi import FastAPI, HTTPException, Query, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import create_engine, text, func
from models.users import User as UserModel, UserRole, UserStatus
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from pydantic import BaseModel
import json
import math
import os
import logging
import uvicorn

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s | %(levelname)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

from database import SessionLocal, engine, get_db
from auth import (
    create_access_token,
    get_current_active_user,
    authenticate_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_initial_admin,
    Token,
    UserResponse,
    UserCreate,
    PasswordChangeRequest,
    get_user,
    get_password_hash,
    verify_password,
    change_password
)

from routers.users import create_user
from auth import get_user_by_email

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create initial admin user on startup
@app.on_event("startup")
async def startup_event():
    create_initial_admin()

# --- Lifespan Events ---
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events für FastAPI"""
    # Startup
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT COUNT(*) FROM tours"))
            count = result.fetchone()[0]
            print(f"✅ Datenbankverbindung erfolgreich. {count} Touren verfügbar.")
    except Exception as e:
        print(f"❌ Datenbankverbindung fehlgeschlagen: {e}")
    
    yield
    
    # Shutdown (falls benötigt)
    print("🔽 Backend wird heruntergefahren...")

# FastAPI App initialisieren
app = FastAPI(
    title="Tour Manager API",
    description="API für die Verwaltung und Visualisierung von GPX-Touren",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware für Frontend-Zugriff
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tourm.bansom.synology.me",
        "http://localhost:3000",  # für lokale Entwicklung
        "http://localhost:3001",  # für lokale Entwicklung mit Vite
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Konfiguration ---
# Database configuration is handled in database.py

# --- Pydantic Models ---
class TourBase(BaseModel):
    id: int
    name: str
    type: str
    date: str
    distance_km: float
    duration_s: float
    speed_kmh: float
    elevation_up: float
    elevation_down: float
    start_lat: float
    start_lon: float
    ebike: bool
    komootid: Optional[str] = None
    komoothref: Optional[str] = None
    track_geojson: Optional[Any] = None  # Can be string or dict

class TourDetail(TourBase):
    pass  # Inherits all fields from TourBase, including optional track_geojson

class TourSummary(BaseModel):
    total_tours: int
    total_distance: float
    total_duration: float
    total_elevation_up: float
    types: Dict[str, int]

class LocationFilter(BaseModel):
    latitude: float
    longitude: float
    radius_km: float = 10.0

class UserStatusUpdate(BaseModel):
    status: str  # Accept string, will validate against UserStatus values later

# --- Hilfsfunktionen ---
def get_db():
    """Datenbankverbindung für Dependency Injection"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Berechnet die Entfernung zwischen zwei GPS-Punkten in Kilometern (Haversine-Formel)"""
    R = 6371  # Erdradius in km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def point_in_radius(tour_geojson: str, center_lat: float, center_lon: float, radius_km: float) -> bool:
    """Prüft ob eine Tour durch einen bestimmten Radius um einen Punkt führt"""
    try:
        geojson_data = json.loads(tour_geojson)
        coordinates = geojson_data.get('coordinates', [])
        
        # Prüfe alle Punkte der Tour
        for coord in coordinates:
            lon, lat = coord
            distance = calculate_distance(center_lat, center_lon, lat, lon)
            if distance <= radius_km:
                return True
        return False
    except (json.JSONDecodeError, KeyError, IndexError):
        return False

# --- API Endpoints ---

@app.get("/")
async def root():
    """Health Check Endpoint"""
    return {"message": "Tour Manager API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint for Docker"""
    # Also print database information
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        users = db.query(UserModel).all()
        user_info = []
        for user in users:
            user_info.append({
                "id": user.id,
                "username": user.username,
                "hash_prefix": user.hashed_password[:15]
            })
        logger.error(f"USERS DB: {user_info}")
        
        # Check database file
        import os
        db_path = os.getenv("DATABASE_PATH", "unknown")
        logger.error(f"DATABASE PATH: {db_path}")
        if os.path.exists(db_path):
            logger.error(f"DATABASE FILE EXISTS: Yes, size={os.path.getsize(db_path)}")
        else:
            logger.error(f"DATABASE FILE EXISTS: No")
    except Exception as e:
        logger.error(f"DATABASE ERROR: {str(e)}")
    
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/tours", response_model=List[TourBase])
async def get_tours(
    tour_type: Optional[str] = Query(None, description="Filter nach Tour-Typ (Bike, Hike, Inline, etc.)"),
    date_from: Optional[str] = Query(None, description="Startdatum (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Enddatum (YYYY-MM-DD)"),
    ebike_only: Optional[bool] = Query(None, description="Nur E-Bike Touren anzeigen"),
    min_distance: Optional[float] = Query(None, description="Minimale Distanz in km"),
    max_distance: Optional[float] = Query(None, description="Maximale Distanz in km"),
    min_elevation: Optional[float] = Query(None, description="Minimaler Höhenunterschied in m"),
    limit: int = Query(100, description="Maximale Anzahl Ergebnisse"),
    offset: int = Query(0, description="Anzahl zu überspringende Ergebnisse")
):
    """Holt alle Touren mit optionalen Filtern"""
    logger.info(f"DEBUG: get_tours called with limit={limit}")
    
    query = """
        SELECT id, name, type, date, distance_km, duration_s, speed_kmh, 
               elevation_up, elevation_down, start_lat, start_lon, ebike, komootid, komoothref, track_geojson
        FROM tours 
        WHERE 1=1
    """
    params = {}
    
    # Filter anwenden
    if tour_type and tour_type.strip():
        query += " AND LOWER(type) = LOWER(:tour_type)"
        params["tour_type"] = tour_type
    
    if date_from and date_from.strip():
        try:
            # Validate date format
            datetime.fromisoformat(date_from)
            query += " AND date >= :date_from"
            params["date_from"] = date_from
        except ValueError:
            pass  # Ignore invalid date format
    
    if date_to and date_to.strip():
        try:
            # Validate date format
            datetime.fromisoformat(date_to)
            query += " AND date <= :date_to"
            params["date_to"] = date_to
        except ValueError:
            pass  # Ignore invalid date format
    
    if ebike_only is not None:
        query += " AND ebike = :ebike_only"
        params["ebike_only"] = ebike_only
    
    if min_distance is not None:
        query += " AND distance_km >= :min_distance"
        params["min_distance"] = min_distance
    
    if max_distance is not None:
        query += " AND distance_km <= :max_distance"
        params["max_distance"] = max_distance
    
    if min_elevation is not None:
        query += " AND elevation_up >= :min_elevation"
        params["min_elevation"] = min_elevation
    
    # Sortierung und Limit
    query += " ORDER BY date DESC LIMIT :limit OFFSET :offset"
    params["limit"] = limit
    params["offset"] = offset
    
    try:
        with engine.connect() as connection:
            result = connection.execute(text(query), params)
            tours = []
            for row in result:
                tours.append(TourBase(
                    id=row[0],
                    name=row[1],
                    type=row[2],
                    date=row[3],
                    distance_km=row[4],
                    duration_s=row[5],
                    speed_kmh=row[6],
                    elevation_up=row[7],
                    elevation_down=row[8],
                    start_lat=row[9],
                    start_lon=row[10],
                    ebike=bool(row[11]),
                    komootid=row[12],
                    komoothref=row[13],
                    track_geojson=row[14]
                ))
            return tours
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Datenbankfehler: {str(e)}")

@app.get("/api/tours/summary", response_model=TourSummary)
async def get_tour_summary(
    tour_type: Optional[str] = Query(None, description="Filter nach Tour-Typ"),
    date_from: Optional[str] = Query(None, description="Startdatum (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Enddatum (YYYY-MM-DD)"),
    ebike_only: Optional[bool] = Query(None, description="Nur E-Bike Touren anzeigen")
):
    """Liefert eine Zusammenfassung aller Touren"""
    
    try:
        with engine.connect() as connection:
            # Build query with filters
            base_query = "SELECT * FROM tours WHERE 1=1"
            params = {}
            
            # Apply filters (same logic as get_tours)
            if tour_type and tour_type.strip():
                base_query += " AND LOWER(type) = LOWER(:tour_type)"
                params["tour_type"] = tour_type
            
            if date_from and date_from.strip():
                try:
                    # Validate date format
                    datetime.fromisoformat(date_from)
                    base_query += " AND date >= :date_from"
                    params["date_from"] = date_from
                except ValueError:
                    pass  # Ignore invalid date format
            
            if date_to and date_to.strip():
                try:
                    # Validate date format
                    datetime.fromisoformat(date_to)
                    base_query += " AND date <= :date_to"
                    params["date_to"] = date_to
                except ValueError:
                    pass  # Ignore invalid date format
            
            if ebike_only is not None:
                base_query += " AND ebike = :ebike_only"
                params["ebike_only"] = ebike_only
            
            # Gesamtstatistiken
            stats_query = f"""
                SELECT 
                    COUNT(*) as total_tours,
                    COALESCE(SUM(distance_km), 0) as total_distance,
                    COALESCE(SUM(duration_s), 0) as total_duration,
                    COALESCE(SUM(elevation_up), 0) as total_elevation_up
                FROM ({base_query}) as filtered_tours
            """
            stats_result = connection.execute(text(stats_query), params)
            stats = stats_result.fetchone()
            
            # Tour-Typen Verteilung
            types_query = f"""
                SELECT type, COUNT(*) as count
                FROM ({base_query}) as filtered_tours
                GROUP BY type
                ORDER BY count DESC
            """
            types_result = connection.execute(text(types_query), params)
            types_dict = {row[0]: row[1] for row in types_result}
            
            return TourSummary(
                total_tours=stats[0],
                total_distance=round(stats[1], 2),
                total_duration=stats[2],
                total_elevation_up=round(stats[3], 2),
                types=types_dict
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Zusammenfassung: {str(e)}")

@app.get("/api/tours/types")
async def get_tour_types():
    """Liefert alle verfügbaren Tour-Typen"""
    
    try:
        with engine.connect() as connection:
            query = "SELECT DISTINCT type FROM tours WHERE type IS NOT NULL ORDER BY type"
            result = connection.execute(text(query))
            types = [row[0] for row in result]
            return {"types": types}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Tour-Typen: {str(e)}")

@app.get("/api/tours/geojson")
async def get_tours_geojson(
    tour_type: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None, description="Startdatum (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Enddatum (YYYY-MM-DD)"),
    limit: int = Query(999999, description="Maximale Anzahl Touren für Performance")
):
    """Liefert Touren als GeoJSON FeatureCollection für Kartendarstellung"""
    
    query = """
        SELECT id, name, type, date, distance_km, start_lat, start_lon, track_geojson, ebike
        FROM tours 
        WHERE 1=1
    """
    params = {}
    
    if tour_type and tour_type.strip():
        query += " AND LOWER(type) = LOWER(:tour_type)"
        params["tour_type"] = tour_type
    
    if date_from and date_from.strip():
        try:
            # Validate date format
            datetime.fromisoformat(date_from)
            query += " AND date >= :date_from"
            params["date_from"] = date_from
        except ValueError:
            pass  # Ignore invalid date format
    
    if date_to and date_to.strip():
        try:
            # Validate date format
            datetime.fromisoformat(date_to)
            query += " AND date <= :date_to"
            params["date_to"] = date_to
        except ValueError:
            pass  # Ignore invalid date format
    
    query += " ORDER BY date DESC LIMIT :limit"
    params["limit"] = limit
    
    try:
        with engine.connect() as connection:
            result = connection.execute(text(query), params)
            
            features = []
            for row in result:
                try:
                    # Track GeoJSON parsen
                    track_geojson = json.loads(row[7])
                    
                    feature = {
                        "type": "Feature",
                        "geometry": track_geojson,
                        "properties": {
                            "id": row[0],
                            "name": row[1],
                            "type": row[2],
                            "date": row[3],
                            "distance_km": row[4],
                            "start_lat": row[5],
                            "start_lon": row[6],
                            "ebike": bool(row[8])
                        }
                    }
                    features.append(feature)
                except json.JSONDecodeError:
                    # Überspringe Touren mit ungültigen GeoJSON Daten
                    continue
            
            geojson = {
                "type": "FeatureCollection",
                "features": features
            }
            
            return geojson
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Generieren des GeoJSON: {str(e)}")

@app.get("/api/tours/{tour_id}", response_model=TourDetail)
async def get_tour_detail(tour_id: int):
    """Holt eine spezifische Tour mit vollständigen Details inkl. Track-Daten"""
    
    query = """
        SELECT id, name, type, date, distance_km, duration_s, speed_kmh, 
               elevation_up, elevation_down, start_lat, start_lon, ebike, 
               komootid, komoothref, track_geojson
        FROM tours 
        WHERE id = :tour_id
    """
    
    try:
        with engine.connect() as connection:
            result = connection.execute(text(query), {"tour_id": tour_id})
            row = result.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Tour nicht gefunden")
            
            # Parse track_geojson if it exists
            track_geojson = None
            if row[14]:  # track_geojson is not None
                try:
                    track_geojson = json.loads(row[14])
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse track_geojson for tour {tour_id}: {e}")
            
            return TourDetail(
                id=row[0],
                name=row[1],
                type=row[2],
                date=row[3],
                distance_km=row[4],
                duration_s=row[5],
                speed_kmh=row[6],
                elevation_up=row[7],
                elevation_down=row[8],
                start_lat=row[9],
                start_lon=row[10],
                ebike=bool(row[11]),
                komootid=row[12],
                komoothref=row[13],
                track_geojson=track_geojson
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_tour_detail for tour {tour_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Datenbankfehler: {str(e)}")

@app.post("/api/tours/nearby", response_model=List[TourBase])
async def get_nearby_tours(location: LocationFilter):
    """Findet Touren in der Nähe eines bestimmten Standorts"""
    
    # Erst alle Touren holen
    query = """
        SELECT id, name, type, date, distance_km, duration_s, speed_kmh, 
               elevation_up, elevation_down, start_lat, start_lon, ebike, 
               komootid, komoothref, track_geojson
        FROM tours
    """
    
    try:
        with engine.connect() as connection:
            result = connection.execute(text(query))
            nearby_tours = []
            
            for row in result:
                # Prüfe ob Tour durch den Radius führt
                if point_in_radius(row[14], location.latitude, location.longitude, location.radius_km):
                    nearby_tours.append(TourBase(
                        id=row[0],
                        name=row[1],
                        type=row[2],
                        date=row[3],
                        distance_km=row[4],
                        duration_s=row[5],
                        speed_kmh=row[6],
                        elevation_up=row[7],
                        elevation_down=row[8],
                        start_lat=row[9],
                        start_lon=row[10],
                        ebike=bool(row[11]),
                        komootid=row[12],
                        komoothref=row[13]
                    ))
            
            return nearby_tours
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler bei der Standortsuche: {str(e)}")

# Test endpoint for debugging track_geojson
@app.get("/api/debug/tours/{tour_id}")
async def debug_tour(tour_id: int):
    """Debug endpoint to check track_geojson data for a specific tour"""
    query = "SELECT id, name, track_geojson FROM tours WHERE id = :id"
    try:
        with engine.connect() as connection:
            result = connection.execute(text(query), {"id": tour_id})
            row = result.fetchone()
            if row:
                track_data = row[2]
                return {
                    "id": row[0],
                    "name": row[1],
                    "track_geojson_type": str(type(track_data)),
                    "track_geojson_is_none": track_data is None,
                    "track_geojson_length": len(track_data) if track_data else 0,
                    "track_geojson_first_100": track_data[:100] if track_data else None,
                    "raw_track_data": track_data
                }
            else:
                return {"error": "Tour not found"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Add debug logging
    print(f"Login attempt for user: {form_data.username}")
    
    # Get user from database directly to check password
    import sqlite3
    import os
    from passlib.context import CryptContext
    
    # Setup password context
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Get database path
    if os.getenv("DOCKER_ENV") == "true":
        db_path = "/app/data/tourmanager.db"
    else:
        db_path = "./tourmanager.db"
    db_path = os.getenv("DATABASE_PATH", db_path)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if user exists and get status
    cursor.execute("SELECT username, hashed_password, status FROM users WHERE username = ?", (form_data.username,))
    user_data = cursor.fetchone()
    conn.close()
    
    if not user_data:
        print(f"User {form_data.username} not found")
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    username, stored_hash, user_status = user_data
    
    # Print debug info
    print(f"Found user {username} with hash: {stored_hash} and status: {user_status}")
    
    # Check if user is pending approval
    if user_status == UserStatus.PENDING.value:
        print(f"User {form_data.username} is pending approval")
        raise HTTPException(
            status_code=403,
            detail="Your account is pending approval by an administrator",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not pwd_context.verify(form_data.password, stored_hash):
        print(f"Password verification failed for {username}")
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    print(f"Password verification successful for {username}")
    
    # Get user from ORM
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        print(f"ORM authentication failed for {username}")
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Update last login time
    user.last_login = datetime.utcnow()
    db.commit()
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: UserModel = Depends(get_current_active_user)):
    return current_user

@app.post("/api/auth/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if username already exists
    if get_user(db, username=user.username):
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    # Check if email already exists
    if get_user_by_email(db, email=user.email):
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Create new user
    user = create_user(db=db, user=user)
    return user

@app.get("/api/users", response_model=List[UserResponse])
async def list_users(
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all users (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view user list"
        )
    return db.query(UserModel).all()

@app.patch("/api/users/{username}/status")
async def update_user_status_endpoint(
    username: str,
    status_update: UserStatusUpdate,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a user's status (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update user status"
        )
    
    if username == current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update your own status"
        )
    
    user = db.query(UserModel).filter(UserModel.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Log received status
        logger.info(f"Received status update for user {username}: {status_update.status}")
        
        # Get valid statuses and log them
        valid_statuses = [status.value for status in UserStatus]
        logger.info(f"Valid status values: {valid_statuses}")
        
        if status_update.status not in valid_statuses:
            logger.error(f"Invalid status value received: {status_update.status}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid status value '{status_update.status}'. Must be one of: {', '.join(valid_statuses)}"
            )
        
        # Set the status directly since we validated it's a valid value
        user.status = UserStatus(status_update.status)
        db.commit()
        db.refresh(user)
        return user.to_dict()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status value. Must be one of: {', '.join([s.value for s in UserStatus])}"
        )

@app.get("/api/users/pending", response_model=List[UserResponse])
async def list_pending_users(
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all pending users (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view pending users"
        )
    return db.query(UserModel).filter(UserModel.status == UserStatus.PENDING).all()

@app.delete("/api/users/{username}")
async def delete_user(
    username: str,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a user (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete users"
        )
    
    if username == current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    if username == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the admin account"
        )
    
    user = db.query(UserModel).filter(UserModel.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": f"User {username} has been deleted"}

@app.post("/api/auth/change-password")
async def change_password_endpoint(
    password_change: PasswordChangeRequest,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        # Import directly here to avoid any circular import issues
        from passlib.context import CryptContext
        import sqlite3
        import os
        
        # Setup password context
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Check current password
        if not pwd_context.verify(password_change.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Generate new hash
        new_hash = pwd_context.hash(password_change.new_password)
        
        # Get database path from environment
        if os.getenv("DOCKER_ENV") == "true":
            db_path = "/app/data/tourmanager.db"
        else:
            db_path = "./tourmanager.db"
        db_path = os.getenv("DATABASE_PATH", db_path)
        
        # Direct database access
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Update the password
        cursor.execute("UPDATE users SET hashed_password = ? WHERE username = ?", 
                     (new_hash, current_user.username))
        rows_updated = cursor.rowcount
        conn.commit()
        
        # Verify it worked
        cursor.execute("SELECT hashed_password FROM users WHERE username = ?", (current_user.username,))
        stored_hash = cursor.fetchone()[0]
        conn.close()
        
        # Also update in memory
        current_user.hashed_password = new_hash
        
        # Log results
        print(f"Updated password for {current_user.username}. Rows updated: {rows_updated}")
        print(f"New hash matches stored hash: {stored_hash == new_hash}")
        
        return {"message": "Password updated successfully"}
    except Exception as e:
        import traceback
        traceback_text = traceback.format_exc()
        print(f"Error changing password: {str(e)}")
        print(traceback_text)
        with open("/app/data/error_log.txt", "a") as f:
            f.write(f"ERROR: {str(e)}\n")
            f.write(traceback_text)
            f.write("\n" + "-"*50 + "\n")
        raise

# Test endpoint to check users
@app.get("/api/test/users")
async def test_users(db: Session = Depends(get_db)):
    import logging
    logger = logging.getLogger("main")
    
    try:
        users = db.query(UserModel).all()
        result = []
        for user in users:
            result.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "hashed_password": user.hashed_password[:10] + "...",
            })
        logger.error(f"TOTAL USERS: {len(result)}")
        logger.error(f"USERS: {result}")
        return result
    except Exception as e:
        logger.error(f"ERROR: {str(e)}")
        return {"error": str(e)}

# Protect your existing endpoints with authentication
# Example:
# @app.get("/protected-route")
# async def protected_route(current_user: User = Depends(get_current_active_user)):
#     return {"message": "This is a protected route"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
