#!/bin/bash

rm -Rf logs/ page/ assets/ templates/ linkbio.egg-info/ linkbio.yaml
pip uninstall linkbio -y
pip install -e .