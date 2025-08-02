from fastapi import FastAPI, HTTPException, Query, Depends, Request, status, File, UploadFile, Form
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
import sys
import logging
import tempfile
import traceback
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

from routers.users import router as users_router, create_user
from auth import get_user_by_email

# Import database fix utility
from utils.db_fixes import fix_user_role_case_sensitivity
from utils.logger import get_logger

# Configure logger for main module
main_logger = get_logger(__name__)

# Import database fix utility
from utils.db_fixes import fix_user_role_case_sensitivity
from utils.logger import get_logger

# Configure logger for main module
main_logger = get_logger(__name__)
async def startup_event():
    create_initial_admin()
    
    # Fix user role case sensitivity issues
    try:
        with SessionLocal() as db:
            updated = fix_user_role_case_sensitivity(db)
            if updated > 0:
                main_logger.info(f"Fixed {updated} user role records with case sensitivity issues")
    except Exception as e:
        main_logger.error(f"Failed to fix user role case sensitivity: {str(e)}", exc_info=True)

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
    description="API for managing GPX tours with FastAPI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Debug middleware to log all requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Get client information
    client_host = request.client.host if request.client else "unknown"
    
    # Log the request
    logger.info(f"Request {request.method} {request.url.path} from {client_host}")
    
    # Log headers in debug mode
    if logger.level <= logging.DEBUG:
        for name, value in request.headers.items():
            # Don't log sensitive headers like Authorization
            if name.lower() not in ['authorization', 'cookie']:
                logger.debug(f"Header {name}: {value}")
    
    # Process the request and log the response
    try:
        response = await call_next(request)
        logger.info(f"Response {request.method} {request.url.path}: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Request {request.method} {request.url.path} failed: {str(e)}")
        raise

