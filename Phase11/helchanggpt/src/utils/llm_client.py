"""
llm_client.py
Ollama 기반 LLM 클라이언트 통합 모듈.

Ollama의 OpenAI 호환 API (localhost:11434/v1)를 활용하여
로컬 모델과 OpenAI API를 동일한 인터페이스로 사용합니다.

지원 모델:
  - Ollama 로컬: exaone3.5, exaone-deep, qwen3.5, gemma4 등
  - OpenAI API: gpt-4o, gpt-4o-mini 등 (API 키 필요)

비전(Vision) 지원 모델:
  - gemma4 (e4b, 26b)
  - qwen2.5vl (추가 다운로드 권장)

사용법:
    client = LLMClient()
    response = client.chat("exaone3.5", "안녕하세요")
    response = client.chat_with_image("gemma4", "이미지 설명", image_path="inbody.png")
"""

import base64
import json
import os
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ModelProvider(Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"


@dataclass
class ModelConfig:
    """모델 설정"""
    name: str                          # Ollama 모델명 또는 OpenAI 모델명
    provider: ModelProvider            # ollama or openai
    display_name: str                  # 표시용 이름
    supports_vision: bool = False      # 비전 지원 여부
    supports_korean: int = 3           # 한국어 지원 수준 (1-3)
    size_gb: float = 0                 # 모델 크기 (GB)
    recommended_for: list[str] = field(default_factory=list)  # 추천 작업
    description: str = ""


# ═══════════════════════════════════════
# 사용 가능한 모델 레지스트리
# ═══════════════════════════════════════

AVAILABLE_MODELS: dict[str, ModelConfig] = {
    # ── Ollama 로컬 모델 ──
    "exaone3.5": ModelConfig(
        name="exaone3.5",
        provider=ModelProvider.OLLAMA,
        display_name="EXAONE 3.5 (LG AI)",
        supports_korean=3,
        size_gb=4.4,
        recommended_for=["텍스트분류", "NER", "감성분석", "식단생성", "운동루틴"],
        description="LG AI Research 한영 이중언어 모델. 한국어 작업에 가장 적합",
    ),
    "exaone-deep": ModelConfig(
        name="exaone-deep",
        provider=ModelProvider.OLLAMA,
        display_name="EXAONE Deep (LG AI)",
        supports_korean=3,
        size_gb=4.4,
        recommended_for=["추론", "분석", "복잡한질의"],
        description="EXAONE 기반 추론 특화 모델. 복잡한 분석/판단에 적합",
    ),
    "qwen3.5:9b": ModelConfig(
        name="qwen3.5:9b",
        provider=ModelProvider.OLLAMA,
        display_name="Qwen 3.5 9B (Alibaba)",
        supports_korean=2,
        size_gb=6.1,
        recommended_for=["식단생성", "운동루틴", "구조화생성"],
        description="201개 언어 지원. 구조화된 텍스트 생성에 강점",
    ),
    "qwen3.5:4b": ModelConfig(
        name="qwen3.5:4b",
        provider=ModelProvider.OLLAMA,
        display_name="Qwen 3.5 4B (Alibaba)",
        supports_korean=2,
        size_gb=3.2,
        recommended_for=["빠른추론", "경량작업"],
        description="경량 모델. 빠른 응답이 필요한 경우 적합",
    ),
    "gemma4": ModelConfig(
        name="gemma4",
        provider=ModelProvider.OLLAMA,
        display_name="Gemma 4 (Google)",
        supports_vision=True,
        supports_korean=2,
        size_gb=8.9,
        recommended_for=["이미지분석", "인바디파싱", "다국어"],
        description="Google 멀티모달 모델. 비전(이미지) 분석 지원",
    ),
    "gemma4:26b": ModelConfig(
        name="gemma4:26b",
        provider=ModelProvider.OLLAMA,
        display_name="Gemma 4 26B (Google)",
        supports_vision=True,
        supports_korean=2,
        size_gb=16.8,
        recommended_for=["이미지분석", "인바디파싱", "고품질생성"],
        description="Gemma 4 대형 모델. 더 높은 품질의 비전/생성",
    ),
    "bge-m3": ModelConfig(
        name="bge-m3",
        provider=ModelProvider.OLLAMA,
        display_name="BGE-M3 (Embedding)",
        supports_korean=3,
        size_gb=1.1,
        recommended_for=["임베딩", "유사도검색"],
        description="다국어 임베딩 모델. 운동 정보 검색에 활용",
    ),
    "gpt-oss:20b": ModelConfig(
        name="gpt-oss:20b",
        provider=ModelProvider.OLLAMA,
        display_name="GPT-OSS 20B",
        supports_korean=1,
        size_gb=12.8,
        recommended_for=["비교실험"],
        description="비교 실험용 보조 모델",
    ),
    "nemotron-cascade-2": ModelConfig(
        name="nemotron-cascade-2",
        provider=ModelProvider.OLLAMA,
        display_name="Nemotron Cascade 2 (NVIDIA)",
        supports_korean=1,
        size_gb=22.6,
        recommended_for=["비교실험"],
        description="NVIDIA 대형 모델. 비교 실험용",
    ),

    # ── OpenAI API 모델 (선택사항) ──
    "gpt-4o": ModelConfig(
        name="gpt-4o",
        provider=ModelProvider.OPENAI,
        display_name="GPT-4o (OpenAI)",
        supports_vision=True,
        supports_korean=3,
        recommended_for=["인바디파싱", "고품질생성", "비교실험"],
        description="OpenAI 최신 모델. API 키 필요",
    ),
    "gpt-4o-mini": ModelConfig(
        name="gpt-4o-mini",
        provider=ModelProvider.OPENAI,
        display_name="GPT-4o Mini (OpenAI)",
        supports_vision=True,
        supports_korean=3,
        recommended_for=["빠른추론", "비교실험"],
        description="OpenAI 경량 모델. API 키 필요",
    ),
}

# ── 작업별 기본 모델 배정 ──
DEFAULT_MODEL_ASSIGNMENTS = {
    "목표분류": "exaone3.5:7.8b",
    "NER": "exaone3.5:7.8b",
    "식단생성": "exaone3.5:7.8b",
    "운동루틴생성": "exaone3.5:7.8b",
    "감성분석": "exaone3.5:7.8b",
    "동기부여피드백": "exaone3.5:7.8b",
    "인바디파싱": "gemma4:e4b",
    "식단요약": "exaone3.5:2.4b",
    "키워드추출": "exaone3.5:2.4b",
    "운동정보검색_임베딩": "bge-m3",
}


class LLMClient:
    """
    Ollama/OpenAI 통합 LLM 클라이언트.

    Ollama의 OpenAI 호환 API를 활용하여 동일한 인터페이스를 제공합니다.

    Examples:
        >>> client = LLMClient()
        >>> response = client.chat("exaone3.5", "25세 남성 식단 추천해줘")
        >>> print(response)

        >>> # 비전 (인바디 파싱)
        >>> response = client.chat_with_image("gemma4", "인바디 수치를 읽어줘", "inbody.png")
    """

    def __init__(
        self,
        ollama_base_url: str = "http://localhost:11434/v1",
        openai_api_key: str | None = None,
    ):
        self.ollama_base_url = ollama_base_url
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self._clients: dict[str, Any] = {}

    def _get_client(self, provider: ModelProvider):
        """프로바이더별 OpenAI 클라이언트를 반환합니다."""
        from openai import OpenAI

        if provider not in self._clients:
            if provider == ModelProvider.OLLAMA:
                self._clients[provider] = OpenAI(
                    base_url=self.ollama_base_url,
                    api_key="ollama",  # Ollama는 API 키 불필요
                )
            elif provider == ModelProvider.OPENAI:
                if not self.openai_api_key:
                    raise ValueError(
                        "OpenAI API 키가 필요합니다. "
                        "OPENAI_API_KEY 환경변수를 설정하거나 openai_api_key 파라미터를 전달하세요."
                    )
                self._clients[provider] = OpenAI(api_key=self.openai_api_key)

        return self._clients[provider]

    def get_model_config(self, model_name: str) -> ModelConfig:
        """모델 설정을 반환합니다."""
        if model_name in AVAILABLE_MODELS:
            return AVAILABLE_MODELS[model_name]
        # 부분 매칭 (예: "exaone3.5:latest" → "exaone3.5")
        base_name = model_name.split(":")[0]
        if base_name in AVAILABLE_MODELS:
            return AVAILABLE_MODELS[base_name]
        # 알 수 없는 모델은 Ollama로 가정
        return ModelConfig(
            name=model_name,
            provider=ModelProvider.OLLAMA,
            display_name=model_name,
        )

    def chat(
        self,
        model: str,
        message: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        json_mode: bool = False,
    ) -> str:
        """
        텍스트 기반 채팅 완성.

        Args:
            model: 모델명 (예: "exaone3.5", "qwen3.5:9b", "gpt-4o")
            message: 사용자 메시지
            system_prompt: 시스템 프롬프트
            temperature: 생성 온도
            max_tokens: 최대 토큰 수
            json_mode: JSON 응답 모드

        Returns:
            모델 응답 텍스트
        """
        config = self.get_model_config(model)
        client = self._get_client(config.provider)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})

        kwargs = {
            "model": config.name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    def chat_with_image(
        self,
        model: str,
        message: str,
        image_path: str,
        temperature: float = 0.1,
        max_tokens: int = 2000,
    ) -> str:
        """
        이미지 포함 채팅 (비전 모델 전용).

        Args:
            model: 비전 지원 모델명 (예: "gemma4", "gpt-4o")
            message: 이미지에 대한 질문/지시
            image_path: 이미지 파일 경로
            temperature: 생성 온도
            max_tokens: 최대 토큰 수

        Returns:
            모델 응답 텍스트
        """
        config = self.get_model_config(model)

        if not config.supports_vision:
            raise ValueError(
                f"모델 '{model}'은 비전을 지원하지 않습니다. "
                f"비전 지원 모델: {[k for k, v in AVAILABLE_MODELS.items() if v.supports_vision]}"
            )

        client = self._get_client(config.provider)

        # 이미지 base64 인코딩
        with open(image_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode("utf-8")

        response = client.chat.completions.create(
            model=config.name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": message},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": "high",
                            },
                        },
                    ],
                }
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content

    def chat_json(
        self,
        model: str,
        message: str,
        system_prompt: str | None = None,
        temperature: float = 0.3,
    ) -> dict:
        """
        JSON 응답을 파싱하여 딕셔너리로 반환합니다.

        Returns:
            파싱된 JSON 딕셔너리
        """
        response = self.chat(
            model=model,
            message=message,
            system_prompt=system_prompt,
            temperature=temperature,
            json_mode=True,
        )

        # JSON 파싱 (코드블록 제거)
        text = response.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            text = text.rsplit("```", 1)[0]

        return json.loads(text)

    def get_embedding(self, model: str, text: str) -> list[float]:
        """
        텍스트 임베딩 벡터를 생성합니다.

        Args:
            model: 임베딩 모델명 (예: "bge-m3")
            text: 임베딩할 텍스트

        Returns:
            임베딩 벡터 (float 리스트)
        """
        config = self.get_model_config(model)
        client = self._get_client(config.provider)

        response = client.embeddings.create(
            model=config.name,
            input=text,
        )

        return response.data[0].embedding

    def list_local_models(self) -> list[str]:
        """Ollama에서 사용 가능한 로컬 모델 목록을 반환합니다."""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")[1:]  # 헤더 제외
                return [line.split()[0] for line in lines if line.strip()]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return list(AVAILABLE_MODELS.keys())

    def is_model_available(self, model: str) -> bool:
        """모델이 사용 가능한지 확인합니다."""
        config = self.get_model_config(model)
        if config.provider == ModelProvider.OPENAI:
            return bool(self.openai_api_key)
        return True  # Ollama 모델은 pull 필요할 수 있음

    def get_recommended_model(self, task: str) -> str:
        """작업에 추천되는 모델을 반환합니다."""
        return DEFAULT_MODEL_ASSIGNMENTS.get(task, "exaone3.5")


