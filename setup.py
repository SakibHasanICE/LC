from setuptools import setup,find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="LC Automation",
    version="0.1",
    author="sakib",
    packages=find_packages(),
    install_requires = requirements,
)