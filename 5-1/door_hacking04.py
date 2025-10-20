import zipfile
import string
import time
import multiprocessing
import subprocess
import os
import platform

def detect_cpu_workers():
    try:
        return multiprocessing.cpu_count()
    except NotImplementedError:
        return 4

def detect_gpu_tools():
    tools = {}
    try:
        subprocess.run(['hashcat','--version'], capture_output=True, check=True)
        tools['hashcat'] = True
    except:
        tools['hashcat'] = False
    return tools

def run_hashcat(zip_path):
    dict_file = 'high_prob_passwords.txt'
    if not os.path.exists(dict_file):
        return None
    try:
        subprocess.run([
            'hashcat','-m','13600',zip_path,dict_file,
            '--force','--quiet','--status','--status-timer=5'
        ], timeout=600)
        potfile = os.path.expanduser('~/.hashcat/hashcat.potfile')
        if os.path.exists(potfile):
            with open(potfile) as f:
                last = f.readlines()[-1].strip()
                return last.split(':',1)[1] if ':' in last else None
    except:
        pass
    return None

def idx_to_password(idx, charset, length):
    pw=[]
    for _ in range(length):
        pw.append(charset[idx%len(charset)])
        idx//=len(charset)
    return ''.join(reversed(pw))

def worker(start,end,charset,length,zip_path,rq,pq,wid):
    attempts=0
    try:
        with zipfile.ZipFile(zip_path) as zf:
            for i in range(start,end):
                pwd=idx_to_password(i,charset,length)
                attempts+=1
                if attempts%10000==0:
                    pq.put((wid,attempts,pwd,time.time()))
                try:
                    zf.extractall(pwd=pwd.encode())
                    rq.put(pwd)
                    break
                except RuntimeError:
                    continue
    except Exception as e:
        print(f"[ERROR] W{wid}:{e}")
    pq.put((wid,attempts,None,time.time()))

def unlock_zip_parallel(zip_path):
    charset=string.ascii_lowercase+string.digits
    length=6
    keyspace=len(charset)**length

    workers=detect_cpu_workers()
    print(f"[SYSTEM] CPU cores: {workers}")

    gpu=detect_gpu_tools()
    if gpu.get('hashcat'):
        print("[SYSTEM] Using GPU hashcat")
        pwd=run_hashcat(zip_path)
        if pwd:
            with open('password.txt','w') as f: f.write(pwd)
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(pwd=pwd.encode())
            print(f"[SUCCESS] {pwd}")
            return

    batch=keyspace//workers
    mgr=multiprocessing.Manager()
    rq=pq=mgr.Queue(),mgr.Queue()
    result_q,progress_q=rq

    procs=[]
    start=time.time()
    print(f"[START] {time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(start))}")

    for i in range(workers):
        s=i*batch
        e=keyspace if i==workers-1 else (i+1)*batch
        p=multiprocessing.Process(target=worker,args=(s,e,charset,length,zip_path,result_q,progress_q,i))
        p.start(); procs.append(p)

    prog=[0]*workers
    found=None
    try:
        while True:
            while not result_q.empty():
                found=result_q.get(); break
            while not progress_q.empty():
                wid,att,pwd,t=progress_q.get()
                prog[wid]=att
                if pwd and att%10000==0:
                    tot=sum(prog); perc=tot/keyspace*100
                    print(f"[PROG] W{wid} {att:,} tot={tot:,} ({perc:.2f}%) pwd={pwd}")
            if found:
                for p in procs: p.terminate()
                elapsed=time.time()-start
                print(f"[SUCCESS] {found} in {elapsed:.1f}s")
                with open('password.txt','w') as f: f.write(found)
                with zipfile.ZipFile(zip_path) as zf: zf.extractall(pwd=found.encode())
                return
            if not any(p.is_alive() for p in procs): break
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("[SYSTEM] Interrupted"); 
        for p in procs: p.terminate()

    if not found:
        print(f"[FAIL] in {time.time()-start:.1f}s")

if __name__=='__main__':
    unlock_zip_parallel('emergency_storage_key.zip')