# Include the users router
app.include_router(users_router, prefix="/api", tags=["users"])

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicitly specify methods
    allow_headers=["*"],  # Allow all headers for simplicity
    expose_headers=["Content-Disposition", "Content-Type"]  # Expose headers for downloads
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
        if not tour_geojson:
            return False
            
        # Handle case where tour_geojson is already a dictionary
        if isinstance(tour_geojson, dict):
            geojson_data = tour_geojson
        else:
            geojson_data = json.loads(tour_geojson)
            
        coordinates = geojson_data.get('coordinates', [])
        
        # Prüfe alle Punkte der Tour
        for coord in coordinates:
            # Handle different coordinate formats (some might have elevation as third value)
            if len(coord) >= 2:
                lon, lat = coord[0], coord[1]
                distance = calculate_distance(center_lat, center_lon, lat, lon)
                if distance <= radius_km:
                    return True
        return False
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as e:
        logger.error(f"Error in point_in_radius: {str(e)}")
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
    from utils.logger import get_logger
    logger = get_logger(__name__)
    
    logger.info(f"Login attempt for user: {form_data.username}")
    
    # Get user from ORM
    user = get_user(db, username=form_data.username)
    
    # Check if user exists
    if not user:
        logger.warning(f"Login failed - User not found: {form_data.username}")
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    from auth import verify_password
    if not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Login failed - Incorrect password for user: {form_data.username}")
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if email is verified (skip for admin)
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    
    if not user.email_verified and user.username != admin_username:
        logger.warning(f"Login blocked - Email not verified for user: {form_data.username}")
        raise HTTPException(
            status_code=403,
            detail="Please verify your email before logging in. Check your inbox for a verification link.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is pending approval
    if user.status == UserStatus.PENDING:
        logger.warning(f"Login blocked - User pending admin approval: {form_data.username}")
        raise HTTPException(
            status_code=403,
            detail="Your account is awaiting approval from an administrator. You will be notified when approved.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is disabled
    if user.status == UserStatus.DISABLED:
        logger.warning(f"Login blocked - Disabled user: {form_data.username}")
        raise HTTPException(
            status_code=403,
            detail="Your account has been disabled. Please contact an administrator.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login time
    user.last_login = datetime.utcnow()
    db.commit()
    
    logger.info(f"Login successful for user: {form_data.username}")
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: UserModel = Depends(get_current_active_user)):
    return current_user

@app.post("/api/auth/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    from utils.logger import get_logger
    from utils.email import send_verification_email
    import secrets
    
    logger = get_logger(__name__)
    logger.info(f"Registration attempt for username: {user.username}, email: {user.email}")
    
    # Check if username already exists
    if get_user(db, username=user.username):
        logger.warning(f"Registration failed - Username already exists: {user.username}")
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    # Check if email already exists
    if get_user_by_email(db, email=user.email):
        logger.warning(f"Registration failed - Email already exists: {user.email}")
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Generate verification token
    verification_token = secrets.token_urlsafe(32)
    
    # Create user with PENDING status and verification token
    hashed_password = get_password_hash(user.password)
    db_user = UserModel(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=UserRole.USER,
        status=UserStatus.PENDING,
        email_verified=False,
        verification_token=verification_token
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info(f"User created: {db_user.username}, status: PENDING, awaiting email verification and admin approval")
    
    # Send verification email
    try:
        logger.info(f"Initiating verification email for new user: {db_user.username} ({db_user.email})")
        email_result = await send_verification_email(db_user.email, verification_token)
        
        # Log the detailed result from the email function
        if email_result and email_result.get("success"):
            logger.info(f"Verification email successfully sent to {db_user.email}")
            logger.info(f"Email details: took {email_result.get('duration_seconds', 'unknown')} seconds")
        else:
            logger.warning(f"Verification email not sent successfully to {db_user.email}")
            if email_result:
                logger.warning(f"Email error: {email_result.get('error', 'unknown error')}")
    except Exception as e:
        logger.error(f"Failed to send verification email: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        # We don't want to fail registration if email sending fails
    
    return db_user

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
    
    try:
        # Use a safer query approach with error handling
        users = db.query(UserModel).all()
        main_logger.info(f"Successfully fetched {len(users)} users")
        return users
    except Exception as e:
        main_logger.error(f"Error fetching users: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while fetching users: {str(e)}"
        )

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

# --- GPX Upload Functionality ---
@app.post("/api/tours/upload")
async def upload_gpx_file(
    file: UploadFile = File(...),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload a GPX or KML file to add a new tour
    """
    # Any authenticated user can upload files
    # Authorization is handled by get_current_active_user dependency
    
    # Import necessary modules to ensure they're available in this scope
    import os
    import tempfile
    
    # Check if the file is a GPX or KML file
    file_ext = os.path.splitext(file.filename.lower())[1]
    logger.debug(f"Detected file extension: '{file_ext}' for file: {file.filename}")
    
    if file_ext not in ['.gpx', '.kml']:
        logger.warning(f"Rejected file with unsupported extension: {file_ext}, filename: {file.filename}")
        raise HTTPException(
            status_code=400,
            detail="Only GPX or KML files are accepted"
        )
    
    try:
        # Create a temporary file to store the uploaded file with correct extension
        file_ext = os.path.splitext(file.filename.lower())[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            contents = await file.read()
            temp_file.write(contents)
            temp_file_path = temp_file.name
        
        # If it's a KML file, convert it to GPX
        if file_ext == '.kml':
            try:
                logger.info(f"Converting KML file to GPX: {file.filename}")
                
                # Check the file content before conversion
                with open(temp_file_path, 'rb') as check_file:
                    file_start = check_file.read(100)
                    logger.debug(f"KML file content start: {file_start}")
                
                from utils.kml_converter import kml_to_gpx
                gpx_path = kml_to_gpx(temp_file_path)
                
                if not gpx_path:
                    logger.error(f"KML conversion failed for file: {file.filename}")
                    return {"status": "error", "message": "Failed to convert KML file to GPX format. The KML file may be invalid or corrupted."}
                
                logger.info(f"KML file successfully converted to GPX: {file.filename}")
                
                # Clean up the original KML file
                os.unlink(temp_file_path)
                temp_file_path = gpx_path
            except Exception as e:
                logger.error(f"Exception during KML conversion: {str(e)}")
                error_trace = traceback.format_exc()
                logger.error(f"Traceback: {error_trace}")
                return {"status": "error", "message": f"Error converting KML file: {str(e)}"}
        
        # Import the GPX processing function from our script
        import sys as _sys  # Renamed to avoid conflicts
        import importlib.util
        
        # Try several possible script paths
        possible_script_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "../scripts"),  # Development environment
            "/app/scripts",  # Docker container standard path
            "/app",  # Root of the Docker container 
            os.path.abspath("scripts"),  # Relative to current directory
            os.path.abspath("../scripts"),  # One level up
            ".",  # Current directory
        ]
        
        # Log debugging information
        logger.error(f"Current working directory: {os.getcwd()}")
        logger.error(f"Searching for import_gpx.py in these directories: {possible_script_paths}")
        
        # Search for the script in all possible locations
        import_gpx_path = None
        for path in possible_script_paths:
            script_path = os.path.join(path, "import_gpx.py")
            if os.path.exists(script_path):
                import_gpx_path = script_path
                logger.error(f"Found script at: {import_gpx_path}")
                break
            else:
                if os.path.exists(path):
                    logger.error(f"Directory exists but script not found. Files in {path}: {os.listdir(path)}")
                else:
                    logger.error(f"Directory does not exist: {path}")
        
        if not import_gpx_path:
            logger.error("import_gpx.py not found in any of the expected locations")
            raise FileNotFoundError("GPX import script not found in any of the expected locations")
            
        # Add all possible paths to sys.path
        for path in possible_script_paths:
            if path not in sys.path and os.path.exists(path):
                sys.path.append(path)
            
        # All potential directories were already added to sys.path in the code above
        
        # Import module using spec
        spec = importlib.util.spec_from_file_location("import_gpx", import_gpx_path)
        import_gpx = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(import_gpx)
        
        # Access the function
        parse_and_store_gpx = import_gpx.parse_and_store_gpx
        
        # Process the GPX file
        result = parse_and_store_gpx(temp_file_path)
        
        # Clean up the temporary file
        os.unlink(temp_file_path)
        
        # Return appropriate response based on the result
        if result == "imported":
            return {"status": "success", "message": "Tour imported successfully"}
        elif result == "exists":
            return {"status": "warning", "message": "Tour already exists (same Komoot ID)"}
        elif result == "skipped":
            return {"status": "warning", "message": "Tour skipped - no track points found"}
        else:
            return {"status": "error", "message": f"Unknown error: {result}"}
            
    except Exception as e:
        logger.error(f"Error processing GPX file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing GPX file: {str(e)}"
        )

# Batch upload endpoint for multiple files
@app.post("/api/tours/upload/batch")
async def upload_multiple_gpx_files(
    files: list[UploadFile] = File(...),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload multiple GPX and KML files at once
    """
    # Any authenticated user can upload files
    # Authorization is handled by get_current_active_user dependency
    
    # Import necessary modules to ensure they're available in this scope
    import os
    import tempfile
    
    results = []
    
    for file in files:
        # Check if the file is a GPX or KML file
        file_ext = os.path.splitext(file.filename.lower())[1]
        logger.debug(f"Batch upload - Detected file extension: '{file_ext}' for file: {file.filename}")
        
        if file_ext not in ['.gpx', '.kml']:
            logger.warning(f"Batch upload - Rejected file with unsupported extension: {file_ext}, filename: {file.filename}")
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": "Only GPX and KML files are accepted"
            })
            continue
        
        try:
            # Create a temporary file to store the uploaded file with correct extension
            file_ext = os.path.splitext(file.filename.lower())[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                contents = await file.read()
                temp_file.write(contents)
                temp_file_path = temp_file.name
            
            # If it's a KML file, convert it to GPX
            if file_ext == '.kml':
                try:
                    logger.info(f"Converting KML file to GPX: {file.filename}")
                    
                    # Check the file content before conversion
                    with open(temp_file_path, 'rb') as check_file:
                        file_start = check_file.read(100)
                        logger.debug(f"KML file content start: {file_start}")
                    
                    from utils.kml_converter import kml_to_gpx
                    gpx_path = kml_to_gpx(temp_file_path)
                    
                    if not gpx_path:
                        logger.error(f"KML conversion failed for file: {file.filename}")
                        results.append({
                            "filename": file.filename,
                            "status": "error",
                            "message": "Failed to convert KML file to GPX format. The KML file may be invalid or corrupted."
                        })
                        # Clean up the original KML file
                        os.unlink(temp_file_path)
                        continue
                    
                    logger.info(f"KML file successfully converted to GPX: {file.filename}")
                    
                    # Clean up the original KML file
                    os.unlink(temp_file_path)
                    temp_file_path = gpx_path
                except Exception as e:
                    logger.error(f"Exception during KML conversion: {str(e)}")
                    error_trace = traceback.format_exc()
                    logger.error(f"Traceback: {error_trace}")
                    results.append({
                        "filename": file.filename,
                        "status": "error",
                        "message": f"Error converting KML file: {str(e)}"
                    })
                    
                    # Clean up the original KML file if it still exists
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                    continue
            
            # Import the GPX processing function from our script
            import sys
            import os
            import importlib.util
            
            # Try several possible script paths
            possible_script_paths = [
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "../scripts"),  # Development environment
                "/app/scripts",  # Docker container standard path
                os.path.abspath("scripts"),  # Relative to current directory
                os.path.abspath("../scripts"),  # One level up
                os.path.abspath("./"),  # base level
            ]
            
            # Log debugging information
            logger.error(f"Batch upload - Current working directory: {os.getcwd()}")
            logger.error(f"Batch upload - Searching for import_gpx.py in these directories: {possible_script_paths}")
            
            # Search for the script in all possible locations
            import_gpx_path = None
            for path in possible_script_paths:
                script_path = os.path.join(path, "import_gpx.py")
                if os.path.exists(script_path):
                    import_gpx_path = script_path
                    logger.error(f"Batch upload - Found script at: {import_gpx_path}")
                    break
                else:
                    if os.path.exists(path):
                        logger.error(f"Batch upload - Directory exists but script not found. Files in {path}: {os.listdir(path)}")
                    else:
                        logger.error(f"Batch upload - Directory does not exist: {path}")
            
            if not import_gpx_path:
                logger.error("Batch upload - import_gpx.py not found in any of the expected locations")
                raise FileNotFoundError("Batch upload - GPX import script not found in any of the expected locations")
                
            # Add all possible paths to sys.path
            for path in possible_script_paths:
                if path not in sys.path and os.path.exists(path):
                    sys.path.append(path)
            
            # Import module using spec
            spec = importlib.util.spec_from_file_location("import_gpx", import_gpx_path)
            import_gpx = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(import_gpx)
            
            # Access the function
            parse_and_store_gpx = import_gpx.parse_and_store_gpx
            
            # Process the GPX file
            result = parse_and_store_gpx(temp_file_path)
            
            # Clean up the temporary file
            os.unlink(temp_file_path)
            
            # Add result to the results list
            if result == "imported":
                results.append({
                    "filename": file.filename,
                    "status": "success",
                    "message": "Tour imported successfully"
                })
            elif result == "exists":
                results.append({
                    "filename": file.filename,
                    "status": "warning",
                    "message": "Tour already exists (same Komoot ID)"
                })
            elif result == "skipped":
                results.append({
                    "filename": file.filename,
                    "status": "warning",
                    "message": "Tour skipped - no track points found"
                })
            else:
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": f"Unknown error: {result}"
                })
                
        except Exception as e:
            logger.error(f"Error processing GPX file {file.filename}: {str(e)}")
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": f"Error processing file: {str(e)}"
            })
    
    return {"results": results}

