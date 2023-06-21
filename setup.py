# -*- coding: utf-8 -*-

"""setup.py: setuptools control."""

import re
from setuptools import setup

# Should equal quasardb api version
version = "3.15.0.dev0"

setup(
    name = "qdb-cloudwatch",
    packages = ["qdb_cloudwatch"],
    entry_points = {
        "console_scripts": ['qdb-cloudwatch = qdb_cloudwatch.check:main']
        },
    version = version,
    description = "Export QuasarDB statistics to AWS Cloudwatch",

    install_requires=[
        "boto3>=1.9",
        "quasardb"],

      extras_require={
          "pandas": ["pandas"],
          "tests": [
              "pytest >= 6.2.5",
              "pytest-runner >= 5.3.1"]
      }
    )
