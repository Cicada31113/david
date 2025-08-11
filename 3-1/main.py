# main.py
import json
from datetime import datetime
from textwrap import fill
from collections import Counter

LOG_FILE = 'mission_computer_main.log'
JSON_FILE = 'mission_computer_main.json'
REPORT_FILE = 'log_analysis.md'
DANGER_FILE = 'danger_logs.log'
DT_FMT = '%Y-%m-%d %H:%M:%S'

# 위험 키워드(대소문자 무시 영어, 한글은 그대로 매칭)
DANGER_KEYWORDS_EN = ['explosion', 'leak', 'high temperature', 'oxygen', 'o2', 'fire', 'warning', 'danger']
DANGER_KEYWORDS_KO = ['폭발', '누출', '고온', '산소', '화재', '경고', '위험']


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
