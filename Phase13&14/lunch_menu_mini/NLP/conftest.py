"""
Pytest root conftest — NLP 디렉토리를 sys.path 에 추가하여
`from nlp_mvp.xxx import ...` 가 작동하도록 한다.

setup.py 없이도 테스트가 돌아가도록 하기 위한 shim.
"""
import sys
from pathlib import Path

_NLP_ROOT = Path(__file__).parent.resolve()
if str(_NLP_ROOT) not in sys.path:
    sys.path.insert(0, str(_NLP_ROOT))
