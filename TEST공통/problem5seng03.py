# problem5.py (int(input()) 예외처리 명시 강화 버전)
# 카이사르 암호 복호화 문제
# - 소문자만 역시프트(-i)
# - 출력: "i: {decoded}" / "Result: {decoded}"
# - 예외처리: ValueError → invalid input. / Exception → error
# - int(input()) 변환 실패 또는 범위 초과 시 ValueError 명시 발생

# 암호문 (문제에 따라 변경 가능)
CIPHER_TEXT = 'b ehox Ftkl sdlkf alk sdklfn'  # #문제에따라명칭변경


def caesar_cipher_decode(target: str) -> list[str]:
    """소문자만 역시프트(-i)하며, 공백/대문자/기호는 그대로 둔다."""
    if not isinstance(target, str):  # #예외처리상황에따라이렇게추가가능
        raise ValueError('input must be string')

    result_list: list[str] = []
    for i in range(26):
        decoded = []
        for ch in target:
            if 'a' <= ch <= 'z':
                shifted = (ord(ch) - ord('a') - i) % 26
                decoded.append(chr(ord('a') + shifted))
            else:
                decoded.append(ch)
        result_list.append(''.join(decoded))
    return result_list


def main():
    try:
        # 모든 복호화 결과 생성
        candidates = caesar_cipher_decode(CIPHER_TEXT)

        # i: {decoded} 형식으로 출력
        for i, decoded in enumerate(candidates):
            print(f"{i}: {decoded}")

        # --- 입력 및 int 예외처리 추가 영역 ---
        raw = input()  # 문제 조건: 별도 안내문구 없음
        # 문자열이 비었거나 숫자 아님 → ValueError 명시 발생
        if not raw.strip().isdigit():
            raise ValueError
        idx = int(raw.strip())

        # 인덱스 범위 벗어남 → ValueError 명시 발생
        if not 0 <= idx < 26:
            raise ValueError
        # -----------------------------------

        # 선택된 복호화 결과 출력
        print(f"Result: {candidates[idx]}")

    except ValueError:
        print('invalid input.')
        return
    except Exception:
        print('error')
        return


if __name__ == '__main__':
    main()
