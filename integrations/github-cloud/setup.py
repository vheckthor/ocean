from setuptools import setup, find_packages

setup(
    name="githubcloud",
    version="0.1.0-beta",
    packages=find_packages(),
    install_requires=[
        "port_ocean[cli]>=0.22.10",
        "aiolimiter>=1.1.0",
    ],
    python_requires=">=3.12",
)
