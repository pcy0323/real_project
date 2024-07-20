from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, MetaData, Table, select, func, and_, update
from sqlalchemy.orm import sessionmaker, Session
from starlette.middleware.sessions import SessionMiddleware
from starlette.exceptions import HTTPException
from sqlalchemy.sql import insert, select
from dotenv import load_dotenv
import os 
from random import *
import datetime
load_dotenv()

app = FastAPI()
global buyTry
buyTry = 2

async def not_found(request: Request, exc):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

app.add_exception_handler(HTTPException, not_found)
app.add_middleware(SessionMiddleware, secret_key="1your-secret-key", max_age=500)

templates = Jinja2Templates(directory="templates")

engine = create_engine(os.getenv("SQLALCHEMY_DATABASE_URL"))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
metadata = MetaData()

# Table 이름을 올바르게 수정하세요.
loginuser = Table('users', metadata, autoload_with=engine)
useraccount = Table('user_account', metadata, autoload_with=engine)
userdetail = Table('detail', metadata, autoload_with=engine)


async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:        
        db.close()

# 정적 파일 제공 설정
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def index(request : Request):
    return templates.TemplateResponse("first_main.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def index(request : Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/forgot_pw", response_class=HTMLResponse)
async def index(request : Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})

@app.post("/lgchk")
async def index(request : Request, userid : str = Form(...), userpassword: str = Form(...), db: Session = Depends(get_db)):
    stmt = select(func.count()).where(and_(loginuser.c.id== userid, loginuser.c.password == userpassword))
    result = db.execute(stmt).scalar()
    
    if result == 1:
        request.session.setdefault("id", userid)
        if userid == "admin":
            # stmt = select(loginuser)
            # myList = db.execute(stmt)
            # stmt = select(useraccount)
            # myList2 = db.execute(stmt)
            # return templates.TemplateResponse("admin.html", {"request": request,"data":myList,"data2":myList2})
            return RedirectResponse(url="/admin", status_code=302)
        else:
            stmt = update(loginuser).where(loginuser.c.id == userid).values(chknum= '{:04d}'.format(randint(0,10000)))
            db.execute(stmt)
            db.commit()
            return RedirectResponse(url="/main", status_code=302)
        
    else:
        error_message = "잘못된 아이디 혹은 비밀번호"
        return templates.TemplateResponse("index.html", {"request": request, "error_message": error_message})

@app.get("/admin")
async def index(request : Request, db: Session = Depends(get_db)):
    stmt = select(loginuser)
    myList = db.execute(stmt)
    stmt = select(useraccount)
    myList2 = db.execute(stmt)
    return templates.TemplateResponse("admin.html", {"request": request,"data":myList,"data2":myList2})

@app.get("/main")
async def index(request : Request, db: Session = Depends(get_db)):
    global buyTry
    buy = buyTry
    preId = request.session["id"]
    stmt = select(useraccount.c.account).where(useraccount.c.id == preId)
    account = db.execute(stmt).fetchall()

    stmt = select(useraccount.c.balance).where(useraccount.c.id == preId)
    balance = db.execute(stmt).fetchall()

    stmt = select(userdetail.c.pay_date, userdetail.c.pay).where(userdetail.c.id == preId)
    detail = db.execute(stmt).fetchall()
    stmt = update(loginuser).where(loginuser.c.id == preId).values(chknum= '{:04d}'.format(randint(0,10000)))
    db.execute(stmt)
    db.commit()
    return(templates.TemplateResponse("main.html", {"request": request, "uc":account[0][0], "bal":balance[0][0], "de":detail}))

@app.post("/lgin")
async def index(request: Request, db: Session = Depends(get_db)):
    preId = request.session["id"]
    stmt = select(useraccount.c.account).where(useraccount.c.id == preId)
    account = db.execute(stmt).fetchall()

    stmt = select(useraccount.c.balance).where(useraccount.c.id == preId)
    balance = db.execute(stmt).fetchall()

    stmt = select(userdetail.c.pay_date, userdetail.c.pay).where(userdetail.c.id == preId)
    detail = db.execute(stmt).fetchall()
    return templates.TemplateResponse("main.html", {"request": request, "uc":account[0][0], "bal":balance[0][0], "de":detail})


@app.get("/join", response_class=HTMLResponse)
async def index(request : Request):
    return templates.TemplateResponse("join.html", {"request": request})

@app.post("/join", response_class=HTMLResponse)
async def index(request: Request, joinuserid: str = Form(...), joinpassword: str = Form(...), db: Session = Depends(get_db)):
    stmt = insert(loginuser).values(id = joinuserid, password = joinpassword)
    db.execute(stmt)
    stmt = insert(useraccount).values(id = joinuserid, balance = 0, account= int('3333'+''.join([str(randint(0,9)) for _ in range(4)])))
    db.execute(stmt)
    db.commit()
    return RedirectResponse(url="/login", status_code=302)

