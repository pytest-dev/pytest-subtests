from pathlib import Path

from setuptools import setup


long_description = (
    Path(__file__).parent.joinpath("README.rst").read_text(encoding="UTF-8")
)

setup(
    name="pytest-subtests",
    author="Bruno Oliveira",
    author_email="nicoddemus@gmail.com",
    maintainer="Bruno Oliveira",
    maintainer_email="nicoddemus@gmail.com",
    license="MIT",
    url="https://github.com/pytest-dev/pytest-subtests",
    description="unittest subTest() support and subtests fixture",
    long_description=long_description,
    py_modules=["pytest_subtests"],
    use_scm_version=True,
    setup_requires=["setuptools-scm", "setuptools>=40.0"],
    python_requires=">=3.7",
    install_requires=["pytest>=7.0"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Framework :: Pytest",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: Implementation :: CPython",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
    ],
    entry_points={"pytest11": ["subtests = pytest_subtests"]},
)
