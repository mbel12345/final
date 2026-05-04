from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from uuid import UUID

from app.auth.dependencies import get_current_active_user
from app.database import get_db
from app.database import get_engine
from app.database.database_init import init_db
from app.models.calculation import Calculation
from app.models.user import User
from app.schemas.calculation import CalculationBase
from app.schemas.calculation import CalculationResponse
from app.schemas.calculation import CalculationUpdate
from app.schemas.token import TokenResponse
from app.schemas.user import UserCreate
from app.schemas.user import UserLogin
from app.schemas.user import UserResponse

@asynccontextmanager
async def lifespan(app: FastAPI):

    print('Creating tables...')
    engine = get_engine()
    init_db(engine=engine)
    print('Tables created successfully')
    yield

app = FastAPI(
    title='Calculations API',
    description='API for managing calculations',
    version='1.0.0',
    lifespan=lifespan,
)

# Mount the static files directory
app.mount('/static', StaticFiles(directory='static'), name='static')

# Set up Jinja2 templates directory
templates = Jinja2Templates(directory='templates')

# Home page
@app.get('/', response_class=HTMLResponse, tags=['web'])
def read_index(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})

# Login page
@app.get('/login', response_class=HTMLResponse, tags=['web'])
def login_page(request: Request):
    return templates.TemplateResponse('login.html', {'request': request})

# Registration page
@app.get('/register', response_class=HTMLResponse, tags=['web'])
def register_page(request: Request):
    return templates.TemplateResponse('register.html', {'request': request})

# Dashboard page
@app.get('/dashboard', response_class=HTMLResponse, tags=['web'])
def dashboard_page(request: Request):
    return templates.TemplateResponse('dashboard.html', {'request': request})

# Page for viewing a single calculation
@app.get('/dashboard/view/{calc_id}', response_class=HTMLResponse, tags=['web'])
def view_calculation_page(request: Request, calc_id: str):
    return templates.TemplateResponse('view_calculation.html', {
        'request': request,
        'calc_id': calc_id,
    })

# Page for editing a calculation
@app.get('/dashboard/edit/{calc_id}', response_class=HTMLResponse, tags=['web'])
def edit_calculation_page(request: Request, calc_id: str):
    return templates.TemplateResponse('edit_calculation.html', {
        'request': request,
        'calc_id': calc_id,
    })

# Health endpoint
@app.get('/health', tags=['health'])
def read_health():
    return {'status': 'ok'}

# User registration route
@app.post(
    '/auth/register',
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=['auth'],
)
def register(user_create: UserCreate, db: Session = Depends(get_db)):

    # Register new user

    print('/auth/register')

    user_data = dict(user_create)
    del(user_data['confirm_password'])
    try:
        user = User.register(db, user_data)
        db.commit()
        db.refresh(user)
        print('Registration succeeded')
        return user
    except ValueError as e:
        print(f'Register failed: {e}')
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# User login route
@app.post('/auth/login', response_model=TokenResponse, tags=['auth'])
def login_json(user_login: UserLogin, db: Session = Depends(get_db)):

    # Login with JSON payload

    print('/auth/login')

    auth_result = User.authenticate(db, user_login.username, user_login.password)
    if auth_result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid username or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    user = auth_result['user']
    db.commit()

    expires_at = auth_result.get('expires_at')
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    return TokenResponse(
        access_token=auth_result['access_token'],
        refresh_token=auth_result['refresh_token'],
        token_type='bearer',
        expires_at=expires_at,
        user_id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
    )

@app.post('/auth/token', tags=['auth'])
def login_form(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):

    # Login with form data for Swagger UI

    print('/auth/token')

    auth_result = User.authenticate(db, form_data.username, form_data.password)
    if auth_result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid username or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    return {
        'access_token': auth_result['access_token'],
        'token_type': 'bearer',
    }

# ------------------------------------------------------------------------------
# Calculation Endpoints
# ------------------------------------------------------------------------------

# Create (Add) Calculation
@app.post(
    '/calculations',
    response_model=CalculationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=['calculations'],
)
def create_calculation(
    calculation_data: CalculationBase,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    # Create a new calculation for the authenticated user

    try:
        new_calc = Calculation.create(
            calculation_type=calculation_data.type,
            user_id=current_user.id,
            inputs=calculation_data.inputs,
        )
        new_calc.result = new_calc.get_result()

        db.add(new_calc)
        db.commit()
        db.refresh(new_calc)
        return new_calc

    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

@app.get('/calculations', response_model=list[CalculationResponse], tags=['calculations'])
def list_calculations(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    # List all calculations belonging to the current authenticated user.

    calculations = db.query(Calculation).filter(Calculation.user_id == current_user.id).all()
    return calculations

@app.get('/calculations/{calc_id}', response_model=CalculationResponse, tags=['calculations'])
def get_calculation(
    calc_id: str,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    # Retrieve a single calculation by its UUID, if it belongs to the current user

    try:
        calc_uuid = UUID(calc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail='Invalid calculation id format')

    calculation = db.query(Calculation).filter(
        Calculation.id == calc_uuid,
        Calculation.user_id == current_user.id,
    ).first()

    if not calculation:
        raise HTTPException(status_code=404, detail='Calculation not found')

    return calculation

@app.put('/calculations/{calc_id}', response_model=CalculationResponse, tags=['calculations'])
def update_calculation(
    calc_id: str,
    calculation_update: CalculationUpdate,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    # Update the inputs and result of a specific calculation

    try:
        calc_uuid = UUID(calc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail='Invalid calculation id format')

    calculation = db.query(Calculation).filter(
        Calculation.id == calc_uuid,
        Calculation.user_id == current_user.id,
    ).first()

    if not calculation:
        raise HTTPException(status_code=404, detail='Calculation not found')

    if calculation_update.inputs is not None:
        calculation.inputs = calculation_update.inputs
        calculation.result = calculation.get_result()

    calculation.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(calculation)
    return calculation

@app.delete('/calculations/{calc_id}', status_code=status.HTTP_204_NO_CONTENT, tags=['calculations'])
def delete_calculation(
    calc_id: str,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    # Delete a calculation by its UUID, if it belongs to the current user.

    try:
        calc_uuid = UUID(calc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail='Invalid calculation id format')

    calculation = db.query(Calculation).filter(
        Calculation.id == calc_uuid,
        Calculation.user_id == current_user.id,
    ).first()

    if not calculation:
        raise HTTPException(status_code=404, detail='Calculation not found')

    db.delete(calculation)
    db.commit()
    return None

if __name__ == '__main__':

    # Main method should not be included in test cases
    import uvicorn # pragma: no cover
    uvicorn.run('app.main:app', host='127.0.0.1', port=8001, log_level='info') # pragma: no cover
