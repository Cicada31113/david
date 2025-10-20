# problem5.py  (refined)

# [중요] 시험지에 나온 원문 문자열을 아래 상수에 '그대로' 넣어 사용하세요.
CAESAR_PASSWORD_TEXT = 'b ehox Ftkl sdlkf alk sdklfn'  # 예시용. 실제 시험 문자열로 교체 필수.


def caesar_cipher_decode(text):
    """
    0~25까지 모든 시프트(복호화: 왼쪽으로 i칸)를 적용해 26개의 후보 문자열을 반환합니다.
    - 영문 소문자('a'~'z')에만 시저 시프트 적용
    - 공백/구두점/대문자 등은 원형 유지
    """
    # 타입 안전장치 (시험 채점에는 보통 영향 없지만, 요청대로 예외처리 보강)
    if not isinstance(text, str):
        raise TypeError("text must be str")

    candidates = []
    base = ord('a')

    for i in range(26):  # 0..25 (인덱스와 출력 번호 일치)
        decoded_chars = []
        for ch in text:
            if 'a' <= ch <= 'z':
                # 복호화: 암호화가 +i였다면 복호화는 -i
                idx = (ord(ch) - base - i) % 26
                decoded_chars.append(chr(base + idx))
            else:
                decoded_chars.append(ch)
        candidates.append(''.join(decoded_chars))

    return candidates


def main():
    try:
        decode_passwords = caesar_cipher_decode(CAESAR_PASSWORD_TEXT)

        # 형식: "{i}: {password}"  (콜론 뒤 공백 1칸 유지)
        for i, password in enumerate(decode_passwords):
            print(f"{i}: {password}")

        # 입력 프롬프트 문구 없이 정수만 입력
        choice = int(input())

        # 범위 검증(0~25)
        if not 0 <= choice <= 25:
            raise ValueError

        # 형식: "Result: {선택_문자열}"  (콜론 뒤 공백 1칸 유지)
        print(f"Result: {decode_passwords[choice]}")

    except ValueError:
        # 정수가 아니거나, 정수여도 범위를 벗어난 경우
        print("invalid input.")
        return
    except Exception:
        # 그 외 모든 예외
        print("error")
        return


if __name__ == '__main__':
    main()
