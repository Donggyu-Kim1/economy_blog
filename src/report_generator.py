import os
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
import sys

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.data_processor import DataProcessor
from src.markdown_builder import MarkdownBuilder
from src.logger import logger
from utils.us_market import get_all_us_market_data
from utils.kr_market import get_all_kr_market_data
from utils.us_treasury import get_all_treasury_data
from utils.forex import get_all_forex_data
from utils.news import get_all_news
from utils.calendar import EconomicCalendar
from config.settings import DATE_FORMAT


class ReportGenerator:
    """시장 리포트 생성을 총괄하는 클래스"""

    def __init__(self, date: Optional[str] = None):
        """
        Args:
            date: 리포트 생성 날짜 (기본값: 오늘)
        """
        self.date = date or datetime.now(timezone(timedelta(hours=9))).strftime(
            DATE_FORMAT
        )
        self.processor = DataProcessor()
        self.builder = MarkdownBuilder(self.date)
        self.calendar = EconomicCalendar()

    def collect_data(self) -> Dict[str, Any]:
        """모든 필요한 데이터 수집"""
        logger.info(f"데이터 수집 시작: {self.date}")
        data = {}

        try:
            # 미국 시장 데이터 수집
            data["us_market"] = get_all_us_market_data()
            logger.log_data_collection("미국 시장", bool(data["us_market"]))

            # 한국 시장 데이터 수집
            data["kr_market"] = get_all_kr_market_data()
            logger.log_data_collection("한국 시장", bool(data["kr_market"]))

            # 미국 국채 데이터 수집
            data["us_treasury"] = get_all_treasury_data()
            logger.log_data_collection("미국 국채", bool(data["us_treasury"]))

            # 환율 데이터 수집
            data["forex"] = get_all_forex_data()
            logger.log_data_collection("환율", bool(data["forex"]))

            # 뉴스 데이터 수집
            data["news"] = get_all_news()
            logger.log_data_collection("뉴스", bool(data["news"]))

            # 경제 지표 데이터 수집
            data["calendar"] = self.calendar.get_recent_data()
            logger.log_data_collection("경제 지표", bool(data["calendar"]))

        except Exception as e:
            logger.error("데이터 수집 중 에러 발생", exc_info=e)
            raise

        return data

    def process_data(self, data: Dict[str, Any]) -> Dict[str, str]:
        """수집된 데이터 처리"""
        logger.info("데이터 처리 시작")
        processed = {}

        try:
            # 각 섹션별 데이터 처리
            processed["us_market_summary"] = self.processor.process_us_market_data(
                data["us_market"]
            )
            logger.log_process_step("미국 시장 분석", True)

            processed["kr_market_summary"] = self.processor.process_kr_market_data(
                data["kr_market"]
            )
            logger.log_process_step("한국 시장 분석", True)

            processed["us_treasury_summary"] = self.processor.process_us_treasury_data(
                data["us_treasury"]
            )
            logger.log_process_step("미국 국채 분석", True)

            processed["forex_summary"] = self.processor.process_forex_data(
                data["forex"]
            )
            logger.log_process_step("환율 분석", True)

            processed["news_summary"] = self.processor.process_news_data(data["news"])
            logger.log_process_step("뉴스 분석", True)

            processed["calendar_summary"] = self.processor.process_economic_calendar(
                data["calendar"]
            )
            logger.log_process_step("경제 지표 분석", True)

        except Exception as e:
            logger.error("데이터 처리 중 에러 발생", exc_info=e)
            raise

        return processed

    def generate_report(self) -> str:
        """최종 리포트 생성"""
        try:
            # 데이터 수집
            data = self.collect_data()
            logger.info("데이터 수집 완료")

            # 데이터 처리
            processed_data = self.process_data(data)
            logger.info("데이터 처리 완료")

            # 리포트 생성
            report_path = self.builder.build_report(
                us_market_data=data["us_market"],
                us_market_summary=processed_data["us_market_summary"],
                us_treasury_data=data["us_treasury"],
                us_treasury_summary=processed_data["us_treasury_summary"],
                kr_market_data=data["kr_market"],
                kr_market_summary=processed_data["kr_market_summary"],
                forex_data=data["forex"],
                forex_summary=processed_data["forex_summary"],
                news_summary=processed_data["news_summary"],
                calendar_summary=processed_data["calendar_summary"],
            )

            # 리포트 저장
            saved_path = self.builder.save_report(report_path)
            logger.log_report_generation(True, saved_path)

            return saved_path

        except Exception as e:
            logger.error("리포트 생성 중 에러 발생", exc_info=e)
            logger.log_report_generation(False)
            raise


def generate_daily_report(date: Optional[str] = None) -> str:
    """
    일일 시장 리포트 생성 헬퍼 함수

    Args:
        date: 리포트 생성 날짜 (기본값: 오늘)

    Returns:
        str: 생성된 리포트 파일 경로
    """
    generator = ReportGenerator(date)
    return generator.generate_report()


if __name__ == "__main__":
    # 리포트 생성 테스트
    print("리포트 생성 테스트 시작...")
    try:
        report_path = generate_daily_report()
        print(f"리포트 생성 완료: {report_path}")
    except Exception as e:
        print(f"리포트 생성 실패: {str(e)}")
