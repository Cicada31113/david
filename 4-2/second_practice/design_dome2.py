# ====================== 여기부터 '건들지 말라' 한 블록: 그대로 유지 ======================
#---------------------------------------------------------------------------------------
# 경로/압축
#---------------------------------------------------------------------------------------
import os, zipfile, csv, pickle, math
import numpy as np  # 문제 3에서만 사용 (그 외 외부 패키지 사용 금지)

zip_dir = os.path.dirname(os.path.realpath(__file__))
zip_path = os.path.join(zip_dir, 'mars_base.zip') 

def unzip_file(zip_dir, zip_path):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zips:      # ZIP파일 열거얌
            zips.extractall(zip_dir)                  # extractall() : 압축해제
            print('압축해제 완료했지렁')
    
    except FileNotFoundError:
        print('파일이 없는데 ?')
    except zipfile.BadZipFile:
        print('zip파일이 좀 이상한가봐 ?')

# from pathlib import Path
# folder_path = Path(zip_path).parent  이런식으로 폴더위치 지정해도됨


#---------------------------------------------------------------------------------------
# 문제 1. 인벤토리 csv/이진 처리
#---------------------------------------------------------------------------------------
#이진파일은 포맷자체가 지정되어있지 않은 상태여서 이후에 내가 어떤 유틸리티설정을 하느냐에 따라 달라질 수 있다.

def read_csv(filename):
    out1 = []
    try:
        with open (filename, 'r', encoding='utf-8') as f:
            header = f.readline().strip().split(',')
            print('HEADER:',', '.join(header))
            if not header:
                return header, out1
            
            for line in f:
                parts = line.strip().split(',')
                if len(parts) != 5:
                    print('잘못된 것 같은데?')
                    continue
                out1.append(parts)
        return header, out1
    
    except FileNotFoundError:
        print('파일이 없는데 ?')
        return [], []          # header, out1 값 내놓는게 이 함수니까 문제발생시 빈리스트값 보여주자는거
    except Exception as e:
        print('뭔가 문제가 있는 것 같은데?', e)
        return [], []


def write_csv(header, data, filename):
    try:
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for row in data:
                row[-1] = f"{float(row[-1]): .3f}"      # 인화성 지수(마지막 열) 소수점 3자리 고정
                writer.writerow(row)            
        print(f'{filename} 파일 저장 완료되었습니다')
    except OSError as e:
        print(f'파일 저장 오류: {e}')


def write_binary(data, filename):
    try:
        with open(filename, 'wb') as f:
            pickle.dump(data, f)
        print(f'{filename} 이진 파일 저장했다오')
    except OSError as e:
        print(f'이진 파일 저장 오류: {e}')

def read_binary(filename):
    try:
        with open(filename, 'rb') as f:
            return pickle.load(f)
    except OSError as e:
        print(f'이진 파일 읽기 오류: {e}')
        return []   # 이거 추가됨
# ====================== 여기까지 원본 블록 ======================


# ====================== 여기부터 리팩토링 (요건 정합) ======================

# ---- 상수/전역 ----
INVENTORY_SRC = os.path.join(zip_dir, 'Mars_Base_Inventory_List.csv')
INVENTORY_SORTED = os.path.join(zip_dir, 'Mars_Base_Inventory_List_sorted.csv')
INVENTORY_DANGER = os.path.join(zip_dir, 'Mars_Base_Inventory_danger.csv')
INVENTORY_BIN = os.path.join(zip_dir, 'Mars_Base_Inventory_List.bin')

PARTS_FILES = [
    os.path.join(zip_dir, 'mars_base_main_parts-001.csv'),
    os.path.join(zip_dir, 'mars_base_main_parts-002.csv'),
    os.path.join(zip_dir, 'mars_base_main_parts-003.csv'),
]
PARTS_TO_WORK_ON = os.path.join(zip_dir, 'parts_to_work_on.csv')
PARTS3_CSV = os.path.join(zip_dir, 'parts3.csv')

DENSITY_G_CM3 = {  # g/cm^3
    'glass': 2.4,
    'aluminum': 2.7,
    'carbon_steel': 7.85,
}
G_EARTH = 9.80665
MARS_G_RATIO = 0.38


# ---------- 문제 1: 인벤토리 파이프라인(표준 라이브러리만) ----------
def task1_inventory():
    header, rows = read_csv(INVENTORY_SRC)
    if not header or not rows:
        print('인벤토리: 읽을 데이터가 없어.')
        return

    # 1) 화면 출력 (원본)
    print('\n[원본 데이터]')
    print(', '.join(header))
    for r in rows[:10]:
        print(', '.join(r))
    if len(rows) > 10:
        print(f'... 총 {len(rows)}행')

    # 2) 인화성 지수(float) 기준 내림차순 정렬
    try:
        sorted_rows = sorted(rows, key=lambda r: float(r[-1]), reverse=True)
    except ValueError:
        print('인화성 지수 파싱 실패. CSV 숫자 형식을 확인해줘.')
        return

    # 저장
    write_csv(header, sorted_rows, INVENTORY_SORTED)

    print('\n[정렬된 상위 10개]')
    print(', '.join(header))
    for r in sorted_rows[:10]:
        front = r[:-1]
        last = float(r[-1])
        print(', '.join(front + [f'{last:.3f}']))

    # 3) 필터: flammability index >= 0.7
    danger_rows = []
    for r in sorted_rows:
        try:
            if float(r[-1]) >= 0.7:
                danger_rows.append(r[:])
        except ValueError:
            continue

    print('\n[인화성 지수 >= 0.7 목록(상위 10개 프리뷰)]')
    print(', '.join(header))
    for r in danger_rows[:10]:
        front = r[:-1]
        last = float(r[-1])
        print(', '.join(front + [f'{last:.3f}']))
    if len(danger_rows) > 10:
        print(f'... 총 {len(danger_rows)}행')

    write_csv(header, danger_rows, INVENTORY_DANGER)

    # 4) 보너스: 이진 저장 → 재로드 출력
    write_binary(sorted_rows, INVENTORY_BIN)
    loaded = read_binary(INVENTORY_BIN)
    if loaded:
        print('\n[이진 재로드 샘플 3행]')
        for r in loaded[:3]:
            try:
                front = r[:-1]
                last = float(r[-1])
                print(', '.join(front + [f'{last:.3f}']))
            except Exception:
                print(', '.join(r))

    explain_text_vs_binary()


def explain_text_vs_binary():
    print('\n[텍스트 vs 이진: 요약]')
    print('- 텍스트(CSV): 사람이 읽기 쉬움, diff에 유리, 이식성 좋음. 대신 용량/파싱비용↑, 타입 정보는 문자열뿐.')
    print('- 이진(pickle 등): 저장/로드 빠름, 타입 보존. 대신 사람이 못 읽고, 파이썬 버전/환경 의존 가능.')


# ---------- 문제 2: 돔 표면적/무게 (반복 실행 + 예외 처리) ----------
def sphere_area():
    try:
        d_in = input('diameter(m: meter): ').strip()
        diameter_m = float(d_in)
        if diameter_m <= 0:
            raise ValueError('지름은 0보다 커야 해.')

        material = input('material(glass/aluminum/carbon_steel): ').strip().lower()
        if material not in DENSITY_G_CM3:
            raise ValueError('재질은 glass/aluminum/carbon_steel 중 하나여야 해.')

        t_in = input('thickness(cm, 기본=1): ').strip()
        thickness_cm = 1.0 if (t_in == '' or t_in is None) else float(t_in)
        if thickness_cm <= 0:
            raise ValueError('두께는 0보다 커야 해.')

        # 반구 곡면적: 2πr^2
        r = diameter_m / 2.0
        surface_area_m2 = 2.0 * math.pi * (r ** 2)

        # 얇은 껍질 부피 ≈ 면적 × 두께
        thickness_m = thickness_cm / 100.0
        volume_m3 = surface_area_m2 * thickness_m

        # g/cm^3 → kg/m^3 변환(×1000)
        density_kg_m3 = DENSITY_G_CM3[material] * 1000.0
        mass_kg = volume_m3 * density_kg_m3

        # 화성 무게(N) = m × g(지구) × 0.38
        weight_on_mars_N = mass_kg * G_EARTH * MARS_G_RATIO

        print(f'재질 ⇒ {material}, 지름 ⇒ {diameter_m:.3f}, 두께 ⇒ {thickness_cm:.3f}, 면적 ⇒ {surface_area_m2:.3f}, 무게 ⇒ {weight_on_mars_N:.3f} N')
        print(f'(참고) 질량 ⇒ {mass_kg:.3f} kg')

        # 예시 포맷(kg 유사) 병기 옵션
        weight_kgf_mars = mass_kg * 0.38
        print(f'무게(화성, kgf 유사값) ⇒ {weight_kgf_mars:.3f} kg')

    except ValueError as e:
        print(f'입력값 오류: {e}')


def task2_dome_loop():
    while True:
        sphere_area()
        again = input('계속 계산할까? (y=계속 / 기타=종료): ').strip().lower()
        if again != 'y':
            break


