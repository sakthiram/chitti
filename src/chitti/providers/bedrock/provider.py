import boto3
import json
from typing import Dict, Any, List, Generator, Union, AsyncGenerator, Optional
import pluggy
from ...hookspecs import ModelProviderSpec

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

class BedrockProvider:
    """AWS Bedrock model provider"""

    def __init__(self):
        session = boto3.Session(profile_name='sakthisi-develop')
        self.bedrock = session.client(
            service_name='bedrock-runtime',
            region_name='us-east-1'
        )
        self.current_model_index = 0

    def _get_model_with_fallback(self, prompt: str, **kwargs) -> str:
        """Try each model in sequence until one works"""
        while self.current_model_index < len(_AVAILABLE_MODELS):
            try:
                model_id = _AVAILABLE_MODELS[self.current_model_index]
                body = self._get_request_body(prompt, **kwargs)
                response = self.bedrock.invoke_model_with_response_stream(
                    modelId=model_id,
                    body=json.dumps(body)
                )
                print(f"Using model: {model_id}")
                return response
            except Exception as e:
                if 'ThrottlingException' in str(e):
                    print(f'Model {_AVAILABLE_MODELS[self.current_model_index]} is throttled. Trying next model...')
                    self.current_model_index += 1
                else:
                    raise e
        raise ValueError('All models are throttled. Please try again later.')

    # Currently only supports Anthropic models
    # TODO: Add support for other models (can use litellm for other models)
    # PS: Can even use litellm for all providers, but want to stick to the 
    # principles of less abstraction and more control
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
        return {
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

    async def _get_response_stream(self, prompt: str, **kwargs) -> Any:
        """Get response stream from Bedrock with fallback handling"""
        model_info = self.get_model_info()
        model_id = kwargs.get('model', model_info["default_model"])
        
        if model_id not in model_info["models"]:
            raise ValueError(f"Unsupported model: {model_id}")

        try:
            # Try with specified model first
            try:
                body = self._get_request_body(prompt, **kwargs)
                response = self.bedrock.invoke_model_with_response_stream(
                    modelId=model_id,
                    body=json.dumps(body)
                )
                print(f"Using model: {model_id}")
            except Exception as e:
                if "ThrottlingException" in str(e):
                    print(f'Model {model_id} is throttled. Trying fallback models...')
                    self.current_model_index = 0  # Reset index for fallback
                    response = self._get_model_with_fallback(prompt, **kwargs)
                else:
                    raise e
        
            if not response or 'body' not in response:
                raise ValueError("Invalid response from Bedrock")
            
            return response
        except ValueError as e:
            if 'ExpiredTokenException' in str(e):
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
            raise

    def _process_chunk(self, chunk_bytes: bytes) -> Optional[str]:
        """Process a chunk and return text if valid"""
        try:
            chunk = json.loads(chunk_bytes.decode())
            if chunk.get('type') == 'content_block_delta':
                if chunk['delta']['type'] == 'text_delta':
                    return chunk['delta']['text']
        except (json.JSONDecodeError, KeyError):
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