# ═══════════════════════════════════════
# 비교 실험 유틸리티
# ═══════════════════════════════════════

@dataclass
class ComparisonResult:
    """모델 비교 결과"""
    model: str
    display_name: str
    provider: str
    response: str
    temperature: float
    latency_ms: float
    token_count: int | None = None


def compare_models(
    prompt: str,
    models: list[str],
    system_prompt: str | None = None,
    temperatures: list[float] | None = None,
    client: LLMClient | None = None,
) -> list[ComparisonResult]:
    """
    동일한 프롬프트로 여러 모델의 응답을 비교합니다.

    Args:
        prompt: 테스트 프롬프트
        models: 비교할 모델 목록
        system_prompt: 시스템 프롬프트
        temperatures: 테스트할 temperature 값들 (None이면 [0.7])
        client: LLMClient 인스턴스

    Returns:
        ComparisonResult 리스트

    Examples:
        >>> results = compare_models(
        ...     "25세 남성 체지방 감소 식단 추천",
        ...     ["exaone3.5", "qwen3.5:9b", "gemma4"],
        ... )
    """
    import time

    if client is None:
        client = LLMClient()
    if temperatures is None:
        temperatures = [0.7]

    results = []

    for model in models:
        config = client.get_model_config(model)
        for temp in temperatures:
            try:
                start = time.time()
                response = client.chat(
                    model=model,
                    message=prompt,
                    system_prompt=system_prompt,
                    temperature=temp,
                )
                latency = round((time.time() - start) * 1000, 1)

                results.append(ComparisonResult(
                    model=model,
                    display_name=config.display_name,
                    provider=config.provider.value,
                    response=response,
                    temperature=temp,
                    latency_ms=latency,
                ))

            except Exception as e:
                results.append(ComparisonResult(
                    model=model,
                    display_name=config.display_name,
                    provider=config.provider.value,
                    response=f"[ERROR] {str(e)}",
                    temperature=temp,
                    latency_ms=0,
                ))

    return results
