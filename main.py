import requests, re, datetime
import traceback, asyncio, os
from fastapi import FastAPI
from contextlib import asynccontextmanager


# uvicorn main:app --reload

def send_msg(text: str):
    requests.post(
        r'https://api.telegram.org/bot'+os.environ.get('TOKEN', 'TOKEN')+'/sendMessage', 
        json={
            'chat_id': os.environ.get('CHATID', 'CHATID'), 
            'text': text, 
        }, 
        timeout=10
    )

def load_movie(date: str) -> dict:
    res = requests.get(
        r'https://cgv.co.kr/api/v1/booking/searchMovScnInfo',
        params={
            'coCd': 'A420', 
            'siteNo': '0013', 
            'scnYmd': date, 
            'rtctlScopCd': '08', 
        }, 
        headers={
            'method': 'get', 
            'referer': r'https://cgv.co.kr/cnm/movieBook/cinema', 
            'User-Agent': os.environ.get('USERAGENT', 'USERAGENT'),
        }, 
        timeout=10
    )
    print(res)
    return res.json()

def load_movies() -> list:
    movies = []
    today = datetime.date.today()
    for j in range(21):
        date = today + datetime.timedelta(days=j)
        res = load_movie(date.strftime(r'%Y%m%d'))
        for i in res['data']:
            if re.compile(r'imax').search(i['scnsEnm'].lower()):
                movies.append(f"{i['prodNm']} {date.strftime(r'%Y.%m.%d')} {i['scnsrtTm'][:2]}:{i['scnsrtTm'][2:]}~{i['scnendTm'][:2]}:{i['scnendTm'][2:]}")
    return movies

async def main():
    try:
        pre_movies = set(load_movies())
    except:
        traceback.print_exc()
    while True:
        try:
            print(f'Load movies at {datetime.datetime.now().strftime(r"%Y.%m.%d %H:%M:%S")}')
            for i in load_movies():
                if i not in pre_movies:
                    pre_movies.add(i)
                    print(f'New {i}')
                    send_msg(i)
                # else:
                #     print(f'Previous {i}')
        except:
            traceback.print_exc()
        await asyncio.sleep(290)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print('Server connected')
    send_msg('Server connected')
    task = asyncio.create_task(main())

    yield

    send_msg('Server down')
    task.cancel()
    print('Server down')

app = FastAPI(lifespan=lifespan)

@app.get('/')
def status_check():
    return {'status': 'OK'}
