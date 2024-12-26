"""FastAPI server for Chitti"""

from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, field_validator
from typing import Optional, Dict, Any, List, AsyncGenerator, Union
import re
from .services import ChittiService
from .hookspecs import PromptRequest, PromptResponse

app = FastAPI(title="Chitti API")
service = ChittiService()

class PromptRequestModel(BaseModel):
    prompt: str
    model: Optional[str] = None
    provider: Optional[str] = None

    @field_validator('prompt')
    def validate_prompt(cls, v):
        if not v.strip():
            raise ValueError("Empty prompt")
        return v

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Convert validation errors to 400 Bad Request"""
    errors = exc.errors()
    
    # Check if it's an empty prompt validation error
    if any("prompt" in error["loc"] and error["type"] == "value_error" for error in errors):
        return JSONResponse(
            status_code=400,
            content={"detail": str(errors[0]["msg"])}
        )
    
    # All other validation errors (including missing fields) return 422
    return JSONResponse(
        status_code=422,
        content={"detail": str(errors)}
    )

def validate_name(name: str, type_: str) -> None:
    """Validate provider/agent name format"""
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        raise ValueError(f"Invalid {type_} name")

class DefaultProviderRequest(BaseModel):
    provider: str

class DefaultModelRequest(BaseModel):
    provider: str
    model: str

@app.get("/")
async def root():
    """Get API information"""
    return {
        "title": "Chitti API",
        "version": "0.1.0",
        "description": "AI agent ecosystem"
    }

@app.post("/prompt/", response_model=None)
async def prompt(request: PromptRequestModel, stream: bool = Query(False, description="Whether to stream the response")):
    """Generate response from model with optional streaming"""
    try:
        if request.provider:
            validate_name(request.provider, "provider")

        prompt_request = PromptRequest(
            prompt=request.prompt,
            model=request.model,
            provider=request.provider
        )

        if stream:
            response = await service.process_prompt(prompt_request, stream=True)
            return StreamingResponse(response, media_type="text/event-stream")
        else:
            response = await service.process_prompt(prompt_request, stream=False)
            return response

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        error_code = "PROVIDER_ERROR"
        if "ThrottlingException" in str(e):
            error_code = "THROTTLING_ERROR"
        elif "ExpiredTokenException" in str(e):
            error_code = "AUTH_ERROR"
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.get("/providers/")
async def list_providers() -> List[str]:
    """List available providers"""
    try:
        return service.list_providers()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/providers/{provider}")
async def get_provider_info(provider: str) -> Dict[str, Any]:
    """Get provider information"""
    try:
        validate_name(provider, "provider")
        return service.get_provider_info(provider)
    except ValueError as e:
        if "Invalid provider name" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=400, detail="Provider not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents/")
async def list_agents() -> List[str]:
    """List available agents"""
    try:
        return service.list_agents()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents/{agent}")
async def get_agent_info(agent: str) -> Dict[str, Any]:
    """Get agent information"""
    try:
        validate_name(agent, "agent")
        return service.get_agent_info(agent)
    except ValueError as e:
        if "Invalid agent name" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=400, detail="Agent not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/settings/default")
async def get_default_settings() -> Dict[str, Any]:
    """Get default settings"""
    try:
        return service.get_default_settings()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/settings/default/provider")
async def set_default_provider(request: DefaultProviderRequest):
    """Set default provider"""
    try:
        service.set_default_provider(request.provider)
        return {"message": "Default provider set successfully"}
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Provider not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/settings/default/model")
async def set_default_model(request: DefaultModelRequest):
    """Set default model for provider"""
    try:
        validate_name(request.provider, "provider")
        try:
            service.set_default_model(request.provider, request.model)
            return {"message": "Default model set successfully"}
        except ValueError as e:
            if "Provider" not in str(e):
                raise HTTPException(status_code=400, detail="Model not found")
            raise
    except ValueError as e:
        if "Invalid provider name" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=400, detail="Provider not found")
    except Exception as e:
        if "not found" in str(e):
            raise HTTPException(status_code=400, detail="Model not found")
        raise HTTPException(status_code=500, detail=str(e))

@app.exception_handler(ValueError)
async def validation_exception_handler(request: Request, exc: ValueError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "error_code": "VALIDATION_ERROR"}
    )

@app.exception_handler(RuntimeError)
async def runtime_exception_handler(request: Request, exc: RuntimeError):
    """Handle runtime errors"""
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "error_code": "PROVIDER_ERROR"}
    )

@app.post("/default/provider/")
async def set_default_provider(request: DefaultProviderRequest):
    """Set the default provider"""
    try:
        service.set_default_provider(request.provider)
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/default/model/")
async def set_default_model(request: DefaultModelRequest):
    """Set the default model for a provider"""
    try:
        service.set_default_model(request.provider, request.model)
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 