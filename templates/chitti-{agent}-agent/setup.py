"""Setup script for the agent package"""

from setuptools import setup, find_namespace_packages

setup(
    name="chitti-{agent}-agent",
    version="0.1.0",
    packages=find_namespace_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "chitti",
        "fastapi",
        "uvicorn",
        "click",
        "pydantic"
    ],
    entry_points={
        "chitti.agents": [
            "{agent}=chitti_{agent}_agent.agent:CustomAgent"
        ]
    }
) 