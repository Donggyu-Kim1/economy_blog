import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import sys
import os
from pykrx import stock

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from config.settings import KRX_INDICES, LOOKBACK_DAYS


def get_market_data(
    ticker: str, lookback_days: int = LOOKBACK_DAYS
) -> Optional[Dict[str, Any]]:
    """
    지정된 한국 시장 지수의 데이터를 수집합니다.

    Args:
        ticker (str): KRX 지수 코드
        lookback_days (int): 과거 데이터 조회 기간 (기본값: settings.LOOKBACK_DAYS)

    Returns:
        Dict[str, Any]: 시장 데이터 딕셔너리 또는 에러 시 None
    """
    try:
        # 날짜 범위 설정
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)

        # 문자열 형식으로 변환
        end_date_str = end_date.strftime("%Y%m%d")
        start_date_str = start_date.strftime("%Y%m%d")

        # KRX에서 데이터 조회
        df = stock.get_index_ohlcv_by_date(start_date_str, end_date_str, ticker)

        if df.empty:
            print(f"Warning: No data found for market {ticker}")
            return None

        # 최신 데이터와 전일 데이터
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        # 20일 평균 거래량 계산
        volume_ma20 = df["거래량"].rolling(window=20).mean()
        latest_volume_ma20 = volume_ma20.iloc[-1]

        # 현재 거래량과 20일 평균 거래량의 비율
        volume_ratio = (
            latest["거래량"] / latest_volume_ma20 if latest_volume_ma20 > 0 else 0
        )

        # 52주 최고가, 최저가 계산
        year_high = df["고가"].max()
        year_low = df["저가"].min()

        # 전일 대비 변화율 계산
        daily_change = ((latest["종가"] - prev["종가"]) / prev["종가"]) * 100

        # 52주 최고가 대비 비율 계산
        year_high_ratio = ((latest["종가"] - year_high) / year_high) * 100

        return {
            "close": latest["종가"],
            "volume": latest["거래량"],
            "change": daily_change,
            "volume_ma20": latest_volume_ma20,
            "volume_ratio": volume_ratio,
            "year_high": year_high,
            "year_low": year_low,
            "year_high_ratio": year_high_ratio,
        }

    except Exception as e:
        print(f"Error fetching data for market {ticker}: {str(e)}")
        return None


def get_all_kr_market_data() -> Dict[str, Dict[str, Any]]:
    """
    모든 한국 시장 지수의 데이터를 수집합니다.

    Returns:
        Dict[str, Dict[str, Any]]: 시장 이름을 키로 하고 데이터를 값으로 하는 딕셔너리
    """
    market_data = {}

    for market_name, krx_ticker in KRX_INDICES.items():
        data = get_market_data(krx_ticker)
        if data:
            market_data[market_name] = data
        else:
            print(f"Failed to fetch data for {market_name}")

    return market_data


def format_market_data(market_name: str, data: Dict[str, Any]) -> str:
    """
    시장 데이터를 보기 좋은 문자열로 포맷팅합니다.

    Args:
        market_name (str): 시장 이름
        data (Dict[str, Any]): 시장 데이터

    Returns:
        str: 포맷팅된 문자열
    """
    volume_ratio = data["volume_ratio"]
    volume_description = (
        "매우 활발한"
        if volume_ratio >= 2
        else (
            "활발한"
            if volume_ratio >= 1.5
            else "평균 수준의" if volume_ratio >= 0.8 else "다소 낮은"
        )
    )

    return f"""
{market_name}:
 종가: {data['close']:,.2f}
 전일대비: {data['change']:+.2f}%
 거래량: {data['volume']:,} ({volume_ratio:.1f}배, {volume_description})
 20일 평균거래량: {data['volume_ma20']:,.0f}
 52주 최고가: {data['year_high']:,.2f}
 52주 최저가: {data['year_low']:,.2f}
 고점대비: {data['year_high_ratio']:,.2f}%
"""


if __name__ == "__main__":
    # 모듈 테스트
    print("Testing Korean market data collection...")
    try:
        data = get_all_kr_market_data()
        if data:
            for market_name, market_info in data.items():
                print(format_market_data(market_name, market_info))
        else:
            print("No data was collected.")
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
