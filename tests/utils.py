"""Test utilities"""

from chitti.hookspecs import ModelProviderSpec

class MockProvider(ModelProviderSpec):
    """Mock provider for testing"""
    def __init__(self, name="mock"):
        self.name = name
        self.models = ["model1", "model2"]
        self.default_model = "model1"
        self.pricing = {
            "model1": {
                "input_cost_per_1k": 0.01,
                "output_cost_per_1k": 0.02
            },
            "model2": {
                "input_cost_per_1k": 0.02,
                "output_cost_per_1k": 0.03
            }
        }
        
    def get_provider_name(self) -> str:
        return self.name
        
    def get_model_info(self) -> dict:
        return {
            "name": self.name,
            "description": "Mock provider for testing",
            "models": self.models,
            "default_model": self.default_model,
            "pricing": self.pricing,
            "capabilities": {
                "streaming": True
            }
        }
        
    async def generate_stream(self, prompt: str, model: str = None, **kwargs):
        """Generate streaming response"""
        if model and model not in self.models:
            raise ValueError(f"Model {model} not found")
        yield f"Mock response from {self.name} using {model or self.default_model}: {prompt}"
        
    async def generate_response(self, prompt: str, model: str = None, **kwargs):
        """Generate non-streaming response"""
        if model and model not in self.models:
            raise ValueError(f"Model {model} not found")
        return f"Mock response from {self.name} using {model or self.default_model}: {prompt}"
        
    def generate(self, prompt: str, model: str = None, **kwargs):
        """Generate response based on streaming flag"""
        if kwargs.get('stream', False):
            return self.generate_stream(prompt, model=model, **kwargs)
        else:
            return self.generate_response(prompt, model=model, **kwargs) 