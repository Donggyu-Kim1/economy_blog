import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from config.settings import US_TREASURIES, LOOKBACK_DAYS


def get_treasury_data(
    ticker: str, lookback_days: int = LOOKBACK_DAYS
) -> Optional[Dict[str, Any]]:
    """
    지정된 미국 국채의 수익률 데이터를 수집합니다.

    Args:
        ticker (str): yfinance 티커 심볼
        lookback_days (int): 과거 데이터 조회 기간 (기본값: settings.LOOKBACK_DAYS)

    Returns:
        Dict[str, Any]: 국채 수익률 데이터 딕셔너리 또는 에러 시 None
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
            print(f"Warning: No data found for treasury {ticker}")
            return None

        # 최신 데이터와 전일 데이터
        latest = hist.iloc[-1]
        prev = hist.iloc[-2] if len(hist) > 1 else latest

        # 52주 최고가, 최저가 계산
        year_high = hist["High"].max()
        year_low = hist["Low"].min()

        # 전일 대비 변화 계산 (수익률은 이미 퍼센트 단위이므로 차이를 직접 사용)
        daily_change = latest["Close"] - prev["Close"]

        return {
            "yield_rate": latest["Close"],
            "change": daily_change,
            "year_high": year_high,
            "year_low": year_low,
        }

    except Exception as e:
        print(f"Error fetching data for treasury {ticker}: {str(e)}")
        return None


def get_all_treasury_data() -> Dict[str, Dict[str, Any]]:
    """
    모든 미국 국채 수익률 데이터를 수집합니다.

    Returns:
        Dict[str, Dict[str, Any]]: 국채 이름을 키로 하고 데이터를 값으로 하는 딕셔너리
    """
    treasury_data = {}

    for treasury_name, ticker in US_TREASURIES.items():
        data = get_treasury_data(ticker)
        if data:
            treasury_data[treasury_name] = data
        else:
            print(f"Failed to fetch data for {treasury_name}")

    return treasury_data


def format_treasury_data(treasury_name: str, data: Dict[str, Any]) -> str:
    """
    국채 수익률 데이터를 보기 좋은 문자열로 포맷팅합니다.

    Args:
        treasury_name (str): 국채 종류
        data (Dict[str, Any]): 국채 수익률 데이터

    Returns:
        str: 포맷팅된 문자열
    """
    return f"""
{treasury_name}:
  현재수익률: {data['yield_rate']:.3f}%
  전일대비: {data['change']:+.3f}%p
  52주 최고: {data['year_high']:.3f}%
  52주 최저: {data['year_low']:.3f}%
"""


if __name__ == "__main__":
    # 모듈 테스트
    print("Testing US treasury data collection...")
    try:
        data = get_all_treasury_data()
        if data:
            for treasury_name, treasury_info in data.items():
                print(format_treasury_data(treasury_name, treasury_info))
        else:
            print("No data was collected.")
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
