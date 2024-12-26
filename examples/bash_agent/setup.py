"""Setup script for the bash agent"""

from setuptools import setup, find_namespace_packages

setup(
    name="chitti-bash-agent",
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
            "bash=chitti_bash_agent.agent:BashAgent"
        ]
    }
) 