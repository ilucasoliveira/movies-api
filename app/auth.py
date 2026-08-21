import os
from dotenv import load_dotenv
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from secrets import compare_digest

load_dotenv()

USERNAME = os.getenv("APP_USERNAME") 
PASSWORD = os.getenv("APP_PASSWORD")

security = HTTPBasic()

def user_authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    is_username_correct = compare_digest(credentials.username, USERNAME)
    is_password_correct = compare_digest(credentials.password, PASSWORD)
    
    if not (is_username_correct and is_password_correct):
        raise HTTPException(status_code=401, detail="Unauthorized Credential", headers={"WWW-Authenticate":"Basic"})
    
    return credentials