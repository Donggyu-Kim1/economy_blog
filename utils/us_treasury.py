import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fredapi import Fred
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from config.settings import US_TREASURIES, LOOKBACK_DAYS, FEDAPI_KEY

fred = Fred(api_key=FEDAPI_KEY)


def get_fed_rate() -> float:
    """연방기금금리 목표 상단 가져오기"""
    try:
        fed_rate = fred.get_series("DFEDTARU").iloc[-1]
        return float(fed_rate)
    except Exception as e:
        print(f"Error fetching Fed rate: {str(e)}")
        return 5.50


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

        # 기간별 평균
        ma_90 = hist["Close"].rolling(window=90).mean().iloc[-1]  # 3개월 평균
        ma_180 = hist["Close"].rolling(window=180).mean().iloc[-1]  # 6개월 평균

        # 변동성 분석
        last_month = hist["Close"].tail(20)  # 최근 1개월
        monthly_volatility = last_month.std()
        long_term_volatility = hist["Close"].std()
        volatility_ratio = (
            monthly_volatility / long_term_volatility if long_term_volatility > 0 else 0
        )

        fed_rate = get_fed_rate()

        return {
            "yield_rate": latest["Close"],
            "change": latest["Close"] - prev["Close"],
            "year_high": hist["High"].max(),
            "year_low": hist["Low"].min(),
            "ma_90": ma_90,
            "ma_180": ma_180,
            "monthly_volatility": monthly_volatility,
            "long_term_volatility": long_term_volatility,
            "volatility_ratio": volatility_ratio,
            "fed_spread": latest["Close"] - fed_rate,
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
    # 변동성 설명
    volatility_desc = (
        "변동성 크게 확대"
        if data["volatility_ratio"] > 1.2
        else (
            "변동성 크게 축소"
            if data["volatility_ratio"] < 0.8
            else "보통 수준의 변동성"
        )
    )

    # 기준금리 대비 설명
    fed_spread_desc = (
        "기준금리와 유사"
        if abs(data["fed_spread"]) <= 0.25
        else f"기준금리 대비 {abs(data['fed_spread']):.2f}%p {'높음' if data['fed_spread'] > 0 else '낮음'}"
    )

    return f"""
{treasury_name}:
 현재수익률: {data['yield_rate']:.3f}% ({data['change']:+.3f}%p)
 3개월 평균: {data['ma_90']:.3f}%
 6개월 평균: {data['ma_180']:.3f}%
 52주 범위: {data['year_low']:.3f}% ~ {data['year_high']:.3f}%
 변동성: {volatility_desc}
 기준금리: {fed_spread_desc}
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
