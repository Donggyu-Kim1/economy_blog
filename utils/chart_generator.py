import os
import plotly.graph_objects as go
from datetime import datetime, timedelta
import yfinance as yf
from typing import Optional
import sys

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from config.settings import (
    US_INDICES,
    KR_INDICES,
    LOOKBACK_DAYS,
    get_image_filepath,
    DATE_FORMAT,
)


def generate_price_chart(
    ticker: str,
    market_name: str,
    date: Optional[str] = None,
    lookback_days: int = LOOKBACK_DAYS,
) -> Optional[str]:
    """
    주가 차트를 생성하고 저장합니다.

    Args:
        ticker (str): yfinance 티커 심볼
        market_name (str): 시장 이름
        date (str, optional): 차트 생성 날짜
        lookback_days (int): 과거 데이터 조회 기간

    Returns:
        str: 저장된 이미지 파일 경로 또는 None (실패 시)
    """
    try:
        # 날짜 설정
        date = date or datetime.now().strftime(DATE_FORMAT)
        end_date = datetime.strptime(date, DATE_FORMAT)
        start_date = end_date - timedelta(days=lookback_days)

        # 티커 형식 조정
        if ticker in KR_INDICES.values():
            ticker = f"^{ticker}"
        elif not ticker.startswith("^"):
            ticker = f"^{ticker}"

        # 데이터 수집
        yf_ticker = yf.Ticker(ticker)
        hist = yf_ticker.history(start=start_date, end=end_date)

        if hist.empty:
            print(f"No data found for {market_name}")
            return None

        # Plotly 차트 생성
        fig = go.Figure(
            data=[
                go.Candlestick(
                    x=hist.index,
                    open=hist["Open"],
                    high=hist["High"],
                    low=hist["Low"],
                    close=hist["Close"],
                    name=market_name,
                )
            ]
        )

        # 차트 스타일링
        fig.update_layout(
            title=f"{market_name} Price Movement",
            yaxis_title="Price",
            template="plotly_white",
            xaxis_rangeslider_visible=False,
            width=800,
            height=500,
        )

        # 저장 경로 설정 및 디렉토리 생성
        save_path = get_image_filepath(market_name, date)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # 이미지 저장
        fig.write_image(save_path)
        return save_path

    except Exception as e:
        print(f"Error generating chart for {market_name}: {str(e)}")
        return None


def generate_all_charts(date: Optional[str] = None) -> bool:
    """
    모든 시장 지수의 차트를 생성합니다.

    Args:
        date (str, optional): 차트 생성 날짜

    Returns:
        bool: 모든 차트 생성 성공 여부
    """
    success = True

    # 미국 시장 차트 생성
    for market_name, ticker in US_INDICES.items():
        if not generate_price_chart(ticker, market_name, date):
            success = False

    # 한국 시장 차트 생성
    for market_name, ticker in KR_INDICES.items():
        if not generate_price_chart(ticker, market_name, date):
            success = False

    return success


if __name__ == "__main__":
    # 모듈 테스트
    print("Testing chart generation...")
    try:
        success = generate_all_charts()
        if success:
            print("All charts generated successfully")
        else:
            print("Some charts failed to generate")
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
