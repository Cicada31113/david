# main.py
import json
from datetime import datetime
from textwrap import fill

LOG_FILE = 'mission_computer_main.log'
JSON_FILE = 'mission_computer_main.json'
DT_FMT = '%Y-%m-%d %H:%M:%S'


def read_lines(path: str) -> list[str]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read().splitlines()
    except FileNotFoundError:
        print(f'[에러] {path} 파일이 없습니다.')
        raise SystemExit(1)
    except UnicodeDecodeError:
        print(f'[에러] {path} 파일의 인코딩이 UTF-8이 아닙니다.')
        raise SystemExit(1)


def parse_csv_line(line: str) -> tuple[str, str, str] | None:
    # 기대 포맷: timestamp,event,message
    parts = line.strip().split(',', 2)
    if len(parts) != 3:
        return None
    ts, event, msg = (p.strip() for p in parts)
    if not ts or not msg:
        return None
    return ts, event, msg


def pretty_table(rows: list[tuple[str, str, str]]) -> str:
    # 보기 좋은 표 출력(옵션)
    ts_w = max([len('timestamp')] + [len(r[0]) for r in rows]) if rows else len('timestamp')
    ev_w = max([len('event')] + [len(r[1]) for r in rows]) if rows else len('event')
    line_width = 100
    header = f"{'timestamp'.ljust(ts_w)}  {'event'.ljust(ev_w)}  message"
    sep = '-' * len(header)
    out = [header, sep]
    for ts, ev, msg in rows:
        wrapped = fill(msg, width=line_width, subsequent_indent=' ' * (ts_w + ev_w + 4))
        out.append(f"{ts.ljust(ts_w)}  {ev.ljust(ev_w)}  {wrapped}")
    return '\n'.join(out)


def main() -> None:
    # 1) 로그 읽기
    lines = read_lines(LOG_FILE)

    # 2) 원본 전체 출력
    print('=== 로그 원본 ===')
    for line in lines:
        print(line)

    # 3) 파싱 → 데이터 로우 보존 + 과제요구용 리스트[(timestamp, message)]
    data_rows: list[tuple[str, str, str]] = []
    start_idx = 1 if lines and lines[0].lower().startswith('timestamp') else 0
    for line in lines[start_idx:]:
        parsed = parse_csv_line(line)
        if parsed:
            data_rows.append(parsed)

    # 과제 요건: "날짜/시간과 메시지를 분리하여 리스트 객체로 전환"
    log_list: list[tuple[str, str]] = [(ts, msg) for ts, _ev, msg in data_rows]

    # 리스트 객체(원형) 화면 출력
    print('\n=== 리스트 객체 (raw list) ===')
    print(log_list)

    # 보기 좋은 표(옵션)
    if data_rows:
        print('\n=== 리스트 객체 (표 형태) ===')
        print(pretty_table(data_rows))

    # 4) 시간 역순 정렬
    try:
        log_list.sort(key=lambda x: datetime.strptime(x[0], DT_FMT), reverse=True)
        data_rows.sort(key=lambda x: datetime.strptime(x[0], DT_FMT), reverse=True)
    except ValueError:
        # 포맷 안 맞으면 문자열 기준 역순
        log_list.sort(key=lambda x: x[0], reverse=True)
        data_rows.sort(key=lambda x: x[0], reverse=True)

    # 정렬된 리스트 원형 출력
    print('\n=== 시간 역순 정렬 리스트 (raw list) ===')
    print(log_list)

    # 표 형태도 같이(옵션)
    if data_rows:
        print('\n=== 시간 역순 정렬 리스트 (표 형태) ===')
        print(pretty_table(data_rows))

    # 5) Dict 객체로 변환 (key=timestamp, value=message)
    log_dict: dict[str, str] = {ts: msg for ts, msg in log_list}

    # 6) Dict를 화면에 pretty JSON으로 출력
    print('\n=== Dict 객체 (pretty JSON) ===')
    print(json.dumps(log_dict, ensure_ascii=False, indent=2))

    # 7) JSON 파일 저장 (UTF-8)
    try:
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(log_dict, f, ensure_ascii=False, indent=2)
        print(f'\n[완료] JSON 저장: {JSON_FILE}')
    except OSError as e:
        print(f'[에러] JSON 저장 실패: {e}')
        raise SystemExit(1)


if __name__ == '__main__':
    main()
