from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import create_engine, text, func
from models.users import User as UserModel
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from pydantic import BaseModel
import json
import math
import os
import logging
from database import SessionLocal, engine, get_db  # Import database utilities
from auth import (
    create_access_token,
    get_current_active_user,
    authenticate_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_initial_admin,
    UserResponse,
    UserCreate,
    get_user,
    get_user_by_email,
    create_user
)
from models.users import UserRole, UserStatus

# Initialize the database and tables
from database import Base
from models.users import User
from models.activity import UserActivity

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize admin user
db = SessionLocal()
try:
    create_initial_admin(db)
finally:
    db.close()

class Token(BaseModel):
    access_token: str
    token_type: str

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
DATABASE_FILE = os.getenv('DATABASE_PATH', os.path.join(os.path.dirname(__file__), 'scripts', 'touren.db'))
print(f"DATABASE_FILE: {DATABASE_FILE}")
engine = create_engine(f'sqlite:///{DATABASE_FILE}')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
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
async def update_user_status(
    username: str,
    status: UserStatus,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a user's status (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to update user status"
        )
    
    user = db.query(UserModel).filter(UserModel.username == username).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    user.status = status
    db.commit()
    return {"message": f"User status updated to {status.value}"}

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

# Protect your existing endpoints with authentication
# Example:
# @app.get("/protected-route")
# async def protected_route(current_user: User = Depends(get_current_active_user)):
#     return {"message": "This is a protected route"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
