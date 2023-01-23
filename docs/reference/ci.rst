***********
Using on CI
***********

You can speed up the execution on CI systems caching the directory
used by **project-config** to store the persistent cache between runs.

This directory is output to STDOUT executing ``project-config show cache``

.. note::

   The cache will be stored the time defined at ``cache``
   configuration field.

Github Actions
==============

.. code-block:: yaml

   name: CI

   on:
     workflow_dispatch:
     pull_request:
     push:
       branches:
         - master
       tags:
         - v*

   jobs:
     lint:
       name: Lint
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: "3.10"
         - name: Install dependencies
           run: pip install project-config
         - name: Get project-config cache directory
           id: project-config-cache
           run: echo "directory=$(project-config show cache)" >> $GITHUB_OUTPUT
         - name: Cache project-config
           uses: actions/cache@v3
           with:
             path: ${{ steps.project-config-cache.outputs.directory }}
             key: ${{ steps.project-config-cache.outputs.directory }}
         - name: Lint
           run: hatch run style:lint
