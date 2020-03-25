from setuptools import setup


version = "0.1.dev0"

long_description = "\n\n".join([open("README.rst").read(), open("CHANGES.rst").read()])

install_requires = []

tests_require = ["pytest", "mock", "pytest-cov", "pytest-flakes", "pytest-black"]

setup(
    name="fews-3di",
    version=version,
    description="FEWS-3di coupling",
    long_description=long_description,
    # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
    classifiers=["Programming Language :: Python", "Framework :: Django"],
    keywords=[],
    author="Reinout van Rees",
    author_email="reinout.vanrees@nelen-schuurmans.nl",
    url="https://github.com/nens/fews-3di",
    license="MIT",
    packages=["fews_3di"],
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={"test": tests_require},
    entry_points={
        "console_scripts": [
            "run-fews-3di = fews_3di.scripts:main"
        ]
    },
)