# ---------- 문제 3: NumPy 활용(배열 병합/평균/필터/저장/전치) ----------
# 헤더가 'parts/strength'가 아닐 수도 있으니, 이름/공백/BOM을 모두 흡수하는 로더
def _load_parts_file(fp: str):
    """
    반환: (names: np.ndarray[str], strengths: np.ndarray[float])
    실패/빈파일: (None, None)
    """
    try:
        # 1) 먼저 names=True 시도 (autostrip으로 공백 제거)
        arr = np.genfromtxt(fp, delimiter=',', names=True, dtype=None, encoding='utf-8', autostrip=True)
        if arr.size != 0 and arr.dtype.names:
            colnames = [c.strip().lower().replace(' ', '') for c in arr.dtype.names]
            # 'part' 혹은 'parts' 포함된 첫 컬럼, 'strength' 포함된 첫 컬럼 찾기
            try:
                idx_name = next(i for i, c in enumerate(colnames) if 'part' in c)
                idx_strength = next(i for i, c in enumerate(colnames) if 'strength' in c)
                # 단일행/다중행 모두 대응
                if arr.ndim == 0:
                    names = np.array([str(arr[arr.dtype.names[idx_name]])], dtype=str)
                    strengths = np.array([float(arr[arr.dtype.names[idx_strength]])], dtype=float)
                else:
                    names = arr[arr.dtype.names[idx_name]].astype(str)
                    strengths = arr[arr.dtype.names[idx_strength]].astype(float)
                return names, strengths
            except StopIteration:
                pass  # 이름 못찾으면 아래 raw 파싱으로 폴백

        # 2) 폴백: 헤더 한 줄 읽고, raw 본문은 위치기반(0,1)으로 파싱
        with open(fp, 'r', encoding='utf-8') as f:
            first = f.readline()  # 헤더는 버림
        raw = np.genfromtxt(fp, delimiter=',', skip_header=1, dtype=str, encoding='utf-8')
        if raw.size == 0:
            return None, None
        if raw.ndim == 1:
            raw = raw.reshape(1, -1)

        # 최소 2열 보장 가정: 0열=이름, 1열=수치
        names = raw[:, 0].astype(str)
        strengths = raw[:, 1].astype(float)
        return names, strengths

    except Exception:
        return None, None


def task3_parts_with_numpy():
    names_all_list = []
    vals_all_list  = []

    # 1) 세 파일을 읽어 arr1/arr2/arr3 역할로 수집 (이름/값)
    for fp in PARTS_FILES:
        names, strengths = _load_parts_file(fp)
        if names is None or strengths is None or names.size == 0:
            print(f'파일 내용이 비어있거나 헤더 인식 실패: {fp}')
            continue
        names_all_list.append(names)
        vals_all_list.append(strengths)

    if not names_all_list:
        print('읽어온 부품 데이터가 없어.')
        return

    # 2) 병합 → parts
    names_all = np.concatenate(names_all_list).astype(str)
    vals_all  = np.concatenate(vals_all_list).astype(float)

    # 3) 항목별 평균
    uniq, inv = np.unique(names_all, return_inverse=True)
    sums   = np.bincount(inv, weights=vals_all, minlength=len(uniq))
    counts = np.bincount(inv, minlength=len(uniq))
    means  = sums / counts

    # 4) 평균 < 50 필터링 → 저장(3자리)
    mask = means < 50.0
    work_names = uniq[mask]
    work_means = means[mask]

    try:
        with open(PARTS_TO_WORK_ON, 'w', encoding='utf-8', newline='') as f:
            w = csv.writer(f)
            w.writerow(['part', 'mean_strength'])
            for n, m in zip(work_names, work_means):
                w.writerow([n, f'{m:.3f}'])
        print('parts_to_work_on.csv 저장 완료')
    except OSError as e:
        print(f'parts_to_work_on.csv 저장 오류: {e}')
        return

    # 5) 보너스: 다시 읽어 parts2 → 전치해서 parts3 저장 + 프리뷰
    try:
        raw = np.genfromtxt(PARTS_TO_WORK_ON, delimiter=',', skip_header=1, dtype=str, encoding='utf-8')
        if raw.size == 0:
            print('parts_to_work_on.csv 가 비어 있어서 전치할 데이터가 없어.')
            np.savetxt(PARTS3_CSV, np.empty((0, 0), dtype=str), fmt='%s', delimiter=',')
            return

        if raw.ndim == 1:
            raw = raw.reshape(1, -1)
        parts2 = raw
        np.savetxt(os.path.join(zip_dir, 'parts2.csv'), parts2, fmt='%s', delimiter=',', encoding='utf-8')
        parts3 = parts2.T
        np.savetxt(PARTS3_CSV, parts3, fmt='%s', delimiter=',')
        print('parts3.csv 저장 완료 (parts_to_work_on 전치)')

        print('\n[parts3 프리뷰(상위 5행)]')
        for row in parts3[:5]:
            print(', '.join(row))
    except OSError as e:
        print(f'parts3 처리 오류: {e}')


# ---------- 메인 루프 ----------
def main():
    # 선택: zip이 있으면 풀어주기
    if os.path.exists(zip_path):
        unzip_file(zip_dir, zip_path)

    while True:
        print('\n=== Mars Program ===')
        print('1) 문제1: 인벤토리 정렬/필터/저장/이진')
        print('2) 문제2: 돔 표면적·무게 계산(반복)')
        print('3) 문제3: NumPy 평균<50 저장 + 전치')
        print('0) 종료')
        sel = input('선택: ').strip()

        if sel == '1':
            task1_inventory()
        elif sel == '2':
            task2_dome_loop()
        elif sel == '3':
            task3_parts_with_numpy()
        elif sel == '0':
            print('끝!')
            break
        else:
            print('메뉴 번호를 확인해줘.')

if __name__ == '__main__':
    main()
