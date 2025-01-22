import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
import sys
import os
from dateutil.relativedelta import relativedelta

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.logger import logger


class OptionDataCollector:
    """옵션 데이터 수집 클래스"""

    def __init__(self, symbol: str = "^SPX"):
        """
        Args:
            symbol (str): 기초자산 티커 심볼 (기본값: S&P 500)
        """
        self.symbol = symbol
        self.ticker = yf.Ticker(symbol)

    def get_expiry_dates(self) -> List[str]:
        """사용 가능한 모든 만기일 조회"""
        try:
            return self.ticker.options
        except Exception as e:
            logger.error(f"만기일 목록 조회 중 오류 발생: {str(e)}")
            return []

    def get_option_chain(self, expiry: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """특정 만기의 옵션 체인 데이터 수집

        Args:
            expiry (str): 만기일 (YYYY-MM-DD 형식)

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: (콜옵션 DataFrame, 풋옵션 DataFrame)
        """
        try:
            chains = self.ticker.option_chain(expiry)
            return chains.calls, chains.puts
        except Exception as e:
            logger.error(f"옵션 체인 데이터 수집 중 오류 발생 ({expiry}): {str(e)}")
            return pd.DataFrame(), pd.DataFrame()

    def get_nearest_expiry_data(self) -> Dict[str, Any]:
        """가장 가까운 만기의 옵션 데이터 수집"""
        try:
            expiry_dates = self.get_expiry_dates()
            if not expiry_dates:
                return self._empty_result()

            # 가장 가까운 만기 선택
            nearest_expiry = expiry_dates[0]
            calls, puts = self.get_option_chain(nearest_expiry)

            return {
                "expiry": nearest_expiry,
                "calls": calls,
                "puts": puts,
                "underlying_price": self._get_current_price(),
            }
        except Exception as e:
            logger.error(f"근월물 데이터 수집 중 오류 발생: {str(e)}")
            return self._empty_result()

    def get_monthly_expiry_data(self, months: int = 3) -> List[Dict[str, Any]]:
        """월간 옵션 데이터 수집

        Args:
            months (int): 수집할 개월 수

        Returns:
            List[Dict[str, Any]]: 월물별 옵션 데이터 리스트
        """
        try:
            all_expiries = self.get_expiry_dates()
            if not all_expiries:
                return []

            # 현재 날짜 기준으로 각 월의 마지막 금요일에 해당하는 만기 필터링
            monthly_data = []
            current_date = datetime.now()
            target_dates = []

            for i in range(months):
                target_date = current_date + relativedelta(months=i)
                # 해당 월의 마지막 금요일 찾기
                last_day = target_date.replace(day=1) + relativedelta(months=1, days=-1)
                offset = (4 - last_day.weekday()) % 7  # 금요일이 되기 위한 차이
                monthly_expiry = last_day - timedelta(days=offset)
                target_dates.append(monthly_expiry.strftime("%Y-%m-%d"))

            # 실제 거래되는 월물 중에서 target_dates와 가장 가까운 만기 선택
            for target in target_dates:
                closest_expiry = min(
                    all_expiries,
                    key=lambda x: abs(
                        datetime.strptime(x, "%Y-%m-%d")
                        - datetime.strptime(target, "%Y-%m-%d")
                    ),
                )

                calls, puts = self.get_option_chain(closest_expiry)
                if not calls.empty and not puts.empty:
                    monthly_data.append(
                        {
                            "expiry": closest_expiry,
                            "calls": calls,
                            "puts": puts,
                            "underlying_price": self._get_current_price(),
                        }
                    )

            return monthly_data

        except Exception as e:
            logger.error(f"월물 데이터 수집 중 오류 발생: {str(e)}")
            return []

    def get_weekly_expiry_data(self, weeks: int = 4) -> List[Dict[str, Any]]:
        """주간 옵션 데이터 수집

        Args:
            weeks (int): 수집할 주 수

        Returns:
            List[Dict[str, Any]]: 주간 옵션 데이터 리스트
        """
        try:
            all_expiries = self.get_expiry_dates()
            weekly_data = []

            # 현재부터 지정된 주 수만큼의 데이터만 수집
            for expiry in all_expiries[:weeks]:
                calls, puts = self.get_option_chain(expiry)
                if not calls.empty and not puts.empty:
                    weekly_data.append(
                        {
                            "expiry": expiry,
                            "calls": calls,
                            "puts": puts,
                            "underlying_price": self._get_current_price(),
                        }
                    )

            return weekly_data

        except Exception as e:
            logger.error(f"주간 데이터 수집 중 오류 발생: {str(e)}")
            return []

    def get_all_expiry_data(self) -> List[Dict[str, Any]]:
        """모든 만기의 옵션 데이터 수집"""
        try:
            all_data = []
            current_price = self._get_current_price()

            for expiry in self.get_expiry_dates():
                calls, puts = self.get_option_chain(expiry)
                if not calls.empty and not puts.empty:
                    all_data.append(
                        {
                            "expiry": expiry,
                            "calls": calls,
                            "puts": puts,
                            "underlying_price": current_price,
                        }
                    )

            return all_data

        except Exception as e:
            logger.error(f"전체 데이터 수집 중 오류 발생: {str(e)}")
            return []

    def _get_current_price(self) -> float:
        """기초자산의 현재 가격 조회"""
        try:
            return self.ticker.history(period="1d")["Close"].iloc[-1]
        except Exception as e:
            logger.error(f"현재가 조회 중 오류 발생: {str(e)}")
            return 0.0

    def _empty_result(self) -> Dict[str, Any]:
        """빈 결과 반환"""
        return {
            "expiry": None,
            "calls": pd.DataFrame(),
            "puts": pd.DataFrame(),
            "underlying_price": 0.0,
        }


def get_market_option_data(
    expiry_type: str = "nearest", periods: int = 1
) -> Dict[str, List[Dict[str, Any]]]:
    """주요 시장 지수의 옵션 데이터 수집

    Args:
        expiry_type (str): 만기 유형 ('nearest', 'weekly', 'monthly', 'all')
        periods (int): 수집할 기간 수 (weekly의 경우 주 수, monthly의 경우 월 수)

    Returns:
        Dict[str, List[Dict[str, Any]]]: 지수별 옵션 데이터
    """
    indices = {
        "SPX": "^SPX",  # S&P 500
        "NDX": "^NDX",  # NASDAQ 100
        "VIX": "^VIX",  # VIX
    }

    market_data = {}

    for name, symbol in indices.items():
        try:
            collector = OptionDataCollector(symbol)

            # 만기 유형에 따른 데이터 수집
            if expiry_type == "nearest":
                data = [collector.get_nearest_expiry_data()]
            elif expiry_type == "weekly":
                data = collector.get_weekly_expiry_data(weeks=periods)
            elif expiry_type == "monthly":
                data = collector.get_monthly_expiry_data(months=periods)
            elif expiry_type == "all":
                data = collector.get_all_expiry_data()
            else:
                logger.error(f"잘못된 만기 유형: {expiry_type}")
                continue

            if data:
                market_data[name] = data
                logger.info(f"{name} 옵션 데이터 수집 완료 (유형: {expiry_type})")
            else:
                logger.warning(f"{name} 옵션 데이터 없음 (유형: {expiry_type})")

        except Exception as e:
            logger.error(f"{name} 옵션 데이터 수집 실패: {str(e)}")
            market_data[name] = []

    return market_data


if __name__ == "__main__":
    # 모듈 테스트
    print("Testing option data collection...")
    try:
        # 근월물 데이터 테스트
        print("\nNearest expiry data:")
        data = get_market_option_data(expiry_type="nearest")
        for index_name, option_data in data.items():
            if option_data:
                print(f"{index_name}: {option_data[0]['expiry']}")

        # 월간 데이터 테스트
        print("\nMonthly expiry data (3 months):")
        data = get_market_option_data(expiry_type="monthly", periods=3)
        for index_name, option_data in data.items():
            if option_data:
                print(f"{index_name}: {[d['expiry'] for d in option_data]}")

    except Exception as e:
        print(f"Test failed with error: {str(e)}")
