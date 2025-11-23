"""
DialogGuard Base Evaluator - Shared API calls and parsing functions
"""
import json
import re
import time
import requests
from typing import Dict, Any, Optional


def call_openai_api(
    system_prompt: str,
    user_prompt: str,
    api_key: str,
    model: str = "gpt-4o-mini",
    base_url: str = "https://api.openai.com/v1",
    temperature: float = 0.0,
    max_tokens: int = 256,
    timeout: int = 60,
    max_retries: int = 3
) -> str:
    """
    Call OpenAI API
    
    Args:
        system_prompt: System prompt
        user_prompt: User prompt
        api_key: OpenAI API key
        model: Model name
        base_url: API base URL
        temperature: Temperature parameter
        max_tokens: Maximum tokens
        timeout: Timeout in seconds
        max_retries: Maximum retry attempts
        
    Returns:
        API response text
        
    Raises:
        RuntimeError: API call failed
    """
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    last_err = None
    backoff = 2.0
    
    for attempt in range(max_retries):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
            
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()
            elif resp.status_code == 401:
                last_err = RuntimeError(f"API authentication failed (401) - Please check your API key")
                break
            else:
                last_err = RuntimeError(f"HTTP {resp.status_code}: {resp.text[:300]}")
                
        except Exception as e:
            last_err = e
            
        if attempt < max_retries - 1:
            time.sleep(backoff)
            backoff *= 2
    
    raise last_err if last_err else RuntimeError("Unknown API error")


def call_deepseek_api(
    system_prompt: str,
    user_prompt: str,
    api_key: str,
    model: str = "deepseek-chat",
    base_url: str = "https://api.deepseek.com/v1",
    temperature: float = 0.0,
    max_tokens: int = 256,
    timeout: int = 60,
    max_retries: int = 3
) -> str:
    """
    Call DeepSeek API
    
    Args:
        system_prompt: System prompt
        user_prompt: User prompt
        api_key: DeepSeek API key
        model: Model name
        base_url: API base URL
        temperature: Temperature parameter
        max_tokens: Maximum tokens
        timeout: Timeout in seconds
        max_retries: Maximum retry attempts
        
    Returns:
        API response text
        
    Raises:
        RuntimeError: API call failed
    """
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    last_err = None
    backoff = 2.0
    
    for attempt in range(max_retries):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
            
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()
            elif resp.status_code == 401:
                last_err = RuntimeError(f"API authentication failed (401) - Please check your API key")
                break
            else:
                last_err = RuntimeError(f"HTTP {resp.status_code}: {resp.text[:300]}")
                
        except Exception as e:
            last_err = e
            
        if attempt < max_retries - 1:
            time.sleep(backoff)
            backoff *= 2
    
    raise last_err if last_err else RuntimeError("Unknown API error")


def parse_score(text: str) -> int:
    """
    Parse score (0, 1, or 2) from text
    
    Args:
        text: Text to parse
        
    Returns:
        Parsed score (0-2)
    """
    text = text.strip()
    
    match = re.search(r'\b([012])\b', text)
    if match:
        return int(match.group(1))
    
    text_lower = text.lower()
    
    if "2" in text or "clear" in text_lower or "explicit" in text_lower:
        return 2
    if "1" in text or "possible" in text_lower or "potential" in text_lower:
        return 1
    
    return 0


def parse_json_response(content: str) -> Dict[str, Any]:
    """
    Parse JSON response (for Dual-Agent mechanism)
    
    Args:
        content: API response content
        
    Returns:
        Parsed dictionary
        
    Raises:
        ValueError: Cannot parse JSON
    """
    content = content.strip()
    if content.startswith('```'):
        content = re.sub(r'^```[a-zA-Z]*\n?', '', content)
        content = re.sub(r'```$', '', content.strip())
    
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        
        raise ValueError(f"Cannot parse JSON response: {content[:100]}")


def call_api(
    system_prompt: str,
    user_prompt: str,
    api_provider: str,
    api_key: str,
    model: Optional[str] = None,
    temperature: float = 0.0,
    max_tokens: int = 256
) -> str:
    """
    Unified API call interface
    
    Args:
        system_prompt: System prompt
        user_prompt: User prompt
        api_provider: API provider ('openai' or 'deepseek')
        api_key: API key
        model: Model name (optional)
        temperature: Temperature parameter
        max_tokens: Maximum tokens
        
    Returns:
        API response text
    """
    if api_provider.lower() == "openai":
        model = model or "gpt-4o-mini"
        return call_openai_api(
            system_prompt, user_prompt, api_key, model,
            temperature=temperature, max_tokens=max_tokens
        )
    elif api_provider.lower() == "deepseek":
        model = model or "deepseek-chat"
        return call_deepseek_api(
            system_prompt, user_prompt, api_key, model,
            temperature=temperature, max_tokens=max_tokens
        )
    else:
        raise ValueError(f"Unsupported API provider: {api_provider}")


def call_llm_api(
    api_provider: str,
    api_key: str,
    messages: list,
    model: str,
    temperature: float = 0.7,
    max_tokens: int = 1024,
    timeout: int = 60
) -> str:
    """
    Unified LLM API call interface (supports message list format)
    Used for chat functionality
    
    Args:
        api_provider: API provider ('openai' or 'deepseek')
        api_key: API key
        messages: Message list [{"role": "user", "content": "..."}, ...]
        model: Model name
        temperature: Temperature parameter
        max_tokens: Maximum tokens
        timeout: Timeout in seconds
        
    Returns:
        API response text
    """
    if api_provider.lower() == "openai":
        base_url = "https://api.openai.com/v1"
    elif api_provider.lower() == "deepseek":
        base_url = "https://api.deepseek.com/v1"
    else:
        raise ValueError(f"Unsupported API provider: {api_provider}")
    
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
        
        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        elif resp.status_code == 401:
            raise RuntimeError(f"API authentication failed (401) - Please check your API key")
        else:
            raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:300]}")
            
    except requests.exceptions.Timeout:
        raise RuntimeError(f"API call timeout (>{timeout}s)")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Network request failed: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"API call failed: {str(e)}")
