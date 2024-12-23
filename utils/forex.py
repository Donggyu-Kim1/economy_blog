import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from config.settings import CURRENCIES, LOOKBACK_DAYS


def get_forex_data(
    currency_pair: str, lookback_days: int = LOOKBACK_DAYS
) -> Optional[Dict[str, Any]]:
    """
    지정된 통화쌍의 환율 데이터를 수집합니다.

    Args:
        currency_pair (str): 통화쌍 (예: "USD/KRW")
        lookback_days (int): 과거 데이터 조회 기간 (기본값: settings.LOOKBACK_DAYS)

    Returns:
        Dict[str, Any]: 환율 데이터 딕셔너리 또는 에러 시 None
    """
    try:
        # 통화쌍을 yfinance 형식으로 변환 (예: USD/KRW -> USDKRW=X)
        base_currency, quote_currency = currency_pair.split("/")
        ticker = f"{base_currency}{quote_currency}=X"

        # yfinance 티커 객체 생성
        yf_ticker = yf.Ticker(ticker)

        # 시작일과 종료일 설정
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)

        # 과거 데이터 조회
        hist = yf_ticker.history(start=start_date, end=end_date)

        if hist.empty:
            print(f"Warning: No data found for currency pair {currency_pair}")
            return None

        # 최신 데이터와 전일 데이터
        latest = hist.iloc[-1]
        prev = hist.iloc[-2] if len(hist) > 1 else latest

        # 52주 최고가, 최저가 계산
        year_high = hist["High"].max()
        year_low = hist["Low"].min()

        # 전일 대비 변화율 계산
        daily_change = ((latest["Close"] - prev["Close"]) / prev["Close"]) * 100

        return {
            "rate": latest["Close"],
            "change": daily_change,
            "year_high": year_high,
            "year_low": year_low,
        }

    except Exception as e:
        print(f"Error fetching data for currency pair {currency_pair}: {str(e)}")
        return None


def get_all_forex_data() -> Dict[str, Dict[str, Any]]:
    """
    모든 설정된 통화쌍의 환율 데이터를 수집합니다.

    Returns:
        Dict[str, Dict[str, Any]]: 통화쌍을 키로 하고 데이터를 값으로 하는 딕셔너리
    """
    forex_data = {}

    for currency_pair in CURRENCIES:
        data = get_forex_data(currency_pair)
        if data:
            forex_data[currency_pair] = data
        else:
            print(f"Failed to fetch data for {currency_pair}")

    return forex_data


def format_forex_data(currency_pair: str, data: Dict[str, Any]) -> str:
    """
    환율 데이터를 보기 좋은 문자열로 포맷팅합니다.

    Args:
        currency_pair (str): 통화쌍
        data (Dict[str, Any]): 환율 데이터

    Returns:
        str: 포맷팅된 문자열
    """
    return f"""
{currency_pair}:
  현재환율: {data['rate']:,.2f}
  전일대비: {data['change']:+.2f}%
  52주 최고: {data['year_high']:,.2f}
  52주 최저: {data['year_low']:,.2f}
"""


if __name__ == "__main__":
    # 모듈 테스트
    print("Testing forex data collection...")
    try:
        data = get_all_forex_data()
        if data:
            for currency_pair, forex_info in data.items():
                print(format_forex_data(currency_pair, forex_info))
        else:
            print("No data was collected.")
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
