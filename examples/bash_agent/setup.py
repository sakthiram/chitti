from setuptools import setup, find_packages

setup(
    name="chitti-bash-agent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "chitti",
        "fastapi",
        "uvicorn"
    ],
    entry_points={
        "chitti.agents": [
            "bash=chitti_bash_agent:BashAgent"
        ]
    }
) 