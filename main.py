import os
import random
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional

from database import db, create_document

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StartOtpRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    phone: str = Field(..., min_length=8, max_length=16)

class VerifyOtpRequest(BaseModel):
    phone: str = Field(..., min_length=8, max_length=16)
    otp: str = Field(..., min_length=4, max_length=6)

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        # Try to import database module
        from database import db
        
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response

# --- OTP Flow Endpoints ---
# NOTE: This demo generates an OTP server-side and stores it with short expiry.
# In production, integrate with SMS provider to actually send the OTP.

@app.post("/api/auth/start")
def start_otp(req: StartOtpRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    # Generate a 6-digit OTP
    otp = f"{random.randint(100000, 999999)}"
    expires = datetime.now(timezone.utc) + timedelta(minutes=5)

    # Upsert auth record for this phone
    payload = {
        "name": req.name.strip(),
        "phone": req.phone.strip(),
        "otp_code": otp,
        "otp_expires": expires,
        "verified": False,
        "updated_at": datetime.now(timezone.utc)
    }

    db["auth"].update_one({"phone": payload["phone"]}, {"$set": payload, "$setOnInsert": {"created_at": datetime.now(timezone.utc)}}, upsert=True)

    # For demo, return OTP in response so user can test without SMS
    return {"ok": True, "demo_otp": otp, "expires_in_sec": 300}

@app.post("/api/auth/verify")
def verify_otp(req: VerifyOtpRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    record = db["auth"].find_one({"phone": req.phone})
    if not record:
        raise HTTPException(status_code=404, detail="Start verification first")

    if not record.get("otp_code") or not record.get("otp_expires"):
        raise HTTPException(status_code=400, detail="No OTP generated")

    # Validate expiry
    if datetime.now(timezone.utc) > record["otp_expires"]:
        raise HTTPException(status_code=400, detail="OTP expired")

    # Validate code
    if req.otp != record["otp_code"]:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # Mark verified and clear otp_code
    db["auth"].update_one({"_id": record["_id"]}, {"$set": {"verified": True}, "$unset": {"otp_code": "", "otp_expires": ""}})

    return {"ok": True, "verified": True}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
