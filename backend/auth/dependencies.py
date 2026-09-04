from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User
from backend.auth.security import SECRET_KEY, ALGORITHM
from backend.auth.schemas import TokenData

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        worker_id: str = payload.get("sub")
        if worker_id is None:
            raise credentials_exception
        token_data = TokenData(worker_id=worker_id)
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.worker_id == token_data.worker_id).first()
    if user is None:
        raise credentials_exception
    return user
