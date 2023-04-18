from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pollev-history-compiler",
    version="1.0.2",
    author="Tony Abou Zeidan",
    author_email="tony.azp25@gmail.com",
    description="A script for the compilation of PollEverywhere history CSV files into more usable forms.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tony-zeidan/PollEvHistoryCompiler",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    python_requires=">=3.6",
    install_requires=[
        'pandas',
        'markdownify',
        'toml'
    ],
    package_data={
        "pollev_tools": [
            "../resources/html-styles.css",
            "../resources/config.ini",

        ],
    },
    entry_points={
        "console_scripts": [
            "pollev-compiler = pollev_tools.reader:main",
        ],
    },
)