"""
patient_app 패키지
환자 정보 관리 시스템 (CRUD)

Author: KDT12 Python Project
Date: 2026-01-09
"""

from .patient import Patient
from .patient_manager import PatientManager

# GUI는 tkinter가 있을 때만 import
try:
    from .patient_gui import PatientManagementApp
    __all__ = ['Patient', 'PatientManager', 'PatientManagementApp']
except ImportError:
    __all__ = ['Patient', 'PatientManager']
