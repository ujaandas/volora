from setuptools import setup

setup(
    name="volora",
    version="0.1.0",
    py_modules=["main"],
    entry_points={
        "console_scripts": [
            "volora=main:main",
        ],
    },
)
