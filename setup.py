from setuptools import setup

setup(
    name="sls",
    version="0.1",
    py_modules=["sls"],
    entry_points={
        "console_scripts": [
            "sls = sls:main",
        ],
    },
)
