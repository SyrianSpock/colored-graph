import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="colored_graph",
    version="0.2.0",
    author="Salah Missri",
    author_email="syrianspock@gmail.com",
    description="Python tool to draw graphs with colors",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/syrianspock/colored-graph",
    packages=setuptools.find_packages(),
    install_requires=[
        "graphviz",
        "watchdog",
    ],
    entry_points={
        'console_scripts': [
            'cgraph = colored_graph.colored_graph:main',
        ],
    },
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
)
