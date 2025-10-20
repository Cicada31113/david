# 계산식 예외처리 추가

# design_dome05.py
import math


def _normalize_material_kor(text: str) -> str:
    """앞뒤/중간 공백 제거 (예: ' 알 루 미 늄 ' -> '알루미늄')"""
    if not isinstance(text, str):
        return ''
    return ''.join(text.strip().split())


def sphere_area(diameter: float, material: str, thickness: float = 1.0) -> tuple[float, float]:
    """반구체 돔(hemisphere)의 겉면적(문제정의: π·d²)과 화성 중력 기준 무게를 계산"""
    # === 입력 검증: 실패 시 반드시 ValueError ===
    if not isinstance(diameter, (int, float)) or not math.isfinite(diameter) or diameter <= 0:
        raise ValueError
    if not isinstance(thickness, (int, float)) or not math.isfinite(thickness) or thickness <= 0:
        raise ValueError
    if not isinstance(material, str):
        raise ValueError

    material_kor = _normalize_material_kor(material)
    densities_g_per_cm3 = {
        '유리': 2.4,
        '알루미늄': 2.7,
        '탄소강': 7.85,
    }
    if material_kor not in densities_g_per_cm3:
        raise ValueError

    # === 계산: 오류 발생 시 그대로 밖으로 전파(절대 ValueError로 바꿔치기 X) ===
    try:
        area_m2 = math.pi * (diameter ** 2)               # π·d² (m²)
        volume_cm3 = (area_m2 * 10000.0) * thickness      # m²→cm² 후 두께(cm) 곱
        mass_kg = densities_g_per_cm3[material_kor] * volume_cm3 / 1000.0
        mars_weight_kg = mass_kg * 0.38
        return area_m2, mars_weight_kg
    except Exception:
        raise  # 그대로 전파 → main()에서 'Processing error.' 경로로 감


def main() -> None:
    try:
        # 지름(m)
        d_raw = input('지름(m)을 입력하세요: ').strip()
        diameter_m = float(d_raw)
        if diameter_m <= 0:
            print('Invalid input.')
            return

        # 재질(유리/알루미늄/탄소강)
        material_in = input('재질(유리/알루미늄/탄소강)을 입력하세요: ').strip()
        material_kor = _normalize_material_kor(material_in)
        if material_kor not in ('유리', '알루미늄', '탄소강'):
            print('Invalid input.')
            return

        # 두께(cm) — 빈 입력이면 1.0
        t_raw = input('두께(cm)를 입력하세요(빈 값=1.0): ').strip()
        thickness_cm = 1.0 if t_raw == '' else float(t_raw)
        if thickness_cm <= 0:
            print('Invalid input.')
            return

        # 계산 호출
        try:
            area_m2, mars_weight_kg = sphere_area(diameter_m, material_kor, thickness_cm)
        except ValueError:
            print('Invalid input.')
            return
        except Exception:
            print('Processing error.')
            return

        # 정확히 한 줄 출력
        print(f'재질 : {material_kor}, 지름 : {diameter_m:g}, 두께 : {thickness_cm:g}, 면적 : {area_m2:.3f}, 무게 : {mars_weight_kg:.3f} kg')



    except ValueError:
        # 입력 변환 등에서 뜬 ValueError
        print('Invalid input.')
    except Exception:
        # 그 외 모든 처리 단계 오류
        print('Processing error.')


if __name__ == '__main__':
    main()
