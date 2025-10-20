from datetime import datetime

def read_log(path: str = "mission_computer_main.log")->str:
    try :
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except (FileNotFoundError, IOError):
        print("File Error")
    except UnicodeDecodeError:
        print("Decoding Error")
    except Exception as e:
        print(f"{e}")
    return ""

def main():
    result = read_log()
    print("============read_log=================")
    print(result)
    log_list = []
    try:
        # 헤더 확인: 형식 문제이므로 ValueError로 처리 (채점 메시지: Invalid log format.)
        if not result.startswith("timestamp,event,message"):
            raise ValueError

        for i, logs in enumerate(result.splitlines()[1:] , start=1):
            if not logs:
                continue
            parts = logs.strip().split(',', 2)

            try:
                if len(parts) == 3:
                    # 타임스탬프 형식 검증 실패 시 ValueError 발생 → Invalid log format.
                    if datetime.strptime(parts[0], '%Y-%m-%d %H:%M:%S'):
                        try:
                            log_list.append((parts[0].strip(), parts[2].strip()))
                        except RuntimeError:
                            # 처리 단계 오류는 RuntimeError 유지 → Processing error.
                            raise RuntimeError
                    else:
                        raise ValueError
                else:
                    raise ValueError
            except RuntimeError:
                raise RuntimeError

        print("============log_list=================")
        print(log_list)
        try:
            sorted_list = sorted(
                log_list,
                key=lambda x: x[0],
                reverse=True
            )
            print("============sorted_list=================")
            print(sorted_list)
            dict_list = dict(sorted_list)
            print("============dict_list=================")
            print(dict_list)
        except ValueError:
            # 정렬 과정에서의 형식 문제도 Invalid log format.로
            raise ValueError

    except (TypeError, ValueError):
        print('Invalid log format.')
    except RuntimeError:
        print('Processing error.')
    except Exception:
        # 기타 예외는 처리 단계 오류로 통일
        print("Processing error.")

if __name__ == "__main__":
    main()
