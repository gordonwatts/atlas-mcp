---
description: Take a question and determine the ATLAS dataset.
tools:
  - atlas_mcp
---

Your job is to analyze the user input below and just provide the dataset or datasets we will use execute the user's prompt.

User input:

```text
$ARGUMENTS
```

Use the following steps to determine the dataset that will be used to run the user's prompt:

1. If the user has a `rucio` DID (Dataset IDentifier) in the statement, then return the DID directly to the user. A typical DID is `mc20_13TeV:mc20_13TeV.311312.MadGraphPythia8EvtGen_A14NNPDF31LO_HSS_LLP_mH125_mS35_ltlow.recon.AOD.e7270_s3234_r13201`.

2. To search for ATLAS DID's, first determine which `scope` the user wants to use. This is connected with the run the user might want to use: the data and Monte Carlo are tied to the run, and the scope depends on those. Possible runs are Run 2 and Run 3 (Run 1 is not supported). Use atlas_mcp tool to determine what scope is what. If the user does not specify a run, assume Run 3.

3. ATLAS has a standard set of recommended datasets for background Monte Carlo. These are grouped by `scope` and also by `addresses`. Use the tools to do to keyword searches for the appropriate `addresses` for datasets in a scope. Select the best address. If you have a choice, it should have `Baseline` as one of the tags in the address.

4. Once you have an address, use the tool `atlas_mcp/get_samples_for_address` tool to find a particular dataset.

5. Select the best matching EVNT dataset for the user question, or more than one if it isn't clear which one to use.

6. Finally, use the `atlas_mcp/get_samples_for_evtgen` tool to find the actual dataset that matches the user's question. If you have a choice, select the one with the most recent period (highest mc letter), and pick the PHYSLITE dataset tier if the user hasn't requested anything specific.

Please reply to the user in the following format:

```text
Scope: <scope>
Tags: <tag1>, <tag2>, ...
Dataset:
  - name: <DID1>
    type: <type1>
    period: <period1>
    x_section: <x_section1>
    k_factor: <k_factor1>
    gen_filter_eff: <gen_filter_eff1>
  - name: <DID2>
    ...
```