# Endpoint moved to users.py router

@app.post("/api/admin/approve-user/{username}", response_model=UserResponse)
async def approve_user(
    username: str,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Approve a pending user (admin only)"""
    from utils.logger import get_logger
    from utils.email import send_account_approved_email
    
    logger = get_logger(__name__)
    
    # Check if the current user is an admin
    if current_user.role != UserRole.ADMIN:
        logger.warning(f"Non-admin user {current_user.username} attempted to approve user {username}")
        raise HTTPException(
            status_code=403,
            detail="Not authorized to approve users"
        )
    
    # Find the pending user
    user = get_user(db, username)
    if not user:
        logger.warning(f"Attempted to approve non-existent user: {username}")
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    # Check if the user is pending
    if user.status != UserStatus.PENDING:
        logger.warning(f"Attempted to approve user {username} with status {user.status}")
        raise HTTPException(
            status_code=400,
            detail=f"User is not pending approval (current status: {user.status.value})"
        )
    
    # Check if email is verified (skip for admin user)
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    
    if not user.email_verified and user.username != admin_username:
        logger.warning(f"Attempted to approve user {username} with unverified email")
        raise HTTPException(
            status_code=400,
            detail="User's email is not verified yet"
        )
    
    # Update user status to ACTIVE
    user.status = UserStatus.ACTIVE
    db.commit()
    db.refresh(user)
    
    logger.info(f"Admin {current_user.username} approved user {username}")
    
    # Notify the user that their account was approved
    try:
        await send_account_approved_email(user.email)
        logger.info(f"Account approval notification sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send approval notification to {user.email}: {str(e)}")
    
    return user

@app.get("/api/admin/pending-users", response_model=List[UserResponse])
async def list_pending_users(
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all pending users awaiting approval (admin only)"""
    from utils.logger import get_logger
    
    logger = get_logger(__name__)
    
    # Check if the current user is an admin
    if current_user.role != UserRole.ADMIN:
        logger.warning(f"Non-admin user {current_user.username} attempted to access pending users")
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view pending users"
        )
    
    # Query pending users
    pending_users = db.query(UserModel).filter(UserModel.status == UserStatus.PENDING).all()
    logger.info(f"Admin {current_user.username} viewed list of {len(pending_users)} pending users")
    
    return pending_users

