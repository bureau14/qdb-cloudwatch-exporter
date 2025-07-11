# qdb-cloudwatch-exporter
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Export QuasarDB cluster statistics to AWS CloudWatch

## Usage
```bash
$ qdb-cloudwatch --cluster qdb://127.0.0.1:2836 --cluster-public-key /path/to/public/key --user-security-file /path/to/security/file --node-id "0-0-0-1" --namespace "quasardb.cluster" --filter-include "memory.+total,count" --filter-exclude "bytes$"
```

## Build wheel package
```bash
$ python3 setup.py bdist_wheel -d dist
```
