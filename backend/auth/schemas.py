from pydantic import BaseModel, Field

class Token(BaseModel):
    access_token: str
    token_type: str
    worker_id: str | None = None
    profile_complete: bool = False
    name: str | None = None

class TokenData(BaseModel):
    worker_id: str = None

class LoginRequest(BaseModel):
    phone: str
    password: str

class SignupRequest(BaseModel):
    email: str
    phone: str
    name: str = ""
    occupation: str = ""
    password: str


class ProfileUpdateRequest(BaseModel):
    name: str | None = None
    occupation: str | None = None
    monthly_income_avg: int | None = Field(default=None, ge=0)
    fixed_expenses: int | None = Field(default=None, ge=0)
    variable_expenses: int | None = Field(default=None, ge=0)
    total_debt: int | None = Field(default=None, ge=0)
    monthly_emi: int | None = Field(default=None, ge=0)
    savings_balance: int | None = Field(default=None, ge=0)
    emergency_buffer: int | None = Field(default=None, ge=0)
    dependents: int | None = Field(default=None, ge=0)
    avg_work_hours_per_week: int | None = Field(default=None, ge=0)
    active_platforms: list[str] | None = None
