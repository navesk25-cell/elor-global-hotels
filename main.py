from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from pathlib import Path
from datetime import date, datetime, timezone
from contextlib import contextmanager
import sqlite3, uuid, os, secrets
from fastapi import Header

ROOT = Path(__file__).parent
DB = Path(os.environ.get('ELOR_DB_PATH', str(ROOT / 'elor_stage2.sqlite3')))
ADMIN_KEY = os.environ.get('ELOR_ADMIN_KEY', '')
def require_admin(x_admin_key: str | None = Header(default=None)):
 if not ADMIN_KEY or not x_admin_key or not secrets.compare_digest(x_admin_key, ADMIN_KEY):
  raise HTTPException(401, 'Staff access requires a valid admin key')
app = FastAPI(title='ELOR Global Hotels — Stage 2 Pilot API', version='0.2.0')
app.mount('/static', StaticFiles(directory=ROOT / 'static'), name='static')
HOTELS = [
 {'id':'signature1','name':'Signature 1 Hotel','area':'Barsha Heights','rooms':300,'description':'Modern city stay with easy access to Dubai business districts.','room_types':[{'id':'classic','name':'Classic Room','rate':390,'capacity':2},{'id':'premium','name':'Premium Room','rate':490,'capacity':2},{'id':'suite','name':'Executive Suite','rate':790,'capacity':3}]},
 {'id':'marina','name':'Signature Hotel Apartments & Spa','area':'Dubai Marina','rooms':95,'description':'Spacious apartment-style accommodation near Dubai Marina.','room_types':[{'id':'studio','name':'Studio Apartment','rate':520,'capacity':2},{'id':'onebed','name':'One-Bedroom Apartment','rate':720,'capacity':3}]},
 {'id':'barsha','name':'Signature Hotel Al Barsha','area':'Al Barsha','rooms':90,'description':'Convenient accommodation near Mall of the Emirates.','room_types':[{'id':'standard','name':'Standard Room','rate':350,'capacity':2},{'id':'deluxe','name':'Deluxe Room','rate':450,'capacity':3}]},
]
@contextmanager
def db():
 c=sqlite3.connect(DB)
 c.row_factory=sqlite3.Row
 try:
  yield c
  c.commit()
 finally: c.close()
with db() as c:
 c.execute('CREATE TABLE IF NOT EXISTS bookings (id TEXT PRIMARY KEY, hotel_id TEXT, room_type TEXT, guest_name TEXT, guest_email TEXT, checkin TEXT, checkout TEXT, guests INTEGER, nights INTEGER, total_aed INTEGER, status TEXT, created_at TEXT)')
 c.execute('CREATE INDEX IF NOT EXISTS idx_bookings_hotel_status ON bookings(hotel_id,status)')
 c.execute('CREATE TABLE IF NOT EXISTS ledger (id TEXT PRIMARY KEY, booking_id TEXT UNIQUE, guest_email TEXT, amount INTEGER, reason TEXT, created_at TEXT)')

class BookingIn(BaseModel):
 hotel_id: str
 room_type: str
 guest_name: str = Field(min_length=2,max_length=120)
 guest_email: str = Field(min_length=5,max_length=200)
 checkin: date
 checkout: date
 guests: int = Field(ge=1,le=8)

@app.get('/')
def home(): return FileResponse(ROOT / 'static' / 'index.html')
@app.get('/api/hotels')
def hotels(): return HOTELS
@app.post('/api/bookings')
def book(b:BookingIn):
 h=next((h for h in HOTELS if h['id']==b.hotel_id),None)
 if not h: raise HTTPException(404,'Hotel not found')
 room=next((r for r in h['room_types'] if r['id']==b.room_type),None)
 if not room: raise HTTPException(400,'Room type not found')
 if b.guests>room['capacity']: raise HTTPException(400,'Too many guests for selected room')
 nights=(b.checkout-b.checkin).days
 if b.checkin<date.today() or nights<1 or nights>30: raise HTTPException(400,'Choose valid future dates (1–30 nights)')
 if '@' not in b.guest_email or '.' not in b.guest_email.split('@')[-1]: raise HTTPException(400,'Enter a valid email')
 booking_id='ELR-'+uuid.uuid4().hex[:8].upper()
 total=nights*room['rate']
 with db() as c:
  c.execute('INSERT INTO bookings VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',(booking_id,b.hotel_id,b.room_type,b.guest_name.strip(),b.guest_email.strip().lower(),str(b.checkin),str(b.checkout),b.guests,nights,total,'pending',datetime.now(timezone.utc).isoformat()))
 return {'id':booking_id,'status':'pending','total_aed':total,'message':'Demo request recorded. This is NOT a confirmed hotel reservation.'}
@app.get('/api/bookings')
def bookings(x_admin_key: str | None = Header(default=None)):
 require_admin(x_admin_key)
 with db() as c: return [dict(x) for x in c.execute('SELECT * FROM bookings ORDER BY created_at DESC')]
@app.get('/api/wallet')
def wallet(email:str, x_admin_key: str | None = Header(default=None)):
 require_admin(x_admin_key)
 with db() as c:
  items=[dict(x) for x in c.execute('SELECT * FROM ledger WHERE guest_email=? ORDER BY created_at DESC',(email.strip().lower(),))]
 return {'balance_aed':sum(i['amount'] for i in items),'transactions':items}
@app.post('/api/bookings/{booking_id}/status')
def status(booking_id:str, status:str, x_admin_key: str | None = Header(default=None)):
 require_admin(x_admin_key)
 if status not in ('confirmed','declined','completed'): raise HTTPException(400,'Invalid status')
 with db() as c:
  b=c.execute('SELECT * FROM bookings WHERE id=?',(booking_id,)).fetchone()
  if not b: raise HTTPException(404,'Booking not found')
  allowed={'pending':['confirmed','declined'],'confirmed':['completed','declined'],'completed':[],'declined':[]}
  if status not in allowed[b['status']]: raise HTTPException(400,'Invalid status transition')
  c.execute('UPDATE bookings SET status=? WHERE id=?',(status,booking_id))
  if status=='completed':
   reward=round(b['total_aed']*0.03)
   c.execute('INSERT INTO ledger VALUES (?,?,?,?,?,?)',(uuid.uuid4().hex,booking_id,b['guest_email'],reward,'3% demo completed-stay reward',datetime.now(timezone.utc).isoformat()))
 return {'id':booking_id,'status':status}
