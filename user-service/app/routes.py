from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from . import models, schemas, config
from .database import get_db
from .utils.logging_config import setup_logging
from passlib.context import CryptContext

logger = setup_logging("user-service")

router = APIRouter()
# Configure bcrypt with truncate_error=False to handle the backend initialization issue
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__default_rounds=12,
    bcrypt__truncate_error=False
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt

def get_password_hash(password):
    # Truncate password to 72 bytes (bcrypt limit) to avoid errors
    if isinstance(password, str):
        password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(current_user: models.User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@router.post("/register", response_model=schemas.APIResponse[schemas.UserResponse], status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    logger.info(f"Attempting to register user: {user.email}")
    
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        logger.warning(f"Email already registered: {user.email}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        name=user.name,
        email=user.email, 
        hashed_password=hashed_password, 
        push_token=user.push_token
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create notification preferences
    email_pref = models.NotificationPreference(
        user_id=db_user.id,
        channel="email",
        enabled=user.preferences.email,
        preferences={}
    )
    push_pref = models.NotificationPreference(
        user_id=db_user.id,
        channel="push",
        enabled=user.preferences.push,
        preferences={}
    )
    db.add(email_pref)
    db.add(push_pref)
    db.commit()
    
    logger.info(f"User registered successfully: {user.email}")
    return schemas.APIResponse(data=db_user, message="User registered successfully")

@router.post("/login", response_model=schemas.Token, status_code=status.HTTP_200_OK)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login to get access token"""
    logger.info(f"Login attempt for user: {form_data.username}")
    
    db_user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        logger.warning(f"Failed login attempt for: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not db_user.is_active:
        logger.warning(f"Inactive user attempted login: {form_data.username}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.email, "user_id": str(db_user.id)}, expires_delta=access_token_expires
    )
    
    logger.info(f"Login successful for user: {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.APIResponse[schemas.UserResponse])
def get_current_user_info(current_user: models.User = Depends(get_current_active_user)):
    """Get current user information"""
    return schemas.APIResponse(data=current_user, message="User retrieved successfully")

@router.get("/{user_id}", response_model=schemas.APIResponse[schemas.UserResponse])
def get_user(user_id: str, db: Session = Depends(get_db)):
    """Get user by ID (UUID)"""
    try:
        from uuid import UUID
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID format")
    
    db_user = db.query(models.User).filter(models.User.id == user_uuid).first()
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return schemas.APIResponse(data=db_user, message="User retrieved successfully")

@router.put("/{user_id}", response_model=schemas.APIResponse[schemas.UserResponse])
def update_user(
    user_id: str, 
    user_update: schemas.UserUpdate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Update user information"""
    try:
        from uuid import UUID
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID format")
    
    if current_user.id != user_uuid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this user")
    
    db_user = db.query(models.User).filter(models.User.id == user_uuid).first()
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    
    logger.info(f"User updated: {db_user.email}")
    return schemas.APIResponse(data=db_user, message="User updated successfully")

@router.post("/{user_id}/preferences", response_model=schemas.APIResponse[schemas.NotificationPreferenceResponse], status_code=status.HTTP_201_CREATED)
def create_notification_preference(
    user_id: str, 
    preference: schemas.NotificationPreferenceCreate, 
    db: Session = Depends(get_db)
):
    """Create notification preference for a user"""
    try:
        from uuid import UUID
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID format")
    
    db_user = db.query(models.User).filter(models.User.id == user_uuid).first()
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Check if preference for this channel already exists
    existing = db.query(models.NotificationPreference).filter(
        models.NotificationPreference.user_id == user_uuid,
        models.NotificationPreference.channel == preference.channel
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Preference for channel '{preference.channel}' already exists"
        )
    
    db_preference = models.NotificationPreference(
        user_id=user_uuid,
        channel=preference.channel,
        enabled=preference.enabled,
        preferences=preference.preferences or {}
    )
    db.add(db_preference)
    db.commit()
    db.refresh(db_preference)
    
    logger.info(f"Notification preference created for user {user_id}, channel: {preference.channel}")
    return schemas.APIResponse(data=db_preference, message="Notification preference created successfully")

@router.get("/{user_id}/preferences", response_model=schemas.APIResponse[List[schemas.NotificationPreferenceResponse]])
def get_notification_preferences(user_id: str, db: Session = Depends(get_db)):
    """Get all notification preferences for a user"""
    try:
        from uuid import UUID
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID format")
    
    db_user = db.query(models.User).filter(models.User.id == user_uuid).first()
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return schemas.APIResponse(
        data=db_user.notification_preferences, 
        message="Notification preferences retrieved successfully"
    )

@router.put("/preferences/{preference_id}", response_model=schemas.APIResponse[schemas.NotificationPreferenceResponse])
def update_notification_preference(
    preference_id: int,
    preference_update: schemas.NotificationPreferenceUpdate,
    db: Session = Depends(get_db)
):
    """Update notification preference"""
    db_preference = db.query(models.NotificationPreference).filter(
        models.NotificationPreference.id == preference_id
    ).first()
    
    if db_preference is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preference not found")
    
    update_data = preference_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_preference, field, value)
    
    db.commit()
    db.refresh(db_preference)
    
    logger.info(f"Notification preference updated: {preference_id}")
    return schemas.APIResponse(data=db_preference, message="Notification preference updated successfully")

@router.delete("/preferences/{preference_id}", response_model=schemas.APIResponse)
def delete_notification_preference(preference_id: int, db: Session = Depends(get_db)):
    """Delete notification preference"""
    db_preference = db.query(models.NotificationPreference).filter(
        models.NotificationPreference.id == preference_id
    ).first()
    
    if db_preference is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preference not found")
    
    db.delete(db_preference)
    db.commit()
    
    logger.info(f"Notification preference deleted: {preference_id}")
    return schemas.APIResponse(message="Notification preference deleted successfully")

@router.post("/me/fcm-token", response_model=schemas.APIResponse[schemas.UserResponse])
def register_fcm_token(
    token_data: schemas.FCMTokenRequest,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Register or update FCM device token for push notifications
    
    Mobile apps should call this endpoint after login to register their device token.
    
    Request body:
    {
        "fcm_token": "firebase-device-token-string"
    }
    """
    # Update user's push token
    current_user.push_token = token_data.fcm_token
    db.commit()
    db.refresh(current_user)
    
    logger.info(f"FCM token registered for user: {current_user.email}")
    
    return schemas.APIResponse(
        data=current_user,
        message="FCM token registered successfully"
    )

@router.delete("/me/fcm-token", response_model=schemas.APIResponse)
def remove_fcm_token(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Remove FCM device token (e.g., when user logs out)
    
    Mobile apps should call this endpoint on logout to prevent sending
    notifications to devices that are no longer logged in.
    """
    current_user.push_token = None
    db.commit()
    
    logger.info(f"FCM token removed for user: {current_user.email}")
    
    return schemas.APIResponse(
        message="FCM token removed successfully"
    )

@router.get("/email/{email}", response_model=schemas.APIResponse[schemas.UserResponse])
def get_user_by_email(email: str, db: Session = Depends(get_db)):
    """Get user by email - Internal endpoint for service communication"""
    db_user = db.query(models.User).filter(models.User.email == email).first()
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return schemas.APIResponse(data=db_user, message="User retrieved successfully")

@router.get("/", response_model=schemas.APIResponse[List[schemas.UserResponse]])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """List all users (requires authentication)"""
    total = db.query(models.User).count()
    users = db.query(models.User).offset(skip).limit(limit).all()
    
    # Calculate pagination meta
    total_pages = (total + limit - 1) // limit
    current_page = (skip // limit) + 1
    
    meta = schemas.PaginationMeta(
        total=total,
        limit=limit,
        page=current_page,
        total_pages=total_pages,
        has_next=current_page < total_pages,
        has_previous=current_page > 1
    )
    
    return schemas.APIResponse(
        data=users,
        message="Users retrieved successfully",
        meta=meta
    )
