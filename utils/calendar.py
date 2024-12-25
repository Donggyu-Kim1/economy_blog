from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from zoneinfo import ZoneInfo
from webdriver_manager.chrome import ChromeDriverManager
import time


class EconomicCalendar:
    def __init__(self):
        self.base_url = "https://www.investing.com/economic-calendar/"
        self.seen_events = set()

    def get_search_dates(self) -> tuple[datetime, datetime]:
        """
        한국시간 기준으로 오늘 0시부터 다음날 23:59까지의 데이터를 얻기 위한
        ET 검색 날짜 범위를 반환

        Returns:
            tuple[datetime, datetime]: 검색 시작일과 종료일 (ET 기준)
        """
        # 현재 한국 시간
        now_kst = datetime.now(ZoneInfo("Asia/Seoul"))

        # 한국 시간으로 오늘 자정
        kst_start = now_kst.replace(hour=0, minute=0, second=0, microsecond=0)

        # 한국 시간으로 다음날 23:59:59
        kst_end = (kst_start + timedelta(days=1)).replace(hour=23, minute=59, second=59)

        # KST를 ET로 변환
        et_start = kst_start.astimezone(ZoneInfo("America/New_York"))
        et_end = kst_end.astimezone(ZoneInfo("America/New_York"))

        # ET 시작시간을 전날 10시로 조정
        et_start = (et_start - timedelta(days=1)).replace(
            hour=10, minute=0, second=0, microsecond=0
        )

        print(f"KST range: {kst_start} ~ {kst_end}")
        print(f"ET range: {et_start} ~ {et_end}")

        return et_start, et_end

    def setup_driver(self):
        """크롬 드라이버 설정"""
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920x1080")
            options.add_argument("--enable-javascript")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--ignore-certificate-errors")
            options.add_argument("--ignore-ssl-errors")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)

            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)

            stealth(
                driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
            )

            return driver
        except Exception as e:
            print(f"Error setting up driver: {str(e)}")
            raise

    def set_date_range(self, driver):
        """날짜 범위 설정"""
        try:
            # ET 기준 검색 날짜 계산
            et_start, et_end = self.get_search_dates()

            # 날짜 문자열 포맷
            start_str = et_start.strftime("%Y-%m-%d")
            end_str = et_end.strftime("%Y-%m-%d")
            print(f"Selecting date range: {start_str} ~ {end_str}")

            # URL에 직접 날짜 파라미터 추가
            date_params = f"?dateFrom={start_str}&dateTo={end_str}"
            new_url = self.base_url + date_params
            driver.get(new_url)
            time.sleep(3)

        except Exception as e:
            print(f"Error setting date range: {str(e)}")

    def extract_event_data(self, event) -> Optional[Dict[str, Any]]:
        """이벤트 데이터 추출 및 KST로 변환"""
        try:
            cells = event.find_elements(By.TAG_NAME, "td")
            if len(cells) < 8:
                return None

            # ET 시간 추출 및 KST로 변환
            date_str = event.get_attribute("data-event-datetime")
            if date_str:
                try:
                    # ET 시간을 KST로 변환
                    et_time = datetime.strptime(date_str, "%Y/%m/%d %H:%M:%S")
                    et_time = et_time.replace(tzinfo=ZoneInfo("America/New_York"))
                    kst_time = et_time.astimezone(ZoneInfo("Asia/Seoul"))
                    time_str = kst_time.strftime("%H:%M")
                    date_str = kst_time.strftime("%Y-%m-%d")
                except ValueError:
                    time_str = cells[0].text.strip()
                    date_str = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d")
            else:
                time_str = cells[0].text.strip()
                date_str = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d")

            event_data = {
                "time": time_str,
                "date": date_str,
                "country": cells[1].text.strip(),
                "event": cells[3].text.strip(),
                "importance": "",
                "actual": cells[4].text.strip() or "N/A",
                "forecast": cells[5].text.strip() or "N/A",
                "previous": cells[6].text.strip() or "N/A",
            }

            # 중요도 추출
            try:
                importance_cell = cells[2]
                cell_html = importance_cell.get_attribute("innerHTML")
                importance_level = cell_html.count("grayFullBullishIcon")
                event_data["importance"] = (
                    "⭐" * importance_level if importance_level > 0 else ""
                )
            except Exception as e:
                print(f"Error extracting importance: {str(e)}")

            return event_data

        except Exception as e:
            print(f"Error extracting event data: {str(e)}")
            return None

    def get_important_events(self) -> List[Dict[str, Any]]:
        """경제 지표 수집"""
        driver = None
        events = []

        try:
            driver = self.setup_driver()
            driver.get(self.base_url)

            # 기본 설정 및 필터 적용
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "economic-calendar"))
            )

            # 쿠키 수락
            try:
                WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
                ).click()
                time.sleep(2)
            except:
                print("No cookie button or already accepted")

            # 날짜 범위 설정
            self.set_date_range(driver)

            # 이벤트 수집
            print("Collecting events...")
            selectors = [
                "tr.js-event-item",
                "#economicCalendarData tbody tr[data-event-datetime]",
                "#economicCalendarData tbody tr:not(.tablesorter-headerRow):not(.theDay)",
            ]

            for selector in selectors:
                try:
                    found_events = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                    )
                    print(
                        f"\nFound {len(found_events)} events with selector: {selector}"
                    )

                    for event in found_events:
                        try:
                            driver.execute_script(
                                "arguments[0].scrollIntoView(true);", event
                            )
                            time.sleep(0.1)

                            event_data = self.extract_event_data(event)
                            if event_data:
                                event_key = (
                                    f"{event_data['date']}-{event_data['time']}-"
                                    f"{event_data['country']}-{event_data['event']}"
                                )
                                if event_key not in self.seen_events:
                                    self.seen_events.add(event_key)
                                    events.append(event_data)
                                    print(f"Extracted event data: {event_data}")
                        except Exception as e:
                            print(f"Error processing event: {str(e)}")
                            continue

                except Exception as e:
                    print(f"Error with selector {selector}: {str(e)}")
                    continue

            return events

        except Exception as e:
            print(f"Error collecting economic calendar: {str(e)}")
            return []

        finally:
            if driver:
                driver.quit()

    def format_events(self, events: List[Dict[str, Any]]) -> str:
        """이벤트 포맷팅"""
        if not events:
            return "예정된 주요 경제 지표가 없습니다."

        # 현재 한국 시간
        now_kst = datetime.now(ZoneInfo("Asia/Seoul"))
        target_date = now_kst.strftime("%Y-%m-%d")
        next_date = (now_kst + timedelta(days=1)).strftime("%Y-%m-%d")

        # 헤더 추가
        formatted = [f"{target_date} ~ {next_date} 경제 지표 일정\n"]

        # 중요 이벤트 필터링 (⭐⭐ 이상)
        important_events = [
            event for event in events if event["importance"].count("⭐") >= 2
        ]

        if not important_events:
            return "예정된 주요 경제 지표가 없습니다."

        # 날짜별로 이벤트 그룹화
        events_by_date = {}
        for event in important_events:
            date = event["date"]
            # 타겟 날짜의 데이터만 포함
            if date in [target_date, next_date]:
                if date not in events_by_date:
                    events_by_date[date] = []
                events_by_date[date].append(event)

        # 날짜별로 정렬된 이벤트 포맷팅
        for date in sorted(events_by_date.keys()):
            formatted.append(f"\n[{date}]")

            # 해당 날짜의 이벤트를 시간순으로 정렬
            day_events = sorted(events_by_date[date], key=lambda x: x["time"])

            for event in day_events:
                formatted.append(
                    f"{event['time']} [{event['country']}] {event['importance']} {event['event']}"
                )
                if event["actual"] != "N/A":
                    formatted.append(f"  발표: {event['actual']}")
                if event["forecast"] != "N/A":
                    formatted.append(f"  예상: {event['forecast']}")
                if event["previous"] != "N/A":
                    formatted.append(f"  이전: {event['previous']}")
                formatted.append("")

        return "\n".join(formatted).strip()


if __name__ == "__main__":
    calendar = EconomicCalendar()

    print("Testing economic calendar crawler...")
    try:
        events = calendar.get_important_events()
        print(calendar.format_events(events))
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
