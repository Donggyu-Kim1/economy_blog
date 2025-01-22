import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.logger import logger


class OptionAnalyzer:
    """옵션 데이터 분석 클래스"""

    def analyze_put_call_ratios(self, option_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Put/Call Ratio 분석

        Args:
            option_data: {
                'expiry': str,
                'calls': DataFrame,
                'puts': DataFrame,
                'underlying_price': float
            }

        Returns:
            Dict[str, Any]: {
                'volume_ratio': float,    # 거래량 기준 P/C ratio
                'oi_ratio': float,        # 미결제약정 기준 P/C ratio
                'signal': str,            # 신호 (BULLISH/BEARISH/NEUTRAL)
                'strength': float         # 신호 강도 (0~1)
            }
        """
        try:
            calls = option_data["calls"]
            puts = option_data["puts"]

            if calls.empty or puts.empty:
                return self._empty_ratio_result()

            # 거래량 기준 P/C ratio
            call_volume = calls["volume"].sum()
            put_volume = puts["volume"].sum()
            volume_ratio = put_volume / call_volume if call_volume > 0 else 0

            # 미결제약정 기준 P/C ratio
            call_oi = calls["openInterest"].sum()
            put_oi = puts["openInterest"].sum()
            oi_ratio = put_oi / call_oi if call_oi > 0 else 0

            # 신호 및 강도 계산
            volume_signal = self._get_signal(volume_ratio)
            oi_signal = self._get_signal(oi_ratio)

            # 최종 신호 결정 (거래량과 미결제약정 신호의 조합)
            if volume_signal == oi_signal:
                final_signal = volume_signal
                strength = max(
                    self._get_signal_strength(volume_ratio),
                    self._get_signal_strength(oi_ratio),
                )
            else:
                # 거래량에 더 높은 가중치 부여
                final_signal = volume_signal
                strength = self._get_signal_strength(volume_ratio) * 0.7

            return {
                "volume_ratio": volume_ratio,
                "oi_ratio": oi_ratio,
                "volume_signal": volume_signal,
                "oi_signal": oi_signal,
                "final_signal": final_signal,
                "strength": strength,
            }

        except Exception as e:
            logger.error(f"P/C ratio 분석 중 오류 발생: {str(e)}")
            return self._empty_ratio_result()

    def analyze_skew(self, option_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        옵션 스큐 분석

        Args:
            option_data: 단일 만기 옵션 데이터

        Returns:
            Dict[str, Any]: 스큐 분석 결과
        """
        try:
            calls = option_data["calls"]
            puts = option_data["puts"]
            underlying_price = option_data["underlying_price"]

            if calls.empty or puts.empty or not underlying_price:
                return self._empty_skew_result()

            # ATM 옵션 찾기
            calls["moneyness"] = calls["strike"] / underlying_price - 1
            puts["moneyness"] = puts["strike"] / underlying_price - 1

            # IV 데이터가 있는 경우만 분석
            if "impliedVolatility" not in calls.columns:
                return self._empty_skew_result()

            # ATM IV (moneyness ±1% 이내)
            atm_options = pd.concat(
                [
                    calls[abs(calls["moneyness"]) < 0.01],
                    puts[abs(puts["moneyness"]) < 0.01],
                ]
            )
            atm_iv = atm_options["impliedVolatility"].mean()

            # OTM 풋옵션 IV (90% ~ 95% moneyness)
            otm_puts = puts[(-0.1 < puts["moneyness"]) & (puts["moneyness"] < -0.05)]
            otm_put_iv = otm_puts["impliedVolatility"].mean()

            # OTM 콜옵션 IV (105% ~ 110% moneyness)
            otm_calls = calls[(0.05 < calls["moneyness"]) & (calls["moneyness"] < 0.1)]
            otm_call_iv = otm_calls["impliedVolatility"].mean()

            # 스큐 측정
            put_skew = (
                (otm_put_iv - atm_iv)
                if pd.notna(otm_put_iv) and pd.notna(atm_iv)
                else 0
            )
            call_skew = (
                (otm_call_iv - atm_iv)
                if pd.notna(otm_call_iv) and pd.notna(atm_iv)
                else 0
            )
            skew_level = put_skew - call_skew

            return {
                "atm_iv": atm_iv,
                "otm_put_iv": otm_put_iv,
                "otm_call_iv": otm_call_iv,
                "put_skew": put_skew,
                "call_skew": call_skew,
                "skew_level": skew_level,
                "trend": self._get_skew_trend(skew_level),
            }

        except Exception as e:
            logger.error(f"스큐 분석 중 오류 발생: {str(e)}")
            return self._empty_skew_result()

    def analyze_term_structure(
        self, options_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        옵션 기간 구조 분석

        Args:
            options_data: 여러 만기의 옵션 데이터 리스트

        Returns:
            Dict[str, Any]: 기간 구조 분석 결과
        """
        try:
            if not options_data:
                return self._empty_term_result()

            # 만기별 ATM IV 계산
            term_structure = []
            for data in options_data:
                expiry = data["expiry"]
                skew_analysis = self.analyze_skew(data)

                if pd.notna(skew_analysis["atm_iv"]):
                    term_structure.append(
                        {
                            "expiry": datetime.strptime(expiry, "%Y-%m-%d"),
                            "atm_iv": skew_analysis["atm_iv"],
                        }
                    )

            if not term_structure:
                return self._empty_term_result()

            # 만기순으로 정렬
            term_structure.sort(key=lambda x: x["expiry"])

            # 기울기 계산 (근월물 대비 원월물 IV 차이)
            iv_slope = term_structure[-1]["atm_iv"] - term_structure[0]["atm_iv"]
            days_between = (
                term_structure[-1]["expiry"] - term_structure[0]["expiry"]
            ).days
            term_slope = iv_slope / days_between if days_between > 0 else 0

            return {
                "term_structure": term_structure,
                "slope": term_slope,
                "trend": self._get_term_trend(term_slope),
            }

        except Exception as e:
            logger.error(f"기간 구조 분석 중 오류 발생: {str(e)}")
            return self._empty_term_result()

    def _get_signal(self, ratio: float) -> str:
        """P/C ratio 기반 신호 생성"""
        if ratio > 1.2:
            return "BEARISH"
        elif ratio < 0.8:
            return "BULLISH"
        else:
            return "NEUTRAL"

    def _get_signal_strength(self, ratio: float) -> float:
        """신호 강도 계산 (0~1)"""
        if ratio > 1.2:
            return min((ratio - 1.2) / 0.8, 1.0)
        elif ratio < 0.8:
            return min((0.8 - ratio) / 0.4, 1.0)
        else:
            return 0.0

    def _get_skew_trend(self, skew_level: float) -> str:
        """스큐 추세 판단"""
        if abs(skew_level) < 0.02:
            return "NEUTRAL"
        elif skew_level > 0:
            return "LEFT_SKEWED"
        else:
            return "RIGHT_SKEWED"

    def _get_term_trend(self, slope: float) -> str:
        """기간 구조 추세 판단"""
        if abs(slope) < 0.0001:
            return "FLAT"
        elif slope > 0:
            return "CONTANGO"
        else:
            return "BACKWARDATION"

    def _empty_ratio_result(self) -> Dict[str, Any]:
        """빈 P/C ratio 결과"""
        return {
            "volume_ratio": 0.0,
            "oi_ratio": 0.0,
            "volume_signal": "UNKNOWN",
            "oi_signal": "UNKNOWN",
            "final_signal": "UNKNOWN",
            "strength": 0.0,
        }

    def _empty_skew_result(self) -> Dict[str, Any]:
        """빈 스큐 분석 결과"""
        return {
            "atm_iv": 0.0,
            "otm_put_iv": 0.0,
            "otm_call_iv": 0.0,
            "put_skew": 0.0,
            "call_skew": 0.0,
            "skew_level": 0.0,
            "trend": "UNKNOWN",
        }

    def _empty_term_result(self) -> Dict[str, Any]:
        """빈 기간 구조 분석 결과"""
        return {"term_structure": [], "slope": 0.0, "trend": "UNKNOWN"}


def analyze_market_options(
    market_data: Dict[str, List[Dict[str, Any]]]
) -> Dict[str, Dict[str, Any]]:
    """
    시장 전체 옵션 데이터 분석

    Args:
        market_data: get_market_option_data()의 반환값

    Returns:
        Dict[str, Dict[str, Any]]: 지수별 분석 결과
    """
    analyzer = OptionAnalyzer()
    analysis_results = {}

    for index_name, options_data in market_data.items():
        try:
            if not options_data:
                continue

            # 가장 가까운 만기 데이터로 P/C ratio와 스큐 분석
            nearest_expiry = options_data[0]
            pc_ratios = analyzer.analyze_put_call_ratios(nearest_expiry)
            skew = analyzer.analyze_skew(nearest_expiry)

            # 전체 만기 데이터로 기간 구조 분석
            term_structure = analyzer.analyze_term_structure(options_data)

            analysis_results[index_name] = {
                "ratios": pc_ratios,
                "skew": skew,
                "term_structure": term_structure,
            }

            logger.info(f"{index_name} 옵션 분석 완료")

        except Exception as e:
            logger.error(f"{index_name} 옵션 분석 중 오류 발생: {str(e)}")
            continue

    return analysis_results


if __name__ == "__main__":
    from utils.option_data import get_market_option_data

    print("Testing option analysis...")
    try:
        # 월간 데이터로 테스트
        market_data = get_market_option_data(expiry_type="monthly", periods=3)
        analysis = analyze_market_options(market_data)

        for index_name, results in analysis.items():
            print(f"\n{index_name} Analysis Results:")
            print(
                f"P/C Ratio Signal: {results['ratios']['final_signal']} (Strength: {results['ratios']['strength']:.2f})"
            )
            print(f"Skew Trend: {results['skew']['trend']}")
            print(f"Term Structure: {results['term_structure']['trend']}")

    except Exception as e:
        print(f"Test failed with error: {str(e)}")
