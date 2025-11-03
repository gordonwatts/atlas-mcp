# atlas-mcp

Exploring `mcp` servers that are tuned to run against ATLAS infrastructure

## Introduction

This is a place to collect some tooling that uses an `mcp` interface to expose ATLAS metadata to an LLM. At the moment everything here is very experimental.

THe current tools expose limited amounts from the following datasources:

- AMI dataset metadata
- Rucio

While the tool code itself runs on all platforms, it uses a `cli` called [`ami-helper`](https://github.com/gordonwatts/ami-helper) to access the data.

**NOTE** This is currently very experimental. Indeed, it is so experimental in part because it requires the `ami-helper` tool, and that can only run on Linux that has `/cvmfs` mounted. And the tool currently expects that to happen on Window's `wsl2` with the `atlas_al9` image installed!! Yes, this is considered a bug.

## Usage

Runs on Windows only, because it requires `ami-helper`.

## Testing

Use `mcp dev src/atlas_mcp/server.py` to run locally with the test web interface.
