#!/bin/bash
set -e

# Run Makefile load target for 3 different accounts
make load config=config/pipeline_config_merge_clean_save.json log_level=INFO

