# === problem5_refactored.py ===
# * 카이사르 암호 복호화 문제 요건 반영 *
# - 영문 소문자만(reverse shift: index 26 -> 0) 변환, 그 외는 그대로 유지
# - 원문 텍스트는 상수(글로벌 전역변수)로 사용
# - chr((ord('a') 기준) ... % 26 + ord('a')) 형태의 전형식에 맞춤
# - 세부 요건 변동에 대응 가능하도록 방어적 검증 및 예외 처리 포함

SHIFT_NUMBERS = 26  # shift 개수(알파벳 26개)
CAESAR_PASSWORD_TEXT = 'b ehox Ftkl sdlkf alk sdklfn'  # #문제에따라명칭변경


def caesar_cipher_decode(text: str, reverse_order: bool = True) -> list[str]:
    """
    카이사르 복호화(소문자 a~z만 변환, 나머지는 유지).
    reverse_order=True이면 'index 26 -> 0' 순서로 결과를 나열(출제 복기 반영).

    반환: 길이 26 리스트(각 시프트에 대한 복호 문자열)
    예외: text가 str이 아니거나 빈 문자열이면 ValueError
    """
    # === 입력 유효성 검증 (채점기 대비) ===
    if not isinstance(text, str):
        raise ValueError
    if text == '':
        raise ValueError

    # index 진행 순서 결정: 26→0 요구사항을 그대로 반영
    # (일반적으로 0~25를 쓰지만, 문제 복기에서는 reverse shift 표기를 강조)
    indices = list(range(SHIFT_NUMBERS))
    if reverse_order:
        indices = indices[::-1]  # 25,24, ... , 0

    results: list[str] = []
    for idx in indices:
        # 전형식: chr((ord(char) - ord('a') + idx) % shift_numbers + ord('a'))
        #   - 여기서 idx를 '역시프트'에 대응시켜, 사람이 보는 관점(26→0)과 일치시키되
        #     실제 변환은 '소문자만', 나머지는 그대로 유지.
        decoded_chars: list[str] = []
        for ch in text:
            if 'a' <= ch <= 'z':
                # 소문자만 변환. 그 외(대문자/공백/구두점)는 그대로 둔다.
                base = ord('a')
                code = (ord(ch) - base + idx) % SHIFT_NUMBERS + base
                decoded_chars.append(chr(code))
            else:
                decoded_chars.append(ch)
        results.append(''.join(decoded_chars))

    return results


def main() -> None:
    try:
        # 1) 모든 시프트 결과 생성(26→0 순서)
        candidates = caesar_cipher_decode(CAESAR_PASSWORD_TEXT, reverse_order=True)

        # 2) 인덱스 라벨과 함께 출력: "{i}: {password}" (콜론 뒤 공백 1칸)
        #    * #예외처리상황에따라이렇게추가가능: 출력 포맷이 다르면 여기만 바꾸면 됨.
        for i, text in enumerate(candidates):
            print(f"{i}: {text}")

        # 3) 사용자 입력(정수/범위 0~25) — 프롬프트 문구가 정해지지 않은 시험 대비
        raw = input()
        s = raw.strip()
        if s == '':
            raise ValueError
        if not s.isdigit():   # 음수 기호/문자 섞임 등 방지
            raise ValueError

        idx = int(s)
        if not 0 <= idx <= 25:
            raise ValueError

        # 4) 결과 출력 (형식 엄수: "Result: {문자열}")
        print(f"Result: {candidates[idx]}")

    except ValueError:
        # 입력형식/범위/빈값 등 사용자 입력 오류
        print('invalid input.')
        return
    except Exception:
        # 그 밖의 모든 런타임 예외(환경/로직 등)
        print('error')
        return


if __name__ == '__main__':
    main()
