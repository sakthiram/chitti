"""AWS Bedrock provider implementation"""

import boto3
import json
import logging
from typing import Dict, Any, List, Generator, Union, AsyncGenerator, Optional
import pluggy
from ...hookspecs import ModelProviderSpec

logger = logging.getLogger(__name__)

hookimpl = pluggy.HookimplMarker("chitti")

# Private constants
_AVAILABLE_MODELS = [
    "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    "us.anthropic.claude-3-5-haiku-20241022-v1:0",
    "anthropic.claude-3-5-sonnet-20240620-v1:0",
    "anthropic.claude-3-sonnet-20240229-v1:0",
    "anthropic.claude-3-haiku-20240307-v1:0",
    "anthropic.claude-3-opus-20240229-v1:0"
]

_MODEL_PRICING = {
    "us.anthropic.claude-3-5-sonnet-20241022-v2:0": {
        "input_cost_per_1k": 0.003,
        "output_cost_per_1k": 0.015
    },
    "us.anthropic.claude-3-5-haiku-20241022-v1:0": {
        "input_cost_per_1k": 0.001,
        "output_cost_per_1k": 0.005
    },
    "anthropic.claude-3-5-sonnet-20240620-v1:0": {
        "input_cost_per_1k": 0.003,
        "output_cost_per_1k": 0.015
    },
    "anthropic.claude-3-opus-20240229-v1:0": {
        "input_cost_per_1k": 0.015,
        "output_cost_per_1k": 0.075
    },
    "anthropic.claude-3-haiku-20240307-v1:0": {
        "input_cost_per_1k": 0.00025,
        "output_cost_per_1k": 0.00125
    },
    "anthropic.claude-3-sonnet-20240229-v1:0": {
        "input_cost_per_1k": 0.003,
        "output_cost_per_1k": 0.015
    }
}

class BedrockProvider(ModelProviderSpec):
    """AWS Bedrock model provider"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not BedrockProvider._initialized:
            session = boto3.Session(profile_name='sakthisi-develop')
            self.bedrock = session.client(
                service_name='bedrock-runtime',
                region_name='us-east-1'
            )
            # Cache model info
            self._model_info = {
                "name": "bedrock",
                "description": "AWS Bedrock model provider",
                "models": _AVAILABLE_MODELS,
                "default_model": _AVAILABLE_MODELS[0],
                "pricing": _MODEL_PRICING,
                "capabilities": {
                    "streaming": True,
                    "function_calling": False,
                    "vision": False
                }
            }
            BedrockProvider._initialized = True

    def _get_request_body(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Get request body for model invocation"""
        return {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": kwargs.get("max_tokens", 8192),
        }

    @hookimpl
    def get_provider_name(self) -> str:
        """Get the unique name of this provider"""
        return "bedrock"

    @hookimpl
    def get_model_info(self) -> Dict[str, Any]:
        """Get comprehensive model information"""
        return self._model_info

    async def _get_response_stream(self, prompt: str, **kwargs) -> Any:
        """Get response stream from Bedrock with fallback handling"""
        model_id = kwargs.get('model', self._model_info["default_model"])
        
        if model_id not in self._model_info["models"]:
            raise ValueError(f"Unsupported model: {model_id}")

        try:
            body = self._get_request_body(prompt, **kwargs)
            response = self.bedrock.invoke_model_with_response_stream(
                modelId=model_id,
                body=json.dumps(body)
            )
            print(f"Using model: {model_id}")
            
            if not response or 'body' not in response:
                raise ValueError("Invalid response from Bedrock")
            
            return response
        except Exception as e:
            # TODO Add throttling fallback support
            if "ExpiredTokenException" in str(e):
                error_message = """
                ### 🔑 AWS Session Token has expired

                Please refresh your AWS credentials using one of these methods:

                1. If using AWS CLI profile:
                ```bash
                aws sso login --profile your-profile-name
                ```

                2. If using environment variables, get new credentials and set:
                ```bash
                export AWS_ACCESS_KEY_ID=your_access_key
                export AWS_SECRET_ACCESS_KEY=your_secret_key
                export AWS_SESSION_TOKEN=your_session_token
                ```

                Then restart the application.
                """
                raise ValueError(error_message)
            else:
                raise

    def _process_chunk(self, chunk_bytes: bytes) -> Optional[str]:
        """Process a chunk and return text if valid"""
        try:
            chunk = json.loads(chunk_bytes.decode())
            if chunk.get('type') == 'content_block_delta':
                if chunk['delta']['type'] == 'text_delta':
                    return chunk['delta']['text']
        except json.JSONDecodeError:
            pass
        return None

    @hookimpl
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using Bedrock models without streaming"""
        response = await self._get_response_stream(prompt, **kwargs)
        
        # Process the response
        full_response = ""
        try:
            for event in response.get('body'):
                if text := self._process_chunk(event['chunk']['bytes']):
                    full_response += text
        except Exception as e:
            if not full_response:  # Only raise if we haven't got any response
                raise
        
        return full_response

    @hookimpl
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Generate text using Bedrock models with streaming"""
        response = await self._get_response_stream(prompt, **kwargs)
        
        # Stream the response
        try:
            for event in response.get('body'):
                if text := self._process_chunk(event['chunk']['bytes']):
                    yield text
        except Exception as e:
            raise
