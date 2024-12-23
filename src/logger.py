import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional
import sys

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)


class MarketReportLogger:
    """시장 리포트 생성 관련 로깅을 처리하는 클래스"""

    def __init__(self, log_directory: Optional[str] = None):
        """
        Args:
            log_directory: 로그 파일을 저장할 디렉토리 (기본값: project_root/logs)
        """
        # 로그 디렉토리 설정
        self.log_directory = log_directory or os.path.join(project_root, "logs")
        os.makedirs(self.log_directory, exist_ok=True)

        # 로거 생성
        self.logger = logging.getLogger("MarketReport")
        self.logger.setLevel(logging.DEBUG)

        # 이미 핸들러가 설정되어 있다면 초기화
        if self.logger.handlers:
            self.logger.handlers.clear()

        # 파일 핸들러 설정 (일별 로그 파일)
        log_file = os.path.join(
            self.log_directory, f"market_report_{datetime.now().strftime('%Y%m')}.log"
        )
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"  # 10MB
        )
        file_handler.setLevel(logging.DEBUG)

        # 콘솔 핸들러 설정
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 포맷터 설정
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 핸들러 추가
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def info(self, message: str):
        """정보 레벨 로그 기록"""
        self.logger.info(message)

    def error(self, message: str, exc_info: Optional[Exception] = None):
        """에러 레벨 로그 기록"""
        if exc_info:
            self.logger.error(message, exc_info=True)
        else:
            self.logger.error(message)

    def warning(self, message: str):
        """경고 레벨 로그 기록"""
        self.logger.warning(message)

    def debug(self, message: str):
        """디버그 레벨 로그 기록"""
        self.logger.debug(message)

    def log_data_collection(self, data_type: str, status: bool, details: str = ""):
        """데이터 수집 과정 로깅"""
        if status:
            self.info(f"{data_type} 데이터 수집 완료: {details}")
        else:
            self.error(f"{data_type} 데이터 수집 실패: {details}")

    def log_report_generation(self, status: bool, report_path: Optional[str] = None):
        """리포트 생성 과정 로깅"""
        if status:
            self.info(f"리포트 생성 완료: {report_path}")
        else:
            self.error("리포트 생성 실패")

    def log_process_step(self, step_name: str, status: bool, details: str = ""):
        """처리 단계별 로깅"""
        if status:
            self.info(f"처리 단계 '{step_name}' 완료: {details}")
        else:
            self.error(f"처리 단계 '{step_name}' 실패: {details}")


# 싱글톤 인스턴스 생성
logger = MarketReportLogger()


if __name__ == "__main__":
    # 로거 테스트
    print("Testing logger...")

    try:
        # 정상 케이스 테스트
        logger.info("테스트 시작")
        logger.debug("상세 디버그 정보")
        logger.log_data_collection("미국 시장", True, "S&P 500 데이터 수집")
        logger.log_process_step("데이터 처리", True, "시장 데이터 분석 완료")
        logger.log_report_generation(True, "/path/to/report.md")

        # 에러 케이스 테스트
        try:
            raise ValueError("테스트 에러 발생")
        except Exception as e:
            logger.error("에러 발생", exc_info=e)

        logger.warning("처리 지연 발생")
        logger.info("테스트 종료")

        print(
            "로그 파일 위치:",
            os.path.join(
                logger.log_directory,
                f"market_report_{datetime.now().strftime('%Y%m')}.log",
            ),
        )

    except Exception as e:
        print(f"테스트 실패: {str(e)}")
