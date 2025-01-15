import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from fredapi import Fred
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from config.settings import FEDAPI_KEY
from src.logger import logger


class BuffettIndicator:
    def __init__(self):
        """
        1980년부터 현재까지의 데이터를 사용하여 버핏 지표를 계산합니다.
        """
        self.start_date = datetime(1980, 1, 1)
        self.end_date = datetime.now()
        self.fred = Fred(api_key=FEDAPI_KEY)

    def get_wilshire_data(self) -> Optional[pd.DataFrame]:
        """Wilshire 5000 Total Market Index 데이터 수집"""
        try:
            ticker = "^W5000"
            wilshire = yf.download(
                ticker,
                start=self.start_date.strftime("%Y-%m-%d"),
                end=self.end_date.strftime("%Y-%m-%d"),
            )

            if wilshire.empty:
                logger.error("Wilshire 5000 데이터를 가져올 수 없습니다.")
                return None

            # 종가만 선택하여 Series로 변환 후 데이터프레임으로 생성
            return pd.DataFrame(
                data=wilshire["Close"].values,
                index=wilshire.index,
                columns=["Market_Value"],
            )

        except Exception as e:
            logger.error(f"Wilshire 데이터 수집 중 오류 발생: {str(e)}")
            return None

    def get_gdp_data(self) -> Optional[pd.DataFrame]:
        """미국 GDP 데이터 수집"""
        try:
            # FRED에서 GDP 데이터 수집 (Quarterly)
            gdp = self.fred.get_series(
                "GDP",
                observation_start=self.start_date.strftime("%Y-%m-%d"),
                observation_end=self.end_date.strftime("%Y-%m-%d"),
            )

            if gdp.empty:
                logger.error("GDP 데이터를 가져올 수 없습니다.")
                return None

            # 데이터프레임으로 변환
            gdp_df = pd.DataFrame(gdp, columns=["GDP"])
            gdp_df.index = pd.to_datetime(gdp_df.index)
            gdp_df.index.name = "Date"

            # Quarterly GDP를 일별 데이터로 보간
            gdp_df = gdp_df.resample("D").interpolate(method="linear")

            return gdp_df

        except Exception as e:
            logger.error(f"GDP 데이터 수집 중 오류 발생: {str(e)}")
            return None

    def calculate_buffett_indicator(self) -> Optional[pd.DataFrame]:
        """Buffett Indicator 계산"""
        try:
            # 데이터 수집
            market_value = self.get_wilshire_data()
            gdp = self.get_gdp_data()

            if market_value is None or gdp is None:
                return None

            # 날짜 인덱스로 데이터 정렬 및 병합
            merged_data = pd.merge(
                market_value, gdp, left_index=True, right_index=True, how="inner"
            )

            # Buffett Indicator 계산 (Market Value to GDP ratio)
            merged_data["Buffett_Indicator"] = (
                merged_data["Market_Value"] / merged_data["GDP"] * 100
            )

            # 트렌드 라인 및 표준편차 계산 (2년 이동평균)
            window = 504  # 2년 거래일 수 (252 * 2)

            # 트렌드 계산
            merged_data["Trend"] = (
                merged_data["Buffett_Indicator"]
                .rolling(window=window, min_periods=int(window / 2))
                .mean()
            )

            # 표준편차 계산
            rolling_std = (
                merged_data["Buffett_Indicator"]
                .rolling(window=window, min_periods=int(window / 2))
                .std()
            )

            merged_data["Upper_2std"] = merged_data["Trend"] + (2 * rolling_std)
            merged_data["Upper_1std"] = merged_data["Trend"] + rolling_std
            merged_data["Lower_1std"] = merged_data["Trend"] - rolling_std
            merged_data["Lower_2std"] = merged_data["Trend"] - (2 * rolling_std)

            return merged_data

        except Exception as e:
            logger.error(f"Buffett Indicator 계산 중 오류 발생: {str(e)}")
            return None

    def get_current_status(self) -> Optional[Dict[str, float]]:
        """현재 Buffett Indicator 상태 분석"""
        try:
            data = self.calculate_buffett_indicator()
            if data is None or data.empty:
                return None

            latest = data.iloc[-1]
            historical_mean = data["Buffett_Indicator"].mean()
            historical_std = data["Buffett_Indicator"].std()

            status = {
                "current_ratio": latest["Buffett_Indicator"],
                "trend_value": latest["Trend"],
                "historical_mean": historical_mean,
                "historical_std": historical_std,
                "deviation_from_trend": (
                    (latest["Buffett_Indicator"] - latest["Trend"])
                    / latest["Trend"]
                    * 100
                ),
                "zscore": (latest["Buffett_Indicator"] - historical_mean)
                / historical_std,
                "upper_2std": latest["Upper_2std"],
                "lower_2std": latest["Lower_2std"],
            }

            # 시장 상태 평가
            if status["zscore"] > 2:
                status["market_status"] = "매우 과대평가"
            elif status["zscore"] > 1:
                status["market_status"] = "과대평가"
            elif status["zscore"] < -2:
                status["market_status"] = "매우 과소평가"
            elif status["zscore"] < -1:
                status["market_status"] = "과소평가"
            else:
                status["market_status"] = "적정가치"

            return status

        except Exception as e:
            logger.error(f"현재 상태 분석 중 오류 발생: {str(e)}")
            return None

    def backtest_indicator(
        self, lookforward_months: int = 12
    ) -> Optional[pd.DataFrame]:
        """
        버핏 지표의 예측력을 백테스트합니다.

        Args:
            lookforward_months (int): 미래 수익률을 계산할 기간 (개월)

        Returns:
            Optional[pd.DataFrame]: 백테스트 결과
        """
        try:
            # 기본 데이터 계산
            data = self.calculate_buffett_indicator()
            if data is None:
                return None

            # S&P 500 데이터 가져오기 (시장 수익률 대용)
            spy_data = yf.download(
                "^GSPC",
                start=self.start_date.strftime("%Y-%m-%d"),
                end=self.end_date.strftime("%Y-%m-%d"),
            )

            # Close 가격을 Series로 변환하여 데이터프레임에 추가
            data = data.copy()  # 데이터 복사본 생성
            data["SPY"] = spy_data["Close"]

            # 미래 수익률 계산 (lookforward_months 개월 후)
            days = lookforward_months * 21  # 거래일 기준 변환
            data["Future_Return"] = (data["SPY"].shift(-days) / data["SPY"] - 1) * 100

            # Z-score 계산
            data["Z_Score"] = (
                data["Buffett_Indicator"] - data["Buffett_Indicator"].expanding().mean()
            ) / data["Buffett_Indicator"].expanding().std()

            # 구간별 성과 분석
            ranges = [
                ("매우 과대평가", lambda x: x > 2),
                ("과대평가", lambda x: (x > 1) & (x <= 2)),
                ("적정가치", lambda x: (x >= -1) & (x <= 1)),
                ("과소평가", lambda x: (x < -1) & (x >= -2)),
                ("매우 과소평가", lambda x: x < -2),
            ]

            results = []
            for label, condition in ranges:
                mask = condition(data["Z_Score"])
                subset = data[mask]

                if len(subset) > 0:
                    avg_return = subset["Future_Return"].mean()
                    pos_prob = (subset["Future_Return"] > 0).mean() * 100
                    count = len(subset)
                    max_drawdown = subset["Future_Return"].min()
                    best_return = subset["Future_Return"].max()

                    results.append(
                        {
                            "구간": label,
                            "평균수익률": avg_return,
                            "양의수익률확률": pos_prob,
                            "샘플수": count,
                            "최대하락": max_drawdown,
                            "최대상승": best_return,
                        }
                    )

            return pd.DataFrame(results)

        except Exception as e:
            logger.error(f"백테스트 중 오류 발생: {str(e)}")
            return None

    def print_backtest_results(self):
        """백테스트 결과를 출력합니다."""
        try:
            # 다양한 기간에 대해 백테스트 수행
            periods = [6, 12, 24, 36]

            print("\n=== 버핏 지표 백테스트 결과 ===")
            for months in periods:
                print(f"\n{months}개월 후 수익률 분석:")
                results = self.backtest_indicator(months)
                if results is not None:
                    pd.set_option("display.float_format", "{:.2f}".format)
                    print(results.to_string(index=False))
                else:
                    print("백테스트 실패")

            # 현재 상태 출력
            current_status = self.get_current_status()
            if current_status:
                print("\n현재 시장 상태:")
                print(f"Z-Score: {current_status['zscore']:.2f}")
                print(f"시장 상태: {current_status['market_status']}")

        except Exception as e:
            logger.error(f"결과 출력 중 오류 발생: {str(e)}")


if __name__ == "__main__":
    # 백테스트 실행
    print("Running Buffett Indicator backtest...")
    indicator = BuffettIndicator()
    indicator.print_backtest_results()
