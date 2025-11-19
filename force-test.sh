#!/bin/bash

# rm -Rf logs/ page/ linkbio.egg-info/ linkbio.yaml
rm -Rf  build/ dist/ logs/ page/ linkbio.egg-info/ linkbio.yaml
pip uninstall linkbio -y
pip install -e .