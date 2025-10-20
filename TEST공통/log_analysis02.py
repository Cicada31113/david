from datetime import datetime

def read_log(path='mission_computer_main.log'):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except (FileNotFoundError, PermissionError, OSError):
        print('File open error.')
    except UnicodeDecodeError:
        print('Decoding error.')
    except Exception:
        print('File open error.')
    return ''

def main():
    raw = read_log()
    if not raw: return
    lines = raw.splitlines()
    if not lines or lines[0].strip() != 'timestamp,event,message':
        print('Invalid log format.'); return

    print(raw)  # ① 원문

    try:
        pairs = []
        for s in lines[1:]:
            if not s.strip(): continue
            parts = s.split(',', 2)
            if len(parts) != 3: print('Invalid log format.'); return
            ts, _, msg = [x.strip() for x in parts]
            datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
            pairs.append((ts, msg))
    except ValueError:
        print('Invalid log format.'); return
    except Exception:
        print('Processing error.'); return

    print(pairs)  # ② 리스트

    try:
        sp = sorted(pairs, key=lambda x: datetime.strptime(x[0], '%Y-%m-%d %H:%M:%S'), reverse=True)
        print(sp)         # ③ 정렬 리스트
        print(dict(sp))   # ④ 딕셔너리
    except Exception:
        print('Processing error.')

if __name__ == '__main__':
    main()
