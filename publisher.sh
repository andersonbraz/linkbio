#!/bin/bash

rm -Rf dist/
python -m build
twine upload dist/*