#!/bin/sh

set -ex

rm -rf build dist
TMPDIR=/var/tmp/ pyinstaller \
    -y \
    --onefile \
    --name project-config \
    --copy-metadata project-config \
    --hidden-import project_config.serializers.editorconfig \
    --hidden-import project_config.serializers.ini \
    --hidden-import project_config.serializers.json \
    --hidden-import project_config.serializers.contrib.pre_commit \
    --hidden-import pyjson5 \
    --hidden-import project_config.serializers.python \
    --hidden-import project_config.serializers.text \
    --hidden-import project_config.serializers.toml \
    --hidden-import project_config.serializers.yaml \
    --hidden-import project_config.fetchers.file \
    --hidden-import project_config.fetchers.github \
    --hidden-import project_config.fetchers.https \
    --hidden-import project_config.commands.check \
    --hidden-import project_config.commands.clean \
    --hidden-import project_config.commands.fix \
    --hidden-import project_config.commands.init \
    --hidden-import project_config.commands.show \
    --hidden-import project_config.reporters.default \
    --hidden-import project_config.reporters.ghf_markdown \
    --hidden-import project_config.reporters.json_ \
    --hidden-import project_config.reporters.table \
    --hidden-import project_config.reporters.toml \
    --hidden-import project_config.reporters.yaml \
    --hidden-import project_config.plugins.contrib \
    --hidden-import project_config.plugins.existence \
    --hidden-import project_config.plugins.inclusion \
    --hidden-import project_config.plugins.jmespath \
    --hidden-import project_config.plugins.contrib.pre_commit \
    src/project_config/__main__.py
