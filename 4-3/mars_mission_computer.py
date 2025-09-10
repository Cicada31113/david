from __future__ import annotations

import json
import os
import random
import time # 문제 2번을 위해 추가
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

# ====================================================
#             문제 2 : Mission Computer
# ====================================================

class MissionComputer:
    """미션 컴퓨터: 센서값을 수집/보관하고 주기적으로 JSON 출력."""
    def __init__(self, sensor: DummySensor) -> None:
        self.sensor = sensor 
        # 문제에서 지정한 키 스키마 동일 유지
        self.env_values = {
            'mars_base_internal_temperature': None,      # ℃
            'mars_base_external_temperature': None,      # ℃
            'mars_base_internal_humidity': None,         # %
            'mars_base_external_illuminance': None,      # W/m2
            'mars_base_internal_co2': None,              # %
            'mars_base_internal_oxygen': None,           # %  
        }

    def get_sensor_data(self, interval_sec: int = 5, log_sensor: bool = True) -> None:
        """
        센서에서 값을 읽어 env_values에 담고, JSON으로 interval_sec마다 출력.
        Ctrl+C(keyboard interrupt)로 종료 가능.
        """
        try:
            while True:
                self.sensor.set_env()
                data = self.sensor.get_env(log=log_sensor)
                self.env_values.update(data)
                print(json.dumps(self.env_values, ensure_ascii=False))
                time.sleep(interval_sec)
        except KeyboardInterrupt:
            print('System stopped... .')



if __name__ == '__main__':
    # 인스턴스 생성
    ds = DummySensor()
    # 랜덤값 채우고
    ds.set_env()
    # 확인 + 로그 남김
    env = ds.get_env(log=True)

    # JSON으로 보기 좋게 출력(사람 읽기 용)
    print(json.dumps(env, ensure_ascii=False, indent=2))

    # ======== 문제 2 ======== (5초마다 지속출력)
    print('\n[MissionComputer streaming every 5s] (Press Ctrl+C to stop)')
    RunComputer = MissionComputer(ds)
    RunComputer.get_sensor_data(interval_sec=5, log_sensor=True)