import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from config.settings import US_INDICES, LOOKBACK_DAYS


def get_market_data(
    ticker: str, lookback_days: int = LOOKBACK_DAYS
) -> Optional[Dict[str, Any]]:
    """
    지정된 티커의 시장 데이터를 수집합니다.

    Args:
        ticker (str): yfinance 티커 심볼
        lookback_days (int): 과거 데이터 조회 기간 (기본값: settings.LOOKBACK_DAYS)

    Returns:
        Dict[str, Any]: 시장 데이터 딕셔너리 또는 에러 시 None
    """
    try:
        # yfinance 티커 객체 생성
        yf_ticker = yf.Ticker(ticker)

        # 시작일과 종료일 설정
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)

        # 과거 데이터 조회
        hist = yf_ticker.history(start=start_date, end=end_date)

        if hist.empty:
            print(f"Warning: No data found for ticker {ticker}")
            return None

        # 최신 데이터와 전일 데이터
        latest = hist.iloc[-1]
        prev = (
            hist.iloc[-2] if len(hist) > 1 else latest
        )  # 데이터가 하나만 있는 경우 처리

        # 52주 최고가, 최저가 계산
        year_high = hist["High"].max()
        year_low = hist["Low"].min()

        # 전일 대비 변화율 계산
        daily_change = ((latest["Close"] - prev["Close"]) / prev["Close"]) * 100

        # 52주 최고가 대비 비율 계산
        year_high_ratio = ((latest["Close"] - year_high) / year_high) * 100

        return {
            "close": latest["Close"],
            "volume": latest["Volume"],
            "change": daily_change,
            "year_high": year_high,
            "year_low": year_low,
            "year_high_ratio": year_high_ratio,
        }

    except Exception as e:
        print(f"Error fetching data for {ticker}: {str(e)}")
        return None


def get_all_us_market_data() -> Dict[str, Dict[str, Any]]:
    """
    모든 미국 시장 지수의 데이터를 수집합니다.

    Returns:
        Dict[str, Dict[str, Any]]: 시장 이름을 키로 하고 데이터를 값으로 하는 딕셔너리
    """
    market_data = {}

    for market_name, ticker in US_INDICES.items():
        data = get_market_data(ticker)
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
    return f"""
{market_name}:
  종가: {data['close']:,.2f}
  전일대비: {data['change']:+.2f}%
  거래량: {data['volume']:,}
  52주 최고가: {data['year_high']:,.2f}
  52주 최저가: {data['year_low']:,.2f}
  고점대비: {data['year_high_ratio']:,.2f}%
"""


if __name__ == "__main__":
    # 모듈 테스트
    print("Testing US market data collection...")
    try:
        data = get_all_us_market_data()
        if data:
            for market_name, market_info in data.items():
                print(format_market_data(market_name, market_info))
        else:
            print("No data was collected.")
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
