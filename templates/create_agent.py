#!/usr/bin/env python3
"""Script to create a new Chitti agent from template"""

import os
import shutil
import sys
from pathlib import Path
import click

@click.command()
@click.argument("agent_name")
@click.option("--output-dir", default=".", help="Directory to create the agent in")
def create_agent(agent_name: str, output_dir: str):
    """Create a new Chitti agent from template"""
    # Normalize agent name
    agent_name = agent_name.lower().replace("-", "_")
    
    # Get template directory
    template_dir = Path(__file__).parent / "chitti-{agent}-agent"
    if not template_dir.exists():
        click.echo(f"Template directory not found: {template_dir}")
        sys.exit(1)
    
    # Create target directory
    target_dir = Path(output_dir) / f"chitti-{agent_name}-agent"
    if target_dir.exists():
        click.echo(f"Target directory already exists: {target_dir}")
        sys.exit(1)
    
    # Copy template
    shutil.copytree(template_dir, target_dir)
    
    # Rename source directory
    src_dir = target_dir / "src" / "chitti_{agent}_agent"
    new_src_dir = target_dir / "src" / f"chitti_{agent_name}_agent"
    src_dir.rename(new_src_dir)
    
    # Replace placeholders in all files
    for path in target_dir.rglob("*"):
        if path.is_file():
            content = path.read_text()
            content = content.replace("{agent}", agent_name)
            path.write_text(content)
    
    click.echo(f"""
Created new agent: {agent_name}
Location: {target_dir}

To install:
cd {target_dir}
pip install -e .

To use:
from chitti_{agent_name}_agent import CustomAgent
    """)

if __name__ == "__main__":
    create_agent() 