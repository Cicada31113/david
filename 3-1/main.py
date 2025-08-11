# main.py
import json
from datetime import datetime
from textwrap import fill
from collections import Counter


# import json -> 파이썬 객체(dict, list)를 json 문자열/파일로 저장하거나, 그 반대로 읽어오는 도구를 가져옴
# from datetime import datetime  -> 문자열 타임스탬프 <> 시간객체 변환하고, 정렬/비교에 쓰려고 가져옴
# from textwrap import fill -> 너무 긴 문장을 콘솔 폭에 맞춰 자동 줄바꿈해 표처럼 예쁘게 보여주려고 씀
# from collection import Counter -> 이벤트 종류가 몇번 나왔는지 빠르게 세려고 빈도계산기(Counter)를 가져옴

LOG_FILE = 'mission_computer_main.log'
JSON_FILE = 'mission_computer_main.json'   # 정리된 결과를 딕셔너리 형태 {timestamp: message}로 저장할 json 파일이름
REPORT_FILE = 'log_analysis.md'       # 로그를 분석해서 만든 사고원인분석보고서를 마크다운으로 저장할 파일 이름
DANGER_FILE = 'danger_logs.log'       # 위험 키워드가 들어간 원문 로그 줄만 따로 모아서 저장할 파일 이름
DT_FMT = '%Y-%m-%d %H:%M:%S'          # 타임스탬프 문자열 형식 정의. 예:2023-08-27 10:00:00 같은 형태

# 위험 키워드(대소문자 무시 영어, 한글은 그대로 매칭)
DANGER_KEYWORDS_EN = ['explosion', 'leak', 'high temperature', 'oxygen', 'o2', 'fire', 'warning', 'danger']
DANGER_KEYWORDS_KO = ['폭발', '누출', '고온', '산소', '화재', '경고', '위험']


def read_lines(path: str) -> list[str]:        # path: str은 표지판 역할 / -> list[str]: 이 함수가 반환할 값이 어떤타입인지 알려주는 표시
    try:
        with open(path, 'r', encoding='utf-8') as f:   # with -> 컨텍스트 매니저 문법. 파일을 열고나면 블록이 끝날때 자동으로 close()해주는 안전장치.
            return f.read().splitlines()               # open -> 파이썬 내장함수 open()으로 파일 열기 / r은 읽기모드
    except FileNotFoundError:                         
        print(f'[에러] {path} 파일이 없습니다.')
        raise SystemExit(1)
    except UnicodeDecodeError:
        print(f'[에러] {path} 파일의 인코딩이 UTF-8이 아닙니다.')
        raise SystemExit(1)
    
#     ➡️ 하는 일:
# 1) path(파일 경로)에 있는 파일을 읽어.
# 2) UTF-8로 읽어서, 파일 전체 내용을 줄 단위로 잘라서 리스트로 반환해.
#    예: ["2023-08-27 10:00:00,INFO,메시지", "2023-08-27 10:02:00,INFO,메시지", ...]
# 3) 만약 파일이 없으면(FileNotFoundError) "[에러] ~파일이 없습니다." 찍고 프로그램을 끝내.
# 4) UTF-8이 아니면(UnicodeDecodeError) "[에러] UTF-8이 아닙니다." 찍고 프로그램을 끝내.

# 💡 한마디로:  
# "로그 파일을 줄 단위로 읽어서 리스트로 내놓는 역할. 파일 없거나 인코딩 틀리면 즉시 종료."


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


def sort_rows_by_time(rows_ts_msg: list[tuple[str, str]] | list[tuple[str, str, str]],
                      ts_index: int = 0) -> None:
    try:
        rows_ts_msg.sort(
            key=lambda x: datetime.strptime(x[ts_index], DT_FMT),
            reverse=True
        )
    except ValueError:
        rows_ts_msg.sort(key=lambda x: x[ts_index], reverse=True)


def detect_danger(msg: str) -> bool:
    low = msg.lower()
    if any(k in low for k in DANGER_KEYWORDS_EN):
        return True
    return any(k in msg for k in DANGER_KEYWORDS_KO)


def write_danger_file(lines: list[str]) -> None:
    # 헤더 제거 후 원문 라인 기준 필터링
    start_idx = 1 if lines and lines[0].lower().startswith('timestamp') else 0
    danger_lines = [ln for ln in lines[start_idx:] if detect_danger(ln)]
    try:
        with open(DANGER_FILE, 'w', encoding='utf-8') as f:
            for ln in danger_lines:
                f.write(ln + '\n')
        print(f'[완료] 위험 키워드 로그 저장: {DANGER_FILE} (총 {len(danger_lines)}건)')
    except OSError as e:
        print(f'[에러] 위험 로그 저장 실패: {e}')
        raise SystemExit(1)


def build_stats(data_rows: list[tuple[str, str, str]]) -> dict:
    events = [ev for _ts, ev, _msg in data_rows]
    counts = Counter(events)
    first_ts = data_rows[-1][0] if data_rows else ''
    last_ts = data_rows[0][0] if data_rows else ''
    danger_hits = [(ts, ev, msg) for ts, ev, msg in data_rows if detect_danger(msg)]
    last_abnormal = next((r for r in data_rows if detect_danger(r[2])), None)
    return {
        'event_counts': counts,
        'first_ts': first_ts,
        'last_ts': last_ts,
        'danger_hits': danger_hits,
        'last_abnormal': last_abnormal,
    }


def infer_cause(stats: dict) -> str:
    # 단순 규칙 기반 추론(로그가 부족하면 보수적 결론)
    danger_msgs = [m for _t, _e, m in stats['danger_hits']]
    text_blob = ' '.join(danger_msgs).lower()

    if 'explosion' in text_blob or '폭발' in text_blob:
        return '추정: 추진체/연료계 폭발 또는 압력계통 이상으로 인한 급격한 파손.'
    if ('oxygen' in text_blob or 'o2' in text_blob or '산소' in text_blob) and ('누출' in text_blob or 'leak' in text_blob):
        return '추정: 산소 계통(O2) 누출로 인한 산화성 환경 위험 증대.'
    if 'high temperature' in text_blob or '고온' in text_blob:
        return '추정: 열관리(냉각) 실패로 인한 온도 급상승.'
    if 'leak' in text_blob or '누출' in text_blob:
        return '추정: 유체/가스 계통 누출.'
    if 'fire' in text_blob or '화재' in text_blob:
        return '추정: 국부 화재 발생.'
    if stats['danger_hits']:
        return '추정: 위험 신호 다수 감지. 구체 원인 식별엔 추가 로그 필요.'
    return '원인 단서 부족. 추가 로그/센서 데이터 필요.'


def write_markdown_report(data_rows: list[tuple[str, str, str]]) -> None:
    stats = build_stats(data_rows)
    cause = infer_cause(stats)

    def fmt_event_counts(c: Counter) -> str:
        if not c:
            return '- (없음)'
        return '\n'.join(f'- {k}: {v}건' for k, v in c.most_common())

    def fmt_danger_hits(hits: list[tuple[str, str, str]]) -> str:
        if not hits:
            return '> 위험 키워드 포함 로그 없음'
        lines = []
        for ts, ev, msg in hits[:30]:  # 리포트는 최대 30줄만
            lines.append(f'- **{ts}** [{ev}] {msg}')
        if len(hits) > 30:
            lines.append(f'- ...외 {len(hits) - 30}건')
        return '\n'.join(lines)

    md = []
    md.append('# 사고 원인 분석 보고서')
    md.append('')
    md.append('> 본 문서는 미션 로그를 기반으로 단순 규칙에 따라 사고 원인을 **추정**합니다. '
              '정밀 진단을 위해서는 원시 센서 데이터와 추가 로그가 필요합니다.')
    md.append('')
    md.append('## 1. 개요')
    md.append(f'- 분석 대상 파일: `{LOG_FILE}`')
    md.append(f'- 총 레코드 수(헤더 제외): {len(data_rows)}')
    md.append(f'- 기간: {stats["first_ts"] or "-"} ~ {stats["last_ts"] or "-"}')
    md.append('')
    md.append('## 2. 이벤트 통계')
    md.append(fmt_event_counts(stats['event_counts']))
    md.append('')
    md.append('## 3. 위험 신호 감지')
    md.append(fmt_danger_hits(stats['danger_hits']))
    md.append('')
    md.append('## 4. 추정 사고 원인')
    md.append(f'- {cause}')
    md.append('')
    md.append('## 5. 권고 조치')
    md.append('- 관련 계통 압력/온도/가스 농도 센서 로그 추가 수집')
    md.append('- 이상 징후 발생 직전의 커맨드/상태 전이 확인(타임라인 교차검증)')
    md.append('- 동일 키워드 재발 여부 모니터링 강화')
    md.append('')
    md.append('---')
    md.append('_Markdown 규격: markdownguide.org 준수_')

    try:
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md) + '\n')
        print(f'[완료] 사고 분석 보고서 저장: {REPORT_FILE}')
    except OSError as e:
        print(f'[에러] 보고서 저장 실패: {e}')
        raise SystemExit(1)


def prompt_search(json_path: str) -> None:
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            log_dict: dict[str, str] = json.load(f)
    except FileNotFoundError:
        print(f'[알림] {json_path} 가 없어 검색을 건너뜁니다.')
        return
    except (json.JSONDecodeError, UnicodeDecodeError):
        print(f'[알림] {json_path} 가 올바른 UTF-8 JSON이 아닙니다.')
        return

    term = input('\n[검색] mission_computer_main.json 에서 찾을 문자열(엔터면 건너뜀): ').strip()
    if not term:
        print('[검색] 건너뜀')
        return

    low_term = term.lower()
    matches = [(ts, msg) for ts, msg in log_dict.items()
               if low_term in ts.lower() or low_term in msg.lower()]

    # 시간 역순 정렬 후 출력
    try:
        matches.sort(key=lambda x: datetime.strptime(x[0], DT_FMT), reverse=True)
    except ValueError:
        matches.sort(key=lambda x: x[0], reverse=True)

    print('\n=== 검색 결과 ===')
    if not matches:
        print('(없음)')
        return
    for ts, msg in matches:
        print(f'- {ts} :: {msg}')


def main() -> None:
    # 1) 로그 읽기
    lines = read_lines(LOG_FILE)

    # 빈 파일 가드
    if not lines:
        print('=== 로그 원본 ===')
        print('[알림] 로그 파일이 비어 있습니다.')
        print('\n=== 리스트 객체 (raw list) ===')
        print([])
        print('\n=== 시간 역순 정렬 리스트 (raw list) ===')
        print([])
        print('\n=== Dict 객체 (pretty JSON) ===')
        print('{}')
        # 비어 있어도 산출물은 생성
        try:
            with open(JSON_FILE, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
            with open(REPORT_FILE, 'w', encoding='utf-8') as f:
                f.write('# 사고 원인 분석 보고서\n\n> 로그가 비어 있어 분석할 수 없습니다.\n')
            with open(DANGER_FILE, 'w', encoding='utf-8') as f:
                f.write('')
        except OSError as e:
            print(f'[에러] 산출물 저장 실패: {e}')
            raise SystemExit(1)
        return

    # 2) 원본 전체 출력
    print('=== 로그 원본 ===')
    for line in lines:
        print(line)

    # 3) 파싱
    data_rows: list[tuple[str, str, str]] = []
    start_idx = 1 if lines and lines[0].lower().startswith('timestamp') else 0
    for line in lines[start_idx:]:
        parsed = parse_csv_line(line)
        if parsed:
            data_rows.append(parsed)

    # 과제 요건 리스트[(timestamp, message)]
    log_list: list[tuple[str, str]] = [(ts, msg) for ts, _ev, msg in data_rows]

    # 출력(리스트 / 표)
    print('\n=== 리스트 객체 (raw list) ===')
    print(log_list)
    if data_rows:
        print('\n=== 리스트 객체 (표 형태) ===')
        print(pretty_table(data_rows))

    # 4) 시간 역순 정렬
    sort_rows_by_time(log_list, ts_index=0)
    sort_rows_by_time(data_rows, ts_index=0)

    print('\n=== 시간 역순 정렬 리스트 (raw list) ===')
    print(log_list)
    if data_rows:
        print('\n=== 시간 역순 정렬 리스트 (표 형태) ===')
        print(pretty_table(data_rows))

    # 5) Dict 변환
    log_dict: dict[str, str] = {ts: msg for ts, msg in log_list}

    # 6) 화면에 pretty JSON
    print('\n=== Dict 객체 (pretty JSON) ===')
    print(json.dumps(log_dict, ensure_ascii=False, indent=2))

    # 7) JSON 파일 저장
    try:
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(log_dict, f, ensure_ascii=False, indent=2)
        print(f'\n[완료] JSON 저장: {JSON_FILE}')
    except OSError as e:
        print(f'[에러] JSON 저장 실패: {e}')
        raise SystemExit(1)

    # 3. 사고 원인 분석 보고서 작성 (Markdown)
    write_markdown_report(data_rows)

    # 4-1. 위험 키워드 필터 파일 저장
    write_danger_file(lines)

    # 4-2. JSON 대상 검색 기능
    prompt_search(JSON_FILE)


if __name__ == '__main__':
    main()



# 1. UTF-8이란?   (Unicode TransFormation Format)
# 컴퓨터가 문자를 저장하는 방법(문자 인코딩 방식) 중 하나야.
# 사람은 A, 가 처럼 글자를 그대로 보지만, 컴퓨터는 글자를 숫자로 저장함.
# "어떤 글자를 어떤 숫자로 표현할지" 정해놓은 규칙이 문자 인코딩이야.

# 2. UTF-8의 특징
# 유니코드(Unicode) 체계의 한 방식.
# 전 세계 모든 문자(한글, 영어, 이모지 등)를 표현 가능.
# 영어/숫자는 1바이트, 한글은 3바이트, 이모지는 4바이트로 저장.
# 지금 인터넷, 웹, JSON, 파이썬 기본 등 대부분이 UTF-8을 표준으로 씀.

# 3. 왜 중요하냐?
# 파일이 UTF-8로 저장돼 있으면, 한글/영어 섞여도 깨지지 않고 읽을 수 있음.
# 만약 다른 인코딩(EUC-KR, CP949 등)으로 저장된 파일을 UTF-8로 읽으려고 하면 문자 깨짐(�) 현상 발생.
                                                          
# 문자:  A   가   😀
# 숫자: 65  44032  128512   (유니코드 번호)
# UTF-8 저장 시:
#  A → 41          (16진수, 1바이트)
#  가 → EA B0 80   (3바이트)
#  😀 → F0 9F 98 80 (4바이트)

                    # retrun f.read().splitlines()
                    # 파일 내용을 전부 읽어서, 줄 단위로 잘라 리스트로 만든 뒤 함수 밖으로 돌려준다.
# f.read()
# -> open()으로 연 파일 객체 f에서 파일 전체 내용을 하나의 긴 문자열로 읽음.
# 예: 파일에 두 줄이 있으면 "첫째줄\n둘째줄" 이런식으로 반호나

# .splitlines()
# -> 문자열을 줄바꿈 (\n,\r\n) 기준으로 잘라서 리스트로 만듦.
# -> 줄 끝의 줄바꿈 문자는 제거됨.
# -> 예: "a\nb\nc".splitline() -> ['a', 'b', 'c']

                     # except FileNotFoundError:
                     # 파이썬이 파일을 열려고 했는데, 해당 경로에 파일이 없을 때 발생하는 내장 예외 클래스.

# 예: open("없는파일.txt", "r")
# # FileNotFoundError: [Errno 2] No such file or directory: '없는파일.txt'
             
                     # raise SystemExit(1)
                     # 이 시점에서 프로그램을 바로 종료시키고, 상태 코드는 1(에러)로 남긴다.
                    
# raise -> 파이썬에서 예외(에러)를 강제로 발생시키는 키워드 
# 여기서는 SystemExit(1) 예외를 발생시킴.

# SystemExit -> 프로그램을 즉시 종료시키는 특수한 예외 클래스.
# 보통 sys.exit() 함수를 써도 같은 효과지만, 여기선 직접 예외를 발생시키는 방식으로 종료함.

# (1) -> 종료 코드 (exit status code).
# 0 -> 정상 종료 // 1(혹은 0이 아닌값)-> 비정상 종료, 에러상태
# 운영체제나 다른 프로그램이 이 값을 보고 "성공인지 실패인지" 판단할 수 있음.
# 예: raise SystemExit(1) -> 프로그램 바로 종료, 이후 코드 실행 안됨.

                      # except UnicodeDecodeError:
                      # UTF-8로 읽으려다 인코딩이 달라서 깨진 경우를 잡아 처리한다.

# 파일을 읽을 때 인코딩 방식이 안 맞아서 문자를 해석(decode)하지 못하면 발생하는 예외.
# 예: 파일이 EUC-KR로 저장돼 있는데 encoding='utf-8'로 열면 발생.
# "이 바이트(숫자조합)를 UTF-8 문자로 바꿀 수 없다"는 의미

                      # def parse_csv_line(line: str) -> tuple[str, str, str] | None:
                      # "line"이라는 문자열을 받아서, 정상적인 csv면 문자열 3개짜리 튜플을 주고, 아니면 None을 준다.
                      
# tuple[str, str, str] | None
# 반환값이 (문자열, 문자열, 문자열) 구조의 튜플이거나(None), 잘못된 형식이면 None을 반환한다는 뜻
# ' | ' 는 union 의미, "이 타입이거나 저 타입"이라는 뜻 (파이썬 3.10+ 문법)

# 튜플(tuple) 이란?
# 여러 값을 하나의 묶음으로 저장하는 자료형.
# 리스트(list)와 비슷하지만, 한 번 만들면 수정할 수 없음(불변, immutable)
# 소괄호 () 로 묶어서 표ㅗ현.
# 요소들은 순서가 있고, 인덱스로 접근 가능
# 예:
# person = ("덕현", 31, "개발자")
# print(person[0])  # "덕현"
# print(person[1])  # 31
# 여기서 person은 3개의 값이 순서대로 들어있는 튜플
# "덕현"은 인덱스 0, 31은 인덱스 1, "개발자"는 인덱스 2.

# | 특징      | 리스트(list)         | 튜플(tuple)                 |
# | -------- | ------------- ---   | ---------  ----    ------- |
# | 기호      | []                  |   ()                       |
# | 수정 가능? | 가능                 |   불가능                    |
# | 속도      | 보통                 |   약간 빠름                  |
# | 용도      | 바뀔 수 있는 데이터 모음 | 바뀌면 안 되는 고정 데이터 모음 |


                         # parts = line.strip().split(',', 2)

# line.strip()
# -> strip() 메서드는 문자열 양쪽에 있는 공백, 탭(\t), 줄바꿈(\n) 같은 여백문자 제거.

#.split(',', 2)
# split(구분자, 최대분할횟수) -> 문자열을 구분자를 기준으로 나눠서 리스트로 반환
# 예:"2023-08-27 10:00:00,INFO,Rocket, start".split(',', 2)
# ['2023-08-27 10:00:00', 'INFO', 'Rocket, start']

                          # if len(parts) != 3:

# if -> 조건문. 뒤의 조건이 참(True)이면, 바로 아래 들여쓴 코드 블록을 실행.
# len(parts) -> parts 리스트 안의 요소 개수를 구함.

# !=3 
# != -> "같지않다" 비교 연산자
# len(parts) != 3   -> 리스트 길이가 3이 아니면 True
# 여기서 3을 기준으로 삼는건, 이 함수에서 CSV 한줄을 timestamp, event, message 딱 3부분으로 나누는게 목표
# 만약 3개가 아니면, 잘못된 형식이라는 뜻.

                        # ts, event, msg = (p.strip() for p in parts)

# ts, event, msg =
# 튜플/리스트 언패킹(unpacking)문법.
# 오른쪽에 있는 값(여기선 3개의 문자열)을 순서대로 왼쪽 변수 3개에 나눠 담음.
# 예:
# a, b = [1, 2]  
# a = 1, b = 2

# (p.strip() for p in parts)
# for p in parts -> parts 리스트에서 요소를 하나씩 꺼내서 p에 담음.
# (... for... in...) -> 제너레이터 표현식(generator expression).
# -> 리스트 [] 대신 소괄호()를 쓰면 메모리에 전부 올리지 않고 순서대로 처리.

#  리스트 표현식                  -> 모든 결과를 한 번에 만들어서 메모리에 저장 / 바로 인덱스로 접근가능
# [x * 2 for x in range(5)]  
# # → [0, 2, 4, 6, 8]

#  제너레이터 표현식               -> 필요할 때 하나씩 만들어서 전달 // 한번 소비하면 다시 못씀(순서대로만 사용)
# (x * 2 for x in range(5))  
#  → 제너레이터 객체 하나를 만듦


                          # if not ts or not msg:

# not ts
# not -> 부정 연산자. 값이 비어있거나(False로 평가되면) 참이 됨.
# 문자열의 경우: 
#   - 비어있으면 False 로 취급됩 -> not "" -> True
#   - 내용이 있으면 True로 취급됨 -> not "abc" -> False
# 즉