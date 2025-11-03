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

### Inside `vscode`

Preparation:

1. First, fire up your `atlas_al9` `wsl2` instance, and `voms-proxy-init` to get a token that gives you access to the ATLAS metadata. You'll need to be a member of ATLAS to use this tool!
1. Run the command `uvx --python=3.11 ami-helper hashtags find mc23_13p6TeV DiJet` to make sure initial installation occurs (some error messages confuse the LLM that aren't error messages).
1. Open the `mcp.json` file found in `.vscode` and make sure to start the mcp server (a little inline option just above the server should present itself - click start, or restart, or if it is running, etc.)

In the agent mode, set the LLM to something like `GPT-5 mini` (no need to waste tokens, this is fairly simple work), and then `/data all-hadronic ttbar`. Grant it permission.

## Testing

Use `mcp dev src/atlas_mcp/server.py` to run locally with the test web interface.

## Sample Run in `vscode`

This was kicked off with `/data all-hadronic ttbar`.

```text
gordonwatts: Follow instructions in [data.prompt.md](file:///c%3A/Users/gordo/Code/llms/atlas-mcp/.github/prompts/data.prompt.md).
all-hadronic ttbar

GitHub Copilot: I'll first fetch the list of allowed MC scopes so I can pick the appropriate Run (Run 3 preferred) before searching for ttbar/all-hadronic hashtags or datasets. Expecting a short list of scopes like mc20_13TeV, mc21_13TeV, mc23_13TeV. I'll use that to choose the scope for a subsequent keyword search.

Ran `get_allowed_scopes`
Completed with input: {}

Now I'll search the Run 3 scope `mc23_13p6TeV` for hashtags/addresses containing the keyword "ttbar" to find the standard-model ttbar (all-hadronic) datasets. I expect a list of hashtag 4-tuples to pick the most relevant.

Ran `get_addresses_for_keyword`
Completed with input: {
  "scope": "mc23_13p6TeV",
  "keyword": "ttbar",
  "baseline_only": true
}

I'll fetch the EVNT-generation sample names for the most relevant ttbar hashtag tuple ["Top","TTbar","Baseline","PowhegPythia"] in `mc23_13p6TeV` to find run numbers and dataset names to inspect further. I expect a list of EVNT rucio IDs.

Ran `get_evtgen_for_address`
Completed with input: {
  "scope": "mc23_13p6TeV",
  "hashtags": [
    "Top",
    "TTbar",
    "Baseline",
    "PowhegPythia"
  ]
}

Ran `get_samples_for_run`
Completed with input: {
  "scope": "mc23_13p6TeV",
  "run_number": "601237",
  "data_tier": "PHYSLITE"
}

I'll fetch metadata for a representative DAOD_PHYSLITE dataset from run 601237 to extract cross-section, filter eff, and description. I'll query the dataset `mc23_13p6TeV.601237.PhPy8EG_A14_ttbar_hdamp258p75_allhad.deriv.DAOD_PHYSLITE.e8514_s4369_r16083_p6697`.

Ran `get_metadata`
Completed with input: {
  "scope": "mc23_13p6TeV",
  "dataset_name": "mc23_13p6TeV.601237.PhPy8EG_A14_ttbar_hdamp258p75_allhad.deriv.DAOD_PHYSLITE.e8514_s4369_r16083_p6697",
  "use_top_of_provenance": true
}

Scope: mc23_13p6TeV
Tags: Top, TTbar, Baseline, PowhegPythia
Dataset:

- name: mc23_13p6TeV.601237.PhPy8EG_A14_ttbar_hdamp258p75_allhad.deriv.DAOD_PHYSLITE.e8514_s4369_r16083_p6697
    type: DAOD_PHYSLITE
    period: mc23e
    x_section: 0.81129
    gen_filter_eff: 0.4561725
    description: POWHEG+Pythia8 ttbar production with Powheg hdamp equal 1.5*top mass, A14 tune for allhad events.
    comments: EVNT run 601237; generator: Powheg(v2)+Pythia8+EvtGen. Representative Run-3 all-hadronic ttbar PHYSLITE derivation.
```
