import os
import matplotlib.pyplot as plt
from datetime import datetime, timedelta, timezone
import yfinance as yf
from typing import Optional
import sys
import pandas as pd
import mplfinance as mpf
import matplotlib.font_manager as fm
from pykrx import stock

# 한글 폰트 설정
if os.name == "nt":  # Windows
    font_path = "C:/Windows/Fonts/malgun.ttf"
else:  # Linux
    font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"

font_name = fm.FontProperties(fname=font_path).get_name()
plt.rcParams["font.family"] = font_name

# mplfinance 스타일에 폰트 적용
s = mpf.make_mpf_style(base_mpf_style="yahoo", rc={"font.family": font_name})

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from config.settings import (
    US_INDICES,
    KRX_INDICES,
    LOOKBACK_DAYS,
    get_image_filepath,
    DATE_FORMAT,
)

MARKET_NAMES_KR = {
    "S&P 500": "S&P 500 지수",
    "NASDAQ": "나스닥 지수",
    "DOW": "다우존스 지수",
    "KOSPI": "코스피 지수",
    "KOSDAQ": "코스닥 지수",
}


def get_market_end_time(market_name: str) -> datetime:
    """시장별 장 마감 시간 반환"""
    now = datetime.now(timezone(timedelta(hours=9)))  # KST

    if market_name in ["KOSPI", "KOSDAQ"]:
        # 한국 시장 (15:30 KST 마감)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)

        # 현재 시간이 장 마감 이전이면 전일로 설정
        if now.time() < market_close.time():
            market_close -= timedelta(days=1)

        # 주말인 경우 금요일로 조정
        while market_close.weekday() > 4:  # 5=토요일, 6=일요일
            market_close -= timedelta(days=1)

        return market_close
    else:
        # 미국 시장
        return now


def process_krx_data(df: pd.DataFrame) -> pd.DataFrame:
    """KRX 데이터를 mplfinance 형식으로 변환"""
    # 컬럼명 변경
    df = df.rename(
        columns={
            "시가": "Open",
            "고가": "High",
            "저가": "Low",
            "종가": "Close",
            "거래량": "Volume",
        }
    )

    return df


def get_krx_data(
    ticker: str, start_date: datetime, end_date: datetime
) -> Optional[pd.DataFrame]:
    """KRX 데이터 조회"""
    try:
        # 날짜 형식 변환
        start_date_str = start_date.strftime("%Y%m%d")
        end_date_str = end_date.strftime("%Y%m%d")

        # KRX에서 데이터 조회
        df = stock.get_index_ohlcv_by_date(start_date_str, end_date_str, ticker)

        if df.empty:
            print(f"데이터를 찾을 수 없음: {ticker}")
            return None

        return process_krx_data(df)

    except Exception as e:
        print(f"KRX 데이터 조회 중 오류 발생: {str(e)}")
        return None


def generate_price_chart(
    ticker: str,
    market_name: str,
    date: Optional[str] = None,
    lookback_days: int = LOOKBACK_DAYS,
) -> Optional[str]:
    """차트 생성"""
    try:
        # 시장별 적절한 종료 시점 설정
        end_date = get_market_end_time(market_name)
        start_date = end_date - timedelta(days=min(lookback_days, 30))

        # 데이터 수집
        if market_name in ["KOSPI", "KOSDAQ"]:
            # KRX 데이터 사용
            hist = get_krx_data(ticker, start_date, end_date)
        else:
            # 미국 시장은 기존 yfinance 사용
            if not ticker.startswith("^"):
                ticker = f"^{ticker}"
            yf_ticker = yf.Ticker(ticker)
            hist = yf_ticker.history(
                start=start_date.strftime("%Y-%m-%d"),
                end=(end_date + timedelta(days=1)).strftime("%Y-%m-%d"),
                interval="1d",
            )

        if hist is None or hist.empty:
            print(f"데이터를 찾을 수 없음: {market_name}")
            return None

        # 저장 경로 설정
        save_path = get_image_filepath(market_name, end_date.strftime(DATE_FORMAT))
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # 한글 제목 사용
        kr_name = MARKET_NAMES_KR.get(market_name, market_name)

        # 차트 생성 및 저장
        mpf.plot(
            hist,
            type="candle",
            title=f"{kr_name} 가격 추이",
            savefig=save_path,
            style=s,
            figsize=(10, 6),
            volume=True,
            panel_ratios=(5, 1),  # 가격:거래량 패널 비율
            ylabel="가격",
            ylabel_lower="거래량",
        )

        plt.close()
        return save_path

    except Exception as e:
        print(f"차트 생성 중 오류 발생 ({market_name}): {str(e)}")
        return None


def generate_all_charts(date: Optional[str] = None) -> bool:
    """모든 시장 지수의 차트를 생성"""
    success = True

    # 한국 시장 차트 먼저 생성
    for market_name, ticker in KRX_INDICES.items():
        if not generate_price_chart(ticker, market_name, date):
            success = False

    # 미국 시장 차트 생성
    for market_name, ticker in US_INDICES.items():
        if not generate_price_chart(ticker, market_name, date):
            success = False

    return success


if __name__ == "__main__":
    # 모듈 테스트
    print("차트 생성 테스트 시작...")
    try:
        success = generate_all_charts()
        if success:
            print("모든 차트가 성공적으로 생성되었습니다")
        else:
            print("일부 차트 생성에 실패했습니다")
    except Exception as e:
        print(f"테스트 실패: {str(e)}")
