from datetime import datetime

def read_log(path: str = 'mission_computer_main.log') -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()  # 여기서 발생하는 예외는 그대로 main으로 전파됨

def main():
    try:
        raw = read_log()
        lines = raw.splitlines()
        if not lines or lines[0].strip() != 'timestamp,event,message':
            raise ValueError  # 헤더 불일치

        pairs = []
        for s in lines[1:]:
            if not s.strip():
                continue  # 빈 줄 무시
            a = s.split(',', 2)  # message 콤마 보존
            if len(a) != 3:
                raise ValueError  # 컬럼수 불일치
            ts, _, msg = (x.strip() for x in a)  # event 무시
            datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')  # 형식 불일치 시 ValueError
            pairs.append((ts, msg))

        sorted_pairs = sorted(
            pairs,
            key=lambda x: datetime.strptime(x[0], '%Y-%m-%d %H:%M:%S'),
            reverse=True
        )
        result_dict = dict(sorted_pairs)

        # 성공 경로: 정확히 4회 출력
        print(raw)           # ① 원문
        print(pairs)         # ② 리스트
        print(sorted_pairs)  # ③ 정렬 리스트
        print(result_dict)   # ④ 딕셔너리

    # 예외 종류별 지정 문구(우선순위대로)
    except (FileNotFoundError, PermissionError, OSError):
        print('File open error.')
    except UnicodeDecodeError:
        print('Decoding error.')
    except ValueError:
        print('Invalid log format.')
    except Exception:
        print('Processing error.')

if __name__ == '__main__':
    main()
