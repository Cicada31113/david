# 공백 트리밍 제거버전
# design_dome.py
import math


def _normalize_material_kor(text: str) -> str:
    """앞뒤 + 중간의 모든 공백 문자 제거(한글 재질명 정규화)"""
    if not isinstance(text, str):
        return ''
    # strip() + split() 조합으로 탭/개행 포함 모든 공백 제거
    return ''.join(text.strip().split())


def sphere_area(diameter: float, material: str, thickness: float = 1.0) -> tuple[float, float]:
    # 1) 타입
    if not isinstance(diameter, (int, float)):
        raise ValueError
    if not isinstance(thickness, (int, float)):
        raise ValueError
    if not isinstance(material, str):
        raise ValueError

    # 2) 유한값(NaN/Inf 차단)
    if not math.isfinite(diameter):
        raise ValueError
    if not math.isfinite(thickness):
        raise ValueError

    # 3) 범위
    if diameter <= 0:
        raise ValueError
    if thickness <= 0:
        raise ValueError

    # 4) 허용 재질(한글만, 공백 정규화 포함)
    material = _normalize_material_kor(material)
    densities_g_per_cm3 = {'유리': 2.4, '알루미늄': 2.7, '탄소강': 7.85}
    if material not in densities_g_per_cm3:
        raise ValueError

    # ---- 계산부(문제식 그대로) ----
    # 면적: π·d² (m²)
    area_m2 = math.pi * (diameter ** 2)

    # m² → cm²(×10000), 두께(cm) 곱 → 부피(cm³)
    volume_cm3 = (area_m2 * 10000.0) * thickness

    # 질량(kg) = 밀도(g/cm³)×부피(cm³)/1000
    mass_kg = densities_g_per_cm3[material] * volume_cm3 / 1000.0

    # 화성 무게(kg) = 질량 × 0.38
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

        # 재질(한글만 허용, 공백 트리밍/내부공백 제거)
        material_in = input('재질(유리/알루미늄/탄소강)을 입력하세요:').strip()
        material_kor = _normalize_material_kor(material_in)
        if material_kor not in ('유리', '알루미늄', '탄소강'):
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
