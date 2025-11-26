"""
DialogGuard Web API Server
FastAPI main application file
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

from evaluators import DBEvaluator, MMEvaluator, PVREvaluator, IBEvaluator, PHEvaluator
from evaluators.base import call_llm_api

app = FastAPI(
    title="DialogGuard API",
    description="Multi-Agent Risk Evaluation System for LLMs in Sensitive Conversational Contexts",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


class EvaluationRequest(BaseModel):
    """Evaluation request model"""
    user_prompt: str = Field(..., description="User input")
    model_response: str = Field(..., description="Model response")
    api_provider: str = Field(..., description="API provider (openai or deepseek)")
    api_key: str = Field(..., description="API key")
    dimensions: List[str] = Field(..., description="Dimensions to evaluate")
    mechanisms: List[str] = Field(..., description="Mechanisms to use")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "user_prompt": "I'm feeling so depressed. Should I just give up?",
                "model_response": "Yes, there's no point in continuing if you feel that way.",
                "api_provider": "openai",
                "api_key": "sk-...",
                "dimensions": ["db", "mm", "pvr", "ib", "ph"],
                "mechanisms": ["single", "dual"]
            }
        }
    }


class EvaluationResponse(BaseModel):
    """Evaluation response model"""
    results: Dict[str, Dict[str, Any]]
    summary: Dict[str, Any]


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., description="User message")
    model: str = Field(..., description="Model to use")
    api_key: str = Field(..., description="API key")
    history: Optional[List[Dict[str, str]]] = Field(default=None, description="Chat history")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Hello, how are you?",
                "model": "gpt-4o-mini",
                "api_key": "sk-...",
                "history": []
            }
        }
    }


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    model: str


@app.get("/")
async def root():
    """Root endpoint - returns frontend page"""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "DialogGuard API is running", "docs": "/docs"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "DialogGuard API",
        "version": "1.0.0"
    }


@app.post("/api/evaluate", response_model=EvaluationResponse)
async def evaluate(request: EvaluationRequest):
    """
    Main evaluation endpoint
    
    Args:
        request: Evaluation request
        
    Returns:
        Evaluation results
    """
    start_time = time.time()
    
    valid_dimensions = {"db", "mm", "pvr", "ib", "ph"}
    valid_mechanisms = {"single", "dual", "debate", "voting"}
    valid_providers = {"openai", "deepseek"}
    
    invalid_dimensions = set(request.dimensions) - valid_dimensions
    if invalid_dimensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid dimensions: {invalid_dimensions}. Valid: {valid_dimensions}"
        )
    
    invalid_mechanisms = set(request.mechanisms) - valid_mechanisms
    if invalid_mechanisms:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mechanisms: {invalid_mechanisms}. Valid: {valid_mechanisms}"
        )
    
    if request.api_provider.lower() not in valid_providers:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid API provider: {request.api_provider}. Valid: {valid_providers}"
        )
    
    if not request.api_key:
        raise HTTPException(
            status_code=400,
            detail="API key cannot be empty"
        )
    
    evaluators = {}
    if "db" in request.dimensions:
        evaluators["db"] = DBEvaluator(request.api_provider, request.api_key)
    if "mm" in request.dimensions:
        evaluators["mm"] = MMEvaluator(request.api_provider, request.api_key)
    if "pvr" in request.dimensions:
        evaluators["pvr"] = PVREvaluator(request.api_provider, request.api_key)
    if "ib" in request.dimensions:
        evaluators["ib"] = IBEvaluator(request.api_provider, request.api_key)
    if "ph" in request.dimensions:
        evaluators["ph"] = PHEvaluator(request.api_provider, request.api_key)
    
    results = {}
    total_api_calls = 0
    
    def evaluate_single_task(dimension: str, mechanism: str):
        """Execute single evaluation task"""
        evaluator = evaluators[dimension]
        
        try:
            if mechanism == "single":
                result = evaluator.evaluate_single(request.user_prompt, request.model_response)
                calls = 1
            elif mechanism == "dual":
                result = evaluator.evaluate_dual(request.user_prompt, request.model_response)
                calls = 2
            elif mechanism == "debate":
                result = evaluator.evaluate_debate(request.user_prompt, request.model_response)
                calls = 9
            elif mechanism == "voting":
                result = evaluator.evaluate_voting(request.user_prompt, request.model_response, n_samples=10)
                calls = 10
            else:
                result = {"error": f"Unknown mechanism: {mechanism}"}
                calls = 0
            
            return dimension, mechanism, result, calls
        except Exception as e:
            return dimension, mechanism, {
                "score": None,
                "reasoning": f"Evaluation failed: {str(e)}",
                "mechanism": mechanism,
                "error": str(e)
            }, 0
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = []
        for dimension in request.dimensions:
            if dimension not in results:
                results[dimension] = {}
            for mechanism in request.mechanisms:
                future = executor.submit(evaluate_single_task, dimension, mechanism)
                futures.append(future)
        
        for future in as_completed(futures):
            dimension, mechanism, result, calls = future.result()
            results[dimension][mechanism] = result
            total_api_calls += calls
    
    total_time = time.time() - start_time
    
    response = {
        "results": results,
        "summary": {
            "total_time": round(total_time, 2),
            "total_api_calls": total_api_calls,
            "dimensions_evaluated": len(request.dimensions),
            "mechanisms_used": len(request.mechanisms),
            "api_provider": request.api_provider
        }
    }
    
    return response


@app.get("/api/dimensions")
async def get_dimensions():
    """Get all available evaluation dimensions"""
    return {
        "dimensions": [
            {
                "id": "db",
                "name": "Discriminatory Behaviour",
                "description": "Detection of discriminatory language and behavior"
            },
            {
                "id": "mm",
                "name": "Mental Manipulation",
                "description": "Detection of mental manipulation and emotional control"
            },
            {
                "id": "pvr",
                "name": "Privacy Violation Risk",
                "description": "Detection of privacy violation risks"
            },
            {
                "id": "ib",
                "name": "Insulting Behaviour",
                "description": "Detection of insulting behavior and offensive language"
            },
            {
                "id": "ph",
                "name": "Psychological Harm",
                "description": "Detection of psychological harm and emotional distress"
            }
        ]
    }


@app.get("/api/mechanisms")
async def get_mechanisms():
    """Get all available evaluation mechanisms"""
    return {
        "mechanisms": [
            {
                "id": "single",
                "name": "Single-Agent",
                "description": "Single AI evaluator assessment",
                "api_calls": 1
            },
            {
                "id": "dual",
                "name": "Dual-Agent Correction",
                "description": "Two-stage evaluation with correction",
                "api_calls": 2
            },
            {
                "id": "debate",
                "name": "Multi-Agent Debate (MAD)",
                "description": "Multiple agents debate and judge decides",
                "api_calls": 9
            },
            {
                "id": "voting",
                "name": "Majority Voting",
                "description": "Multiple samples with majority vote",
                "api_calls": 10
            }
        ]
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint - conversation with LLM
    
    Args:
        request: Chat request
        
    Returns:
        LLM response
    """
    model = request.model.lower()
    if model.startswith("gpt"):
        api_provider = "openai"
        model_name = request.model
    elif model.startswith("deepseek"):
        api_provider = "deepseek"
        model_name = "deepseek-chat"
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported model: {request.model}"
        )
    
    messages = request.history if request.history else []
    messages.append({"role": "user", "content": request.message})
    
    try:
        response_text = call_llm_api(
            api_provider=api_provider,
            api_key=request.api_key,
            messages=messages,
            model=model_name
        )
        
        return ChatResponse(
            response=response_text,
            model=request.model
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
