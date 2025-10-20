# === problem5seng.py ===
# 문제에서 주어진 암호문(카이사르 암호)을 아래 변수에 넣으세요.
CAESAR_PASSWORD_TEXT = 'b ehox Ftkl sdlkf alk sdklfn'  # #문제에따라명칭변경

def caesar_cipher_decode(text: str) -> list[str]:
    """
    카이사르 암호(소문자 a~z만 대상)를 모든 시프트(0~25)로 복호화한 결과 리스트를 반환.
    - 입력 유효성 검증 실패 시 ValueError를 명시적으로 발생시킵니다.
    """
    # === 입력 유효성 검증 ===
    if not isinstance(text, str):             # 타입 체크
        raise ValueError                      # 입력값 오류는 명시적으로 ValueError
    if text == '':                            # 빈 문자열 금지 (채점기 대비)
        raise ValueError

    results: list[str] = []
    for shift in range(26):                    # 0 ~ 25
        decoded = []
        for ch in text:
            if 'a' <= ch <= 'z':
                code = ord(ch) - shift
                if code < ord('a'):
                    code += 26
                decoded.append(chr(code))
            else:
                # 공백/구두점/대문자 등은 그대로 둠(문제 복기 기준)
                decoded.append(ch)
        results.append(''.join(decoded))
    return results


def main() -> None:
    try:
        # 1) 암호문 복호화 테이블 생성
        decode_passwords = caesar_cipher_decode(CAESAR_PASSWORD_TEXT)

        # 2) 0~25 라벨과 함께 전부 출력 (형식: "{i}: {password}")
        for i, password in enumerate(decode_passwords):
            print(f"{i}: {password}")

        # 3) 사용자 입력 받기 (정수 & 범위 0~25) - 모든 단계에서 명시적 ValueError 처리
        raw = input()                          # 프롬프트 문구 명시 없음(문제 기준)
        if not isinstance(raw, str):           # #예외처리상황에따라이렇게추가가능
            raise ValueError                   # (일반적으로 input은 str 반환이므로 방어적 처리)

        s = raw.strip()
        if s == '':                            # 공백만 입력
            raise ValueError
        if not s.isdigit():                    # 음수/기타 문자는 허용 안함(문제 범위 0~25)
            raise ValueError

        idx = int(s)                           # 숫자로 확정된 후 변환
        if not 0 <= idx <= 25:                 # 범위 벗어나면 명시적으로 ValueError
            raise ValueError

        # 4) 결과 출력 (형식 엄수: "Result: {문자열}")
        print(f"Result: {decode_passwords[idx]}")

    except ValueError:
        # 사용자 입력 오류(형식/범위/빈값/타입 등)는 모두 여기서 처리
        print('invalid input.')
        return
    except Exception:
        # 그밖의 모든 런타임 예외(내부 로직, 인덱스, 환경 등)
        print('error')
        return


if __name__ == '__main__':
    main()