# Protect your existing endpoints with authentication
# Example:
# @app.get("/protected-route")
# async def protected_route(current_user: User = Depends(get_current_active_user)):
#     return {"message": "This is a protected route"}

@app.post("/api/debug/upload-test")
async def test_file_upload(file: UploadFile = File(...)):
    """
    Debug endpoint to test single file upload functionality
    """
    logger.info(f"Debug upload test received file: {file.filename}")
    
    try:
        # Extract file extension
        file_ext = os.path.splitext(file.filename.lower())[1]
        logger.info(f"File extension: {file_ext}")
        
        # Get the file content
        content = await file.read()
        logger.info(f"File size: {len(content)} bytes")
        logger.info(f"Content type: {file.content_type}")
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
            
        logger.info(f"Wrote file to: {temp_file_path}")
        
        # Clean up the temporary file
        os.unlink(temp_file_path)
        
        return {
            "status": "success",
            "filename": file.filename,
            "size": len(content),
            "extension": file_ext,
            "content_type": file.content_type
        }
        
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Debug upload error: {str(e)}")
        logger.error(f"Traceback: {error_trace}")
        return {
            "status": "error",
            "filename": file.filename,
            "error": str(e)
        }

@app.post("/api/debug/upload-batch-test")
async def test_batch_file_upload(files: list[UploadFile] = File(...)):
    """
    Debug endpoint to test batch file upload functionality
    """
    logger.info(f"Debug batch upload test received {len(files)} files")
    
    results = []
    
    try:
        for i, file in enumerate(files):
            logger.info(f"Processing file {i+1}/{len(files)}: {file.filename}")
            
            # Extract file extension
            file_ext = os.path.splitext(file.filename.lower())[1]
            
            # Get the file content
            content = await file.read()
            
            results.append({
                "status": "success",
                "filename": file.filename,
                "size": len(content),
                "extension": file_ext,
                "content_type": file.content_type
            })
            
        return {"results": results}
        
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Debug batch upload error: {str(e)}")
        logger.error(f"Traceback: {error_trace}")
        return {
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
