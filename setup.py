from setuptools import setup, find_packages

setup(
    name="chitti",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "fastapi",
        "uvicorn",
        "pluggy",
        "click",
        "boto3",
        "pydantic",
        "python-dotenv",
        "typing-extensions",
        "prompt_toolkit"
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
            "httpx>=0.24.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
            "ruff>=0.1.0"
        ]
    },
    entry_points={
        "console_scripts": [
            "chitti=chitti.cli:main",
        ],
        "chitti.providers": [
            "bedrock=chitti.providers.bedrock:BedrockProvider",
        ],
        "chitti.tools": [],
        "chitti.agents": []
    }
) 