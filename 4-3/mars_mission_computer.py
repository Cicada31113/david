from __future__ import annotations

import json
import os
import random
from datetime import datetime

class DummySensor:
    """더미 센서: 화성 기지 환경값을 랜덤 생성해 보관/반환/로그."""

    LOG_PATH = 'mission_env.log'

    def __init__(self) -> None:
        # 모든 항목을 키로 고정해두고 값은 None으로 초기화
        self.env_values = {
            'mars_base_internal_temperature': None,      # ℃
            'mars_base_external_temperature': None,      # ℃
            'mars_base_internal_humidity': None,         # %
            'mars_base_external_illuminance': None,      # W/m2
            'mars_base_internal_co2': None,              # %
            'mars_base_internal_oxygen': None,           # %
        }

    def set_env(self) -> None:
        """문제에서 준 범위로 랜덤 값을 채움."""
        # 온도 (℃)
        self.env_values['mars_base_internal_temperature'] = round(random.uniform(18,30), 2)
        self.env_values['mars_base_external_temperature'] = round(random.uniform(0, 21), 2)
        # 습도 (%)
        self.env_values['mars_base_internal_humidity'] = round(random.uniform(50, 60), 2)
        # 광량 (W/m2)
        self.env_values['mars_base_external_illuminance'] = round(random.uniform(500, 715), 2)
        # 농도 (%)
        self.env_values['mars_base_internal_co2'] = round(random.uniform(0.02, 0.1), 4)
        self.env_values['mars_base_internal_oxygen'] = round(random.uniform(4, 7), 2)

    def get_env(self, *, log: bool = True) -> dict:
        """
        현재 env_values를 반환.
        보너스: log=True면 타임스탬트와 함께 파일에 로그를 남김.
        """

        if log:
            self._log_env(self.env_values)
            return self.env_values
        
    #-------보너스 과제용: 내부 전용 메소드-------
    def _log_env(self, env: dict) -> None:
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        header = (
            'datetime'
            'mars_base_internal_temperature,'
            'mars_base_external_temperature,'
            'mars_base_internal_humidity,'
            'mars_base_external_illuminance,'
            'mars_base_internal_co2,'
            'mars_base_internal_oxygen'
        )
        line = (
            f'{ts},'
            f'{env["mars_base_internal_temperature"]},'
            f'{env["mars_base_external_temperature"]},'
            f'{env["mars_base_internal_humidity"]},'
            f'{env["mars_base_external_illuminance"]},'
            f'{env["mars_base_internal_co2"]},'
            f'{env["mars_base_internal_oxygen"]},'
        )
        # 파일이 없으면 헤더부터 쓰고, 있으면 데이터만 추가
        file_exists = os.path.exists(self.LOG_PATH)
        with open(self.LOG_PATH, mode='a', encoding='utf-8') as f:
            if not file_exists:
                f.write(header + '\n')
            f.write(line + '\n')

if __name__ == '__main__':
    # 인스턴스 생성
    ds = DummySensor()
    # 랜덤값 채우고
    ds.set_env()
    # 확인 + 로그 남김
    env = ds.get_env(log=True)

    # JSON으로 보기 좋게 출력(사람 읽기 용)
    print(json.dumps(env, ensure_ascii=False, indent=2))