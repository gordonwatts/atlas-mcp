---
description: Take a question and determine the ATLAS dataset.
tools:
  - atlas_mcp
---

The user input can be provided directly by the agent or as a command argument - you **MUST** consider it before proceeding with the prompt (if not empty).

User input:

$ARGUMENTS

This prompt you strictly answer a question and reply to the user and do not need to read or write any project files.

1. If the user has a `rucio` did in the statement, then return the did below. A typical DID is `mc20_13TeV:mc20_13TeV.311312.MadGraphPythia8EvtGen_A14NNPDF31LO_HSS_LLP_mH125_mS35_ltlow.recon.AOD.e7270_s3234_r13201`.

2. To search for datasets first determine which `scope` the user wants to use. This is connected with the run the user might want to use: the data and Monte Carlo are tied to the run, and the scope depends on those. Possible runs are Run 2 and Run 3 (Run 1 is not supported). Use tools to determine what scope is what. If the user does not specify a run, assume Run 3.

3. ATLAS has a standard set of recommended datasets for background Monte Carlo. These are grouped by `scope` and also by `addresses`. Use the tools to do to keyword searches for the appropriate `addresses` for datasets in a scope.

4. Select the best matching dataset for the user question. If you have a choice, it should have `Baseline` as one of the tags in the address.

Let the user know the scope and address where you think the dataset can be located.
