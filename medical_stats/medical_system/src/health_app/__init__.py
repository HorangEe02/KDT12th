"""
health_app 패키지
건강 상태 체크 & 관리 시스템

Author: KDT12 Python Project
Date: 2026-01-09
"""

from .health_checker import HealthChecker
from .data_manager import HealthDataManager

# GUI는 tkinter가 있을 때만 import
try:
    from .health_gui import HealthCheckApp
    __all__ = ['HealthChecker', 'HealthDataManager', 'HealthCheckApp']
except ImportError:
    __all__ = ['HealthChecker', 'HealthDataManager']
