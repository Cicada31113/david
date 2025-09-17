from typing import List, Tuple

LOG_FILE = 'mission_computer_main.log'

def load_log(path: str = LOG_FILE) -> List[Tuple[str, str, str]]:
    rows: List[Tuple[str, str, str]] = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            header = f.readline()
            print("헤더 내용:", header.strip())
            if not header:
                return rows
            for line in f:
                parts = line.strip().split(',', 2)
                if len(parts) != 3:
                    continue
                ts, event, msg = (p.strip() for p in parts)
                rows.append((ts, event, msg))
                print(rows)

    except FileNotFoundError:
        print('파일없음', path)
    except UnicodeDecodeError:
        print('인코딩오류', path)
    except OSError as e:
        print('파일오류', path, e)
    return rows

def print_log(rows: List[Tuple[str, str, str]]) -> None:
    if not rows:
        print('로그가 없습니다.')
        return
    print("Timestamp, Event, Message")
    for ts, event, msg in rows:
        print(f"{ts}, {event}, {msg}")



def rows_to_dict(rows: List[Tuple[str, str, str]]) -> dict[str, dict[str, str]]:
    log_dict : dict[str, dict[str, str]] = {}   # 타입힌트를 하나만 넣어서, join
    for ts, event, msg in rows:
        log_dict[ts] = {
            'event': event,
            'message': msg
        }
    return log_dict

import json # 파일 크기에 따라 의견이 달라질 수 있음. / 인터프리터, 컴파일러 (인터프리터는 한 줄 씩 실행하는)
            # json 은 현재 전역스코프인데 위치상 중간에 있음. 근데 컴파일러가 어떻게 구현하느냐에 따라 다름. 
            # 일반적으로는 위에서 못쓴다고 생각하면된다. 
            # 맨위에 둬도 좋다. 협업시 인풋을 위에서 쓰기도 한다.

def save_to_json(data: dict[str, dict[str, str]], path: str = "mission_computer_main.json") -> None:
    try:
        with open(path, "w", encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"JSON 파일로 저장됨: {path}")
    except OSError as e:
        print(f"파일 저장 오류: {e}")  

def save_danger_logs(rows: list[tuple[str, str, str]], path: str = 'danger_logs.log') -> None:
    danger_kw = ['explosion', 'unstable', 'leak', 'overheat', 'Oxygen']
    try:
        with open(path, 'w', encoding='utf-8') as f:
            for ts, event, msg in rows:
                if any(k in msg for k in danger_kw):
                    f.write(f'{ts}, {event}, {msg}\n')
        print(f"위험 로그 저장됨: {path}")
    except OSError as e:
        print(f"파일 저장 오류: {e}")

def write_markdown_report(rows: List[Tuple[str, str, str]], path: str = 'log_analysis.md') -> None:
    msgs = [m for _, _, m in rows]
    blob = ' '.join(msgs)
    blob_low = blob.lower()

# 다양한 교집합들을 분기점으로 나누고 싶었을 때, 
# 이진법으로 개수만큼 -> 분기문을 많이 줄일 수 있을 때 (리팩토링해보자)
    danger_lines = [
        f'- {ts} {event} {msg}'
        for ts, event, msg in rows
        if ('explosion in msg') or ('leak in msg') or ('unstable in msg') or ('overheat in msg') or ('oxygen' in msg.lower())
    ]
    if ('oxygen' in blob_low and 'explosion' in blob_low) or ('Oxygen' in blob and 'explosion' in blob):
        cause = '산소 계통 관련 이상 후 폭발로 진행된 사고 가능성'
    elif ('oxygen' in blob_low) or ('Oxygen' in blob):
        cause = '산소 계통 이상 징후 감지(추가 점검 필요)'
    elif ('explosion' in blob_low) or ('explosion' in blob):
        cause = '폭발 징후 감지(원인 식별 필요)'
    elif ('leak' in blob_low) or ('leak' in blob):
        cause = '누출 징후 감지(추가 점검 필요)'
    elif ('overheat' in blob_low) or ('overheat' in blob):
        cause = '과열 징후 감지(열관리 점검 필요)'
    else:
        cause = '기타 이상 징후 없음'
    
    lines = []
    lines.append('# 사고 원인 분석 보고서')
    lines.append('')
    lines.append('## 1. 로그 개요')
    lines.append(f'- 총 {len(rows)}개의 로그가 기록됨')
    if rows:
        lines.append(f'- 기간: {rows[0][0]} ~ {rows[-1][0]}')
    lines.append('')
    lines.append('## 2. 위험 로그')
    if danger_lines:
        lines.extend(danger_lines)
    else:
        lines.append('- (없음)')
    lines.append('')
    lines.append('## 3. 추정 원인')
    lines.append(f'- {cause}')
    lines.append('')

    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f"마크다운 보고서 저장됨: {path}")
    except OSError as e:
        print(f"파일 저장 오류: {e}")

def filter_rows(rows, keyword: str | None) -> list[tuple[str, str, str]]:
    if not keyword:
        return rows
    k = keyword.lower()
    out = []
    for ts, event, msg in rows:
        if (k in ts.lower()) or (k in event.lower()) or (k in msg.lower()):
            out.append((ts, event, msg))
    return out
        
def main() -> None:
    rows = load_log()
    if not rows:
        print('출력할 데이터가 없습니다')
        return

    kw = input('검색 키워드(엔터=전체): ').strip()
    view = filter_rows(rows, kw)

    print('====검색결과===')
    print_log(view)

    print('====역순출력===')
    rev_view = list(reversed(view))
    print_log(rev_view)

    log_dict = rows_to_dict(list(reversed(rows)))
    save_to_json(log_dict)
    save_danger_logs(rows)
    write_markdown_report(rows)

if __name__ == "__main__":
    main()

