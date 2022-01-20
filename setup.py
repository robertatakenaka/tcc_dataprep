#!/usr/bin/env python3
import os, setuptools

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README.md")) as f:
    README = f.read()

CHANGES = ""

with open(os.path.join(here, "LICENSE")) as f:
    LICENSE = f.read()

requires = [

]

tests_require = [

]

setuptools.setup(
    name="dataprep",
    version="0.1",
    author="Roberta Takenaka",
    author_email="takenaka.roberta.bw@gmail.com",
    description="",
    long_description=README + "\n\n" + CHANGES,
    long_description_content_type="text/markdown",
    license="GNU GENERAL PUBLIC LICENSE",
    packages=setuptools.find_packages(
        exclude=["*.tests", "*.tests.*", "tests.*", "tests"]
    ),
    include_package_data=True,
    extras_require={"testing": tests_require},
    install_requires=requires,
    dependency_links=[
    ],
    python_requires=">=3.6",
    test_suite="tests",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Other Environment",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3 :: Only",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Operating System :: OS Independent",
    ],
	entry_points={
        "console_scripts":[
			"rs_prep_csv=dataprep.harvesting.seq2csv:main",
			"migration_prep=dataprep.preparation.migration_inputs:main",
            "rs_migration_prep=dataprep.preparation.migration_inputs:main",
            "rs_migrate=dataprep.migration_from_isis:main",
        ]
    }
)
