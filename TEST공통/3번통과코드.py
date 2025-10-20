def read_log(path:str='mission_computer_main.log') -> str:
    """원문을 읽어 문자열로 변환한다"""
    try:
        with open(path,'r',encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise
    except UnicodeDecodeError:
        raise
    except Exception:
        raise

def log_to_tuple(log):
    raw_data = log.strip()
    logs = raw_data.split('\n')

    if logs[0] != 'timestamp,event,message':
        raise ValueError
    
    pairs = []
    for line in logs[1:]:
        if line.strip():
            parts = line.split(',', 2)
            if len(parts) != 3:
                raise ValueError
            if len(parts[0]) != 19:
                raise ValueError
            pairs.append((parts[0], parts[2]))
    return pairs

def sort_log(tuples):
    return sorted(tuples, key=lambda x: x[0], reverse=True)

def log_to_dict(tuples):
    result = {}
    for timestamp, message in tuples:
        result[timestamp] = message
    return result

def main():
    try:
        log = read_log()
        print(log)

        tuples = log_to_tuple(log)
        print(tuples)

        sorted_tuples = sort_log(tuples)
        print(sorted_tuples)

        dict_log = log_to_dict(sorted_tuples)
        print(dict_log)

    except FileNotFoundError:
        print('File open error.')
        return
    except UnicodeDecodeError:
        print('Decoding error.')
        return
    except ValueError:
        print('Invalid log format.')
        return
    except Exception:
        print('Processing error.')
        return
    
if __name__ == '__main__':
    main()