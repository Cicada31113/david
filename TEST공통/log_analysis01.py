from datetime import datetime

def read_log(path: str = 'mission_computer_main.log') -> str:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except (FileNotFoundError, PermissionError, OSError):
        print('File open error.')
        return ''
    except UnicodeDecodeError:
        print('Decoding error.')
        return ''
    except Exception:
        # 문제 요건상 여기서 임의 메시지 출력 금지. 상위에서 처리.
        return ''

def main():
    raw = read_log()
    if not raw:
        return  # 예외 시 이미 메시지 출력됨. 즉시 종료.

    # 1) 헤더 검증
    try:
        lines = raw.splitlines()
        if not lines or lines[0].strip() != 'timestamp,event,message':
            print('Invalid log format.')
            return
    except Exception:
        print('Invalid log format.')
        return

    # 2) 원문 그대로 1회 출력 (라벨 금지)
    print(raw)

    # 3) 파싱: (timestamp, message) 리스트
    pairs: list[tuple[str, str]] = []
    try:
        for line in lines[1:]:
            if not line.strip():
                continue
            parts = line.strip().split(',', 2)  # 최대 2번 분리
            if len(parts) != 3:
                print('Invalid log format.')
                return
            ts, _event, msg = parts[0].strip(), parts[1].strip(), parts[2].strip()
            # timestamp 형식 검증
            datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
            pairs.append((ts, msg))
    except ValueError:
        print('Invalid log format.')
        return
    except Exception:
        print('Processing error.')
        return

    # 4) 원본 리스트 출력
    print(pairs)

    # 5) 내림차순 정렬 리스트 출력
    try:
        # 문자열 정렬도 동치지만, 명시적으로 datetime 키로 정렬
        sorted_pairs = sorted(
            pairs,
            key=lambda x: datetime.strptime(x[0], '%Y-%m-%d %H:%M:%S'),
            reverse=True
        )
        print(sorted_pairs)
    except Exception:
        print('Processing error.')
        return

    # 6) dict로 변환하여 출력
    try:
        result_dict = dict(sorted_pairs)
        print(result_dict)
    except Exception:
        print('Processing error.')
        return

if __name__ == '__main__':
    main()
