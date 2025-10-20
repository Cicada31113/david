# 예외처리 우선순서 반영
# design_dome.py
import math

# 공백트리밍 반영 !!!!
def _normalize_material_kor(text: str) -> str:
    """앞뒤 + 중간 공백 제거"""
    if not isinstance(text, str):
        return ''
    return ''.join(text.strip().split())


def sphere_area(diameter: float, material: str, thickness: float = 1.0) -> tuple[float, float]:
    # 1) 타입
    if not isinstance(diameter, (int, float)):
        raise ValueError
    if not isinstance(thickness, (int, float)):
        raise ValueError
    if not isinstance(material, str):
        raise ValueError

    # 2) 유한값
    if not math.isfinite(diameter):
        raise ValueError
    if not math.isfinite(thickness):
        raise ValueError

    # 3) 범위
    if diameter <= 0:
        raise ValueError
    if thickness <= 0:
        raise ValueError

    # 4) 재질(한글만, 공백 정규화)
    material = _normalize_material_kor(material)
    densities_g_per_cm3 = {'유리': 2.4, '알루미늄': 2.7, '탄소강': 7.85}
    if material not in densities_g_per_cm3:
        raise ValueError

    # ---- 계산(문제식 그대로) ----
    area_m2 = math.pi * (diameter ** 2)               # π·d² (m²)
    volume_cm3 = (area_m2 * 10000.0) * thickness      # m²→cm² 후 두께(cm) 곱
    mass_kg = densities_g_per_cm3[material] * volume_cm3 / 1000.0
    mars_weight_kg = mass_kg * 0.38

    return area_m2, mars_weight_kg


def main() -> None:
    try:
        # 지름(m)
        d_raw = input('지름(m)을 입력하세요:').strip()
        if not d_raw:
            print('Invalid input.'); return
        try:
            diameter_m = float(d_raw)
        except Exception:
            print('Invalid input.'); return
        if diameter_m <= 0:                      # ✅ 입력값 오류 우선 처리(a)
            print('Invalid input.'); return

        # 재질(한글만 허용, 공백 정규화)
        material_in = input('재질(유리/알루미늄/탄소강)을 입력하세요:').strip()
        material_kor = _normalize_material_kor(material_in)
        if material_kor not in ('유리', '알루미늄', '탄소강'):   # ✅ 입력값 오류 우선 처리(b)
            print('Invalid input.'); return

        # 두께(cm) — 빈 입력이면 1.0
        t_raw = input('두께(cm)를 입력하세요(기본값 1):').strip()
        if t_raw == '':
            thickness_cm = 1.0
        else:
            try:
                thickness_cm = float(t_raw)
            except Exception:
                print('Invalid input.'); return
        if thickness_cm <= 0:                    # ✅ 입력값 오류 우선 처리(c)
            print('Invalid input.'); return

        # 계산
        try:
            area_m2, mars_weight_kg = sphere_area(diameter_m, material_kor, thickness_cm)
        except ValueError:
            print('Invalid input.'); return
        except Exception:
            print('Processing error.'); return

        # 정확히 한 줄 출력
        print(f'재질 : {material_kor}, 지름 : {diameter_m:g}, 두께 : {thickness_cm:g}, 면적 : {area_m2:.3f}, 무게 : {mars_weight_kg:.3f} kg')

    except Exception:
        print('Processing error.')


if __name__ == '__main__':
    main()
