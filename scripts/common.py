# ==============================================================================
# 공통 유틸리티 모듈
# ==============================================================================
# 이 파일의 역할: 모든 스크립트에서 공통으로 사용하는 함수들 제공
# - 로깅 설정
# - JSON 파일 읽기/쓰기
# - 환경변수 로드
# - 다중 AI API 클라이언트 지원 (Claude, OpenAI, Gemini 등)
# ==============================================================================

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List

# ==============================================================================
# 경로 상수 정의
# ==============================================================================
# 프로젝트 루트 디렉토리 (scripts의 부모)
ROOT_DIR = Path(__file__).parent.parent
CONFIG_DIR = ROOT_DIR / "config"
LOGS_DIR = ROOT_DIR / "logs"
OUTPUT_DIR = ROOT_DIR / "output"

# ==============================================================================
# 환경변수 로드
# ==============================================================================
def load_environment():
    """
    .env 파일에서 환경변수를 로드합니다.
    """
    env_path = ROOT_DIR / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        return True
    else:
        print("[WARNING] .env 파일이 없습니다. .env.example을 참고해주세요.")
        return False

# ==============================================================================
# 로깅 설정
# ==============================================================================
def setup_logging(name: str, log_file: str = None) -> logging.Logger:
    """
    로깅을 설정합니다.
    
    Args:
        name: 로거 이름 (보통 스크립트 이름)
        log_file: 로그 파일 경로 (선택사항)
    
    Returns:
        설정된 로거 인스턴스
    """
    # 로그 디렉토리 생성
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # 이미 핸들러가 있으면 추가하지 않음
    if logger.handlers:
        return logger
    
    # 포맷터 생성
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 콘솔 핸들러 추가
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러 추가 (지정된 경우)
    if log_file:
        file_handler = logging.FileHandler(LOGS_DIR / log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# ==============================================================================
# JSON 파일 읽기/쓰기
# ==============================================================================
def load_json(filename: str) -> dict:
    """
    JSON 파일을 읽어 파이썬 딕셔너리로 반환합니다.
    
    Args:
        filename: config/ 폴더 내의 파일명
    
    Returns:
        파싱된 딕셔너리
    """
    file_path = CONFIG_DIR / filename
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {file_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 파싱 오류 ({file_path}): {e}")

def save_json(data: dict, filename: str) -> bool:
    """
    딕셔너리를 JSON 파일로 저장합니다.
    
    Args:
        data: 저장할 딕셔너리
        filename: output/ 폴더 내의 파일명
    
    Returns:
        저장 성공 여부
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    file_path = OUTPUT_DIR / filename
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[ERROR] JSON 저장 실패: {e}")
        return False

def load_output_json(filename: str) -> dict:
    """
    output/ 폴더에서 JSON 파일을 읽어 파이썬 딕셔너리로 반환합니다.
    
    Args:
        filename: output/ 폴더 내의 파일명
    
    Returns:
        파싱된 딕셔너리
    """
    file_path = OUTPUT_DIR / filename
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def list_output_files() -> list:
    """
    output/ 폴더의 모든 JSON 파일 목록을 반환합니다.
    
    Returns:
        파일명 리스트
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return [f.name for f in OUTPUT_DIR.glob("*.json")]

# ==============================================================================
# 다중 AI API 클라이언트 지원
# ==============================================================================
class MultiAIClient:
    """
    여러 AI 프로바이더를 지원하는 범용 AI 클라이언트
    지원: Claude (Anthropic), OpenAI, Google Gemini, Groq, Ollama 등
    """
    
    def __init__(self):
        """AI 클라이언트 초기화"""
        self.providers = {}
        self.current_provider = os.getenv("AI_PROVIDER", "claude").lower()
        self._initialize_providers()
    
    def _initialize_providers(self):
        """지원되는 모든 AI 프로바이더 초기화"""
        # Claude (Anthropic)
        if os.getenv("CLAUDE_API_KEY"):
            try:
                from anthropic import Anthropic
                self.providers["claude"] = {
                    "client": Anthropic(api_key=os.getenv("CLAUDE_API_KEY")),
                    "model": os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514"),
                    "supports_system_prompt": True
                }
            except ImportError:
                print("[WARNING] Anthropic 라이브러리가 설치되지 않았습니다.")
        
        # OpenAI
        if os.getenv("OPENAI_API_KEY"):
            try:
                from openai import OpenAI
                self.providers["openai"] = {
                    "client": OpenAI(api_key=os.getenv("OPENAI_API_KEY")),
                    "model": os.getenv("OPENAI_MODEL", "gpt-4o"),
                    "supports_system_prompt": True
                }
            except ImportError:
                print("[WARNING] OpenAI 라이브러리가 설치되지 않았습니다.")
        
        # Google Gemini
        if os.getenv("GEMINI_API_KEY"):
            try:
                import google.generativeai as genai
                genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
                self.providers["gemini"] = {
                    "client": genai,
                    "model": os.getenv("GEMINI_MODEL", "gemini-pro"),
                    "supports_system_prompt": True
                }
            except ImportError:
                print("[WARNING] Google Generative AI 라이브러리가 설치되지 않았습니다.")
        
        # Groq (무료/low-cost AI)
        if os.getenv("GROQ_API_KEY"):
            try:
                from groq import Groq
                self.providers["groq"] = {
                    "client": Groq(api_key=os.getenv("GROQ_API_KEY")),
                    "model": os.getenv("GROQ_MODEL", "mixtral-8x7b-32768"),
                    "supports_system_prompt": True
                }
            except ImportError:
                print("[WARNING] Groq 라이브러리가 설치되지 않았습니다.")
        
        # Ollama (로컬 AI)
        if os.getenv("OLLAMA_BASE_URL"):
            self.providers["ollama"] = {
                "client": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                "model": os.getenv("OLLAMA_MODEL", "llama2"),
                "supports_system_prompt": True
            }
        
        # LiteLLM 프록시 서버 (NVIDIA API 등)
        if os.getenv("LITELLM_BASE_URL"):
            try:
                from litellm import completion
                self.providers["litellm"] = {
                    "client": completion,
                    "base_url": os.getenv("LITELLM_BASE_URL"),
                    "model": os.getenv("LITELLM_MODEL", "glm-plan"),
                    "supports_system_prompt": True
                }
            except ImportError:
                print("[WARNING] LiteLLM 라이브러리가 설치되지 않았습니다.")
    
    def get_available_providers(self) -> List[str]:
        """
        사용 가능한 AI 프로바이더 목록 반환
        
        Returns:
            프로바이더 이름 리스트
        """
        return list(self.providers.keys())
    
    def set_provider(self, provider: str):
        """
        사용할 AI 프로바이더 설정
        
        Args:
            provider: 프로바이더 이름 (claude, openai, gemini, groq, ollama)
        """
        if provider in self.providers:
            self.current_provider = provider
        else:
            raise ValueError(f"지원되지 않는 프로바이더: {provider}")
    
    def generate(self, prompt: str, system_prompt: str = None, **kwargs) -> str:
        """
        AI를 사용하여 텍스트 생성
        
        Args:
            prompt: 사용자 프롬프트
            system_prompt: 시스템 프롬프트 (선택사항)
            **kwargs: 추가 매개변수 (temperature, max_tokens 등)
        
        Returns:
            생성된 텍스트
        """
        if self.current_provider not in self.providers:
            raise ValueError(f"프로바이더가 설정되지 않았습니다: {self.current_provider}")
        
        provider_info = self.providers[self.current_provider]
        
        if self.current_provider == "claude":
            return self._generate_claude(provider_info, prompt, system_prompt, **kwargs)
        elif self.current_provider == "openai":
            return self._generate_openai(provider_info, prompt, system_prompt, **kwargs)
        elif self.current_provider == "gemini":
            return self._generate_gemini(provider_info, prompt, system_prompt, **kwargs)
        elif self.current_provider == "groq":
            return self._generate_groq(provider_info, prompt, system_prompt, **kwargs)
        elif self.current_provider == "ollama":
            return self._generate_ollama(provider_info, prompt, system_prompt, **kwargs)
        elif self.current_provider == "litellm":
            return self._generate_litellm(provider_info, prompt, system_prompt, **kwargs)
        
        raise ValueError(f"지원되지 않는 프로바이더: {self.current_provider}")
    
    def _generate_claude(self, provider_info: dict, prompt: str, system_prompt: str, **kwargs) -> str:
        """Claude API 호출"""
        messages = []
        if system_prompt:
            messages.append({"role": "user", "content": f"System: {system_prompt}\n\n{prompt}"})
        else:
            messages.append({"role": "user", "content": prompt})
        
        response = provider_info["client"].messages.create(
            model=provider_info["model"],
            max_tokens=kwargs.get("max_tokens", 8192),
            temperature=kwargs.get("temperature", 0.7),
            messages=messages
        )
        return response.content[0].text
    
    def _generate_openai(self, provider_info: dict, prompt: str, system_prompt: str, **kwargs) -> str:
        """OpenAI API 호출"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = provider_info["client"].chat.completions.create(
            model=provider_info["model"],
            max_tokens=kwargs.get("max_tokens", 4096),
            temperature=kwargs.get("temperature", 0.7),
            messages=messages
        )
        return response.choices[0].message.content
    
    def _generate_gemini(self, provider_info: dict, prompt: str, system_prompt: str, **kwargs) -> str:
        """Google Gemini API 호출"""
        model = provider_info["client"].get_model(provider_info["model"])
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        response = model.generate_content(full_prompt)
        return response.text
    
    def _generate_groq(self, provider_info: dict, prompt: str, system_prompt: str, **kwargs) -> str:
        """Groq API 호출"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = provider_info["client"].chat.completions.create(
            model=provider_info["model"],
            max_tokens=kwargs.get("max_tokens", 4096),
            temperature=kwargs.get("temperature", 0.7),
            messages=messages
        )
        return response.choices[0].message.content
    
    def _generate_ollama(self, provider_info: dict, prompt: str, system_prompt: str, **kwargs) -> str:
        """Ollama (로컬 AI) API 호출"""
        import requests
        
        payload = {
            "model": provider_info["model"],
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "num_predict": kwargs.get("max_tokens", 4096)
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        response = requests.post(
            f"{provider_info['client']}/api/generate",
            json=payload,
            timeout=120
        )
        
        if response.status_code == 200:
            return response.json().get("response", "")
        else:
            raise Exception(f"Ollama API 오류: {response.status_code}")
    
    def _generate_litellm(self, provider_info: dict, prompt: str, system_prompt: str, **kwargs) -> str:
        """LiteLLM 프록시 서버 API 호출"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = provider_info["client"](
            model=provider_info["model"],
            messages=messages,
            api_base=provider_info["base_url"],
            max_tokens=kwargs.get("max_tokens", 8192),
            temperature=kwargs.get("temperature", 0.7)
        )
        
        return response.choices[0].message.content

# ==============================================================================
# AI 클라이언트 인스턴스 (전역)
# ==============================================================================
_ai_client: Optional[MultiAIClient] = None

def get_ai_client() -> MultiAIClient:
    """
    AI 클라이언트 인스턴스를 반환합니다. (싱글톤)
    
    Returns:
        MultiAIClient 인스턴스
    """
    global _ai_client
    if _ai_client is None:
        _ai_client = MultiAIClient()
    return _ai_client

# ==============================================================================
# WordPress API 설정
# ==============================================================================
def get_wordpress_config() -> dict:
    """
    WordPress API 설정값을 반환합니다.
    
    Returns:
        WordPress 설정 딕셔너리
    """
    return {
        "site_url": os.getenv("WP_SITE_URL"),
        "username": os.getenv("WP_API_USERNAME"),
        "password": os.getenv("WP_API_PASSWORD")
    }

# ==============================================================================
# 유틸리티 함수
# ==============================================================================
def generate_timestamp() -> str:
    """
    현재 타임스탬프를 반환합니다.
    
    Returns:
        YYYYMMDD_HHMMSS 형식의 문자열
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def sanitize_filename(filename: str) -> str:
    """
    파일명에 사용할 수 없는 문자를 제거합니다.
    
    Args:
        filename: 원본 파일명
    
    Returns:
        정제된 파일명
    """
    # 사용할 수 없는 문자 제거
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

# ==============================================================================
# 초기화
# ==============================================================================
# 스크립트 실행 시 자동으로 환경변수 로드
load_environment()