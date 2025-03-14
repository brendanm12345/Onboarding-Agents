from setuptools import setup, find_packages

setup(
    name="onboarding-agents",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pyaudio",
        "openai",
        "pydantic",
    ],
)