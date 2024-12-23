from fredapi import Fred
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import sys
import os
from dataclasses import dataclass

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from config.settings import (
    FREDAPI_KEY,
    ECONOMIC_INDICATORS,
    CALENDAR_LOOKBACK_DAYS,
)


@dataclass
class EconomicEvent:
    """경제 지표 이벤트를 표현하는 데이터 클래스"""

    date: str
    indicator: str
    value: float
    previous_value: Optional[float] = None
    forecast_value: Optional[float] = None
    description: Optional[str] = None


class EconomicCalendar:
    """FRED API를 사용하여 경제 지표 데이터를 관리하는 클래스"""

    # 지표명 한글 매핑
    INDICATOR_NAMES = {
        "GDP": "국내총생산(GDP)",
        "UNRATE": "실업률",
        "CPIAUCSL": "소비자물가지수",
        "FEDFUNDS": "기준금리",
        "INDPRO": "산업생산지수",
        "PAYEMS": "비농업부문고용",
        "PCE": "개인소비지출",
        "HOUST": "주택착공건수",
        "BOGMBASE": "본원통화",
        "RETAILSMNSA": "소매판매",
    }

    def __init__(self):
        """FRED API 클라이언트 초기화"""
        if not FREDAPI_KEY:
            raise ValueError("FRED API key is not set in environment variables")
        self.fred = Fred(api_key=FREDAPI_KEY)

    def get_recent_data(self) -> List[EconomicEvent]:
        """최근 발표된 경제지표 데이터를 조회"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=CALENDAR_LOOKBACK_DAYS)

        recent_events = []

        for indicator_name, series_id in ECONOMIC_INDICATORS.items():
            try:
                # 시계열 데이터 조회
                series = self.fred.get_series(
                    series_id, start_date=start_date, end_date=end_date
                )

                if not series.empty:
                    # 최신 데이터와 이전 데이터 추출
                    latest_date = series.index[-1]
                    latest_value = series.iloc[-1]
                    previous_value = series.iloc[-2] if len(series) > 1 else None

                    event = EconomicEvent(
                        date=latest_date.strftime("%Y-%m-%d"),
                        indicator=indicator_name,
                        value=latest_value,
                        previous_value=previous_value,
                        description=self.fred.get_series_info(series_id)["title"],
                    )
                    recent_events.append(event)

            except Exception as e:
                print(f"Error fetching data for {indicator_name}: {str(e)}")

        return recent_events

    def format_recent_data(self, events: List[EconomicEvent]) -> str:
        """최근 경제지표 데이터를 문자열로 포맷팅"""
        formatted_text = "최근 발표된 주요 경제지표:\n\n"

        for event in events:
            change = ""
            if event.previous_value is not None:
                pct_change = (
                    (event.value - event.previous_value) / event.previous_value
                ) * 100
                change = f"(전기대비 {pct_change:+.1f}%)"

            # 한글 지표명 사용
            indicator_name = self.INDICATOR_NAMES.get(event.indicator, event.indicator)
            formatted_text += (
                f"- {indicator_name}: {event.value:.2f} {change}\n"
                f"  날짜: {event.date}\n"
                f"  설명: {event.description}\n\n"
            )

        return formatted_text


if __name__ == "__main__":
    # 모듈 테스트
    calendar = EconomicCalendar()

    print("Testing economic calendar...")
    try:
        # 최근 데이터 조회 테스트
        recent_events = calendar.get_recent_data()
        print(calendar.format_recent_data(recent_events))

    except Exception as e:
        print(f"Test failed with error: {str(e)}")
