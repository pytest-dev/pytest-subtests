import codecs
import os

from setuptools import setup


def read(fname):
    file_path = os.path.join(os.path.dirname(__file__), fname)
    return codecs.open(file_path, encoding="utf-8").read()


setup(
    name="pytest-subtests",
    version="0.1.0",
    author="Bruno Oliveira",
    author_email="nicoddemus@gmail.com",
    maintainer="Bruno Oliveira",
    maintainer_email="nicoddemus@gmail.com",
    license="MIT",
    url="https://github.com/pytest-dev/pytest-subtests",
    description="unittest subTest() support and subtests fixture",
    long_description=read("README.rst"),
    py_modules=["pytest_subtests"],
    use_scm_version=True,
    setup_requires=["setuptools-scm", "setuptools>=40.0"],
    python_requires=">=3.4",
    install_requires=["pytest>=4.4.0"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Framework :: Pytest",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
    ],
    entry_points={"pytest11": ["subtests = pytest_subtests"]},
)