@app.post("/show_pw", response_class=HTMLResponse)
async def index(request: Request, userid: str = Form(...), account_l3: str = Form(...), db: Session = Depends(get_db)):
    stmt = select(func.count()).where(and_(loginuser.c.id == userid, func.substr(useraccount.c.account, 6, 3) == account_l3,))
    result = db.execute(stmt).scalar()
    if result == 1:
        stmt = select(loginuser.c.password).where(and_(loginuser.c.id == userid, func.substr(useraccount.c.account, 6, 3) == account_l3,))
        get_pw = db.execute(stmt).scalar()      
        return templates.TemplateResponse("show_password.html", {"request": request,"data":get_pw})
    else:
        error_message = "잘못 입력하셨습니다"
        return templates.TemplateResponse("forgot_password.html", {"request": request, "error_message": error_message})


@app.get('/logout')
async def index(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")

@app.get("/mypage", response_class=HTMLResponse)
async def index(request : Request, db: Session = Depends(get_db)):
    preId = request.session["id"]
    stmt = select(loginuser.c.password).where(loginuser.c.id == preId)
    balances = db.execute(stmt).scalar()
    return templates.TemplateResponse("mypage.html", {"request" : request, "error_message":balances})

@app.get("/charge", response_class=HTMLResponse)
async def index(request : Request, db: Session = Depends(get_db)):
    try:
        preId = request.session["id"]
        stmt = select(loginuser).where(loginuser.c.id == preId)
        myList = db.execute(stmt)
    except:
        return templates.TemplateResponse("index.html", {"request": request})
    return templates.TemplateResponse("pay.html", {"request" : request, "pi":preId, "data": list(myList)[0][len(preId):len(preId)+5]})

@app.post("/charge", response_class=HTMLResponse)
async def index(request: Request, recharge_amount : int = Form(...), db: Session = Depends(get_db)):
    preId = request.session["id"]
    stmt = select(useraccount.c.balance).where(useraccount.c.id == preId)
    balances = db.execute(stmt).scalar()
    stmt = update(useraccount).where(useraccount.c.id == preId).values(balance = balances + recharge_amount)
    db.execute(stmt)
    stmt = insert(userdetail).values(id = preId, pay_date = datetime.datetime.now(), pay = recharge_amount)
    db.execute(stmt)
    db.commit()
    return RedirectResponse(url="/main", status_code=302)

@app.post("/charge2", response_class=HTMLResponse)
async def index(request: Request, recharge_amount : int = Form(...), db: Session = Depends(get_db), preId : str = Form(...)):
    stmt = select(useraccount.c.balance).where(useraccount.c.id == preId)
    balances = db.execute(stmt).scalar()
    stmt = update(useraccount).where(useraccount.c.id == preId).values(balance = balances + recharge_amount)
    db.execute(stmt)
    stmt = insert(userdetail).values(id = preId, pay_date = datetime.datetime.now(), pay = recharge_amount)
    db.execute(stmt)
    db.commit()
    return RedirectResponse(url="/admin", status_code=302)

@app.get("/changePW", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    preId = request.session["id"]
    stmt = select(func.count()).where(and_(loginuser.c.id== preId))
    result = db.execute(stmt).scalar()
    return templates.TemplateResponse("change_password.html", {"request": request, "idExist": result})

@app.post("/changeChkPW", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db), prePW : str = Form(...)):
    preId = request.session["id"]
    stmt = select(loginuser.c.password).where(loginuser.c.id == preId)
    userPW = db.execute(stmt).scalar()
    if(userPW == prePW):
        return templates.TemplateResponse("change_check_PW.html", {"request": request})
    else:
        error_message = "잘못 입력하였습니다"
        return templates.TemplateResponse("change_password.html", {"request": request, "error_message": error_message})

                

@app.post("/changePW", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db), newPW : str = Form(...), conPW : str = Form(...)):
    
    preId = request.session["id"]
    if(newPW == conPW):
        stmt = update(loginuser).where((loginuser.c.id == preId)).values(password = newPW)
        db.execute(stmt)
        db.commit()
        return RedirectResponse(url="/main", status_code=302)
    else:
        error_message = ""
        return templates.TemplateResponse("cahnge_check_PW.html", {"request": request, "error_message": error_message})

@app.post("/pay", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db), totalD : int = Form()):
    preId = request.session["id"]
    stmt = select(useraccount.c.balance).where(useraccount.c.id == preId)
    balances = db.execute(stmt).scalar()

    if balances - totalD < 0:
        global buyTry
        buyTry = 0
        return RedirectResponse(url="/main", status_code=302)
    else:
        buyTry = 1
        stmt = update(useraccount).where(useraccount.c.id == preId).values(balance = balances - totalD)
        db.execute(stmt)
        stmt = insert(userdetail).values(id = preId, pay_date = datetime.datetime.now(), pay = -totalD)
        db.execute(stmt)
        db.commit()
    return RedirectResponse(url="/main", status_code=302)


if __name__ == '__main__':
    import uvicorn    
    uvicorn.run(app, host="127.0.0.1", port=8000)