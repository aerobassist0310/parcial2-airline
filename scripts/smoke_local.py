"""Prueba local HTTP/SQLite. No equivale a ensayos PostgreSQL/AWS ni R1-R12."""
import concurrent.futures as cf
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import urllib.error

def main():
    base_dir=Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as temp:
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]
        env=os.environ.copy();env.update(DB_MODE='sqlite',SQLITE_PATH=str(Path(temp)/'test.db'),APP_HOST='127.0.0.1',APP_PORT=str(port))
        base=f'http://127.0.0.1:{port}'
        def request(path,body=None):
            payload=None if body is None else json.dumps(body).encode()
            req=urllib.request.Request(base+path,data=payload,headers={'Content-Type':'application/json'})
            try:
                with urllib.request.urlopen(req,timeout=30) as r:return r.status,r.read().decode()
            except urllib.error.HTTPError as e:return e.code,e.read().decode()
        with open(Path(temp)/'server.log','w') as log:
            process=subprocess.Popen([sys.executable,'-m','backend.app'],cwd=base_dir,env=env,stdout=log,stderr=log)
            try:
                for _ in range(100):
                    try:
                        if request('/health')[0]==200:break
                    except OSError:time.sleep(.05)
                else:raise RuntimeError('El servidor no inició')
                for page in ['/','/manager','/app.js','/style.css']:
                    assert request(page)[0]==200,page
                assert request('/reservations/no-existe')[0]==404
                assert request('/reservations',{'flight_id':'NO','passenger_name':'Test','fare_class':'ECONOMY'})[0]==404
                races=[]
                for capacity in [1,7,1,7]:
                    fid='LOCAL-'+str(len(races)); flight={'flight_id':fid,'route':'BOG-MDE','flight_date':'2030-01-15','capacity':capacity,'price_cents':10000}
                    assert request('/admin/flights',flight)[0]==201
                    assert request('/admin/flights',flight)[0]==409
                    assert request('/flights/search?origin=BOG&destination=MDE&date=2030-01-15')[0]==200
                    barrier=threading.Barrier(50)
                    def reserve(i):
                        barrier.wait(timeout=20)
                        return request('/reservations',{'flight_id':fid,'passenger_name':f'Persona {i}','fare_class':'ECONOMY'})
                    with cf.ThreadPoolExecutor(max_workers=50) as pool:
                        results=list(pool.map(reserve,range(50)))
                    codes=[r[0] for r in results]
                    assert codes.count(201)==capacity,codes
                    assert codes.count(409)==50-capacity,codes
                    rid=json.loads(next(body for code,body in results if code==201))['reservation_id']
                    assert request('/reservations/'+rid)[0]==200
                    remaining=json.loads(request('/flights/search?origin=BOG&destination=MDE&date=2030-01-15')[1])
                    assert all(row['flight_id']!=fid for row in remaining)
                    races.append({'capacity':capacity,'201':codes.count(201),'409':codes.count(409)})
                print(json.dumps({'result':'OK','backend':'SQLite local','http_requests_approx':225,'races':races,'aws_tested':False},ensure_ascii=False))
            finally:
                process.terminate();process.wait(timeout=10)

if __name__=='__main__':main()
