from setuptools import find_packages, setup

setup(
    name="model-deployment-service",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "jinja2",
        "python-multipart",
        "firebase-admin",
        "paramiko",
        "docker",
        "pydantic"
    ],
    python_requires=">=3.8",
)