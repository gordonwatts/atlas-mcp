import os
from pathlib import Path
from typing import Any, List, Union, Dict, Tuple
import base64
import json

from diskcache import Cache
from pydantic import BaseModel, Field

# Cache location selection:
# - If ATLAS_MCP_CACHE_DIR environment variable is set, use it (useful for tests/CI)
# - Otherwise default to the user's home directory under `.atlas_mcp_cache` for
#   server/external runs.
cache_dir = os.environ.get(
    "ATLAS_MCP_CACHE_DIR", str(Path.home() / ".cache" / "atlas_mcp_cache")
)
cache = Cache(cache_dir)


class CentralPageAddress(BaseModel):
    model_config = {"frozen": True}

    scope: str = Field(description="Data scope name")
    hash_tags: Tuple[str, ...] = Field(description="Tuple of hash tags")


class CentralPageScope(BaseModel):
    scope: str = Field(description="Data Scope name")
    description: str = Field(description="Description of the scope")


class DIDInfo(BaseModel):
    did: str = Field(description="Rucio Dataset Identifier")
    x_sec: float = Field(description="Cross section in pb")
    generator_filter_eff: float = Field(description="Generator filter efficiency")
    k_factor: float = Field(description="K-factor")
    d_type: str = Field(
        description="What data/tier type is this file - AOD, DAOD_PHYS, etc"
    )
    s_type: str = Field(
        description="Simulation type - Full Simulation (FS), Fast Simulation (AF3), etc"
    )
    period: str = Field(description="MC period - mc20, mc21, mc23a, etc.")


# TODO: Figure out how not to hard-wire this!
allowed_scopes = [
    CentralPageScope(
        scope="mc16_13TeV",
        description="MonteCarlo for Run 2 Data, based on Release 21 of the software. Very old."
        " Stay away if possible.",
    ),
    CentralPageScope(
        scope="mc20_13TeV",
        description="MonteCarlo for Run 2 Detector Data, based on Release 22 of the software "
        "(Release 25 is usable).",
    ),
    # CentralPageScope(
    #     scope="mc21_13p6TeV",
    #     description="MonteCarlo for Run 3 Data, second, more modern, campaign",
    # ),
    CentralPageScope(
        scope="mc23_13p6TeV",
        description="MonteCarlo for Run 3 Detector Data, based on Release 25 of the software.",
    ),
]


def get_allowed_scopes() -> List[CentralPageScope]:
    """Returns a list of allowed scopes for the CentralPage MC Sample catalog.

    Returns:
        List[CentralPageScope]: List of scopes and short descriptions
    """
    return allowed_scopes


def run_ami_helper(
    args: str,
    files: Union[Dict[str, Union[str, Path]], None] = None,
) -> List[str]:
    """Runs the ami-helper command with the given arguments and returns the output as a list of
    lines.

    This wraps `run_on_wsl` which runs arbitrary commands on a configured WSL
    distribution. We set up the ATLAS environment, lsetup centralpage, echo a start marker,
    then run `centralpage` with the provided args and return the output lines after the marker.

    Args:
        args (List[str]): List of arguments to pass to the centralpage command

    Returns:
        List[str]: List of output lines after the start marker, or all output lines if the marker
        is not found.
    """
    # Build the command snippet to run inside WSL (after env setup)
    inner_cmd = "echo --start-- && uvx --python=3.11 ami-helper " + args

    # Run inside the centralpage-configured environment.
    stdout = run_on_wsl(inner_cmd, files=files)

    lines = stdout.splitlines()
    try:
        start_index = lines.index("--start--") + 1
        return lines[start_index:]
    except ValueError:
        # If the marker is not found, return all lines as a list
        return lines


def run_on_wsl(
    command: str,
    distro: str = "atlas_al9",
    files: Union[Dict[str, Union[str, Path]], None] = None,
) -> str:
    """Run an arbitrary shell command inside a WSL distro and return raw stdout.

    Args:
        command (str): Shell command to run inside the WSL session.
        distro (str): WSL distribution name to use.
        files (Dict[str, Union[str, Path]], optional): Dictionary of files to copy to /tmp
            in WSL before running the command. Keys are filenames in /tmp, values can be
            strings (content) or Path objects (file paths to copy).

    Returns:
        str: Raw stdout from the executed command.
    """
    import subprocess

    # If files are provided, copy them to /tmp in WSL first
    if files:
        for filename, file_data in files.items():
            wsl_path = f"/tmp/{filename}"

            if isinstance(file_data, Path):
                # File path provided - lets read and write the file.
                if not file_data.exists():
                    raise FileNotFoundError(f"File not found: {file_data}")

                # Load the file in as a massive string
                with open(file_data, "r", encoding="utf-8") as f:
                    file_data = f.read()

            if isinstance(file_data, str):
                # File content provided as string - write to temp file in WSL
                encoded_content = base64.b64encode(file_data.encode("utf-8")).decode(
                    "ascii"
                )
                copy_cmd = [
                    "wsl",
                    "-d",
                    distro,
                    "bash",
                    "-c",
                    f"echo '{encoded_content}' | base64 -d > {wsl_path}",
                ]
                copy_result = subprocess.run(copy_cmd, capture_output=True, text=True)
                if copy_result.returncode != 0:
                    raise RuntimeError(
                        f"Failed to copy string content to WSL: {copy_result.stderr}"
                    )

    cmd = ["wsl", "-d", distro, "bash", "-l", "-c", command]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(
            f"command failed with return code {result.returncode}: {result.stderr}"
        )

    # Return raw stdout; higher-level callers can choose to split/parse it.
    return result.stdout


def get_address_for_keyword(
    scope: str, keywords: str | List[str]
) -> List[CentralPageAddress]:
    """Returns a CentralPageAddress object for a given scope and keyword.

    This searches the hash tag tree up to depth 4 for a hash tag that
    contains the given keyword. If found, it returns the corresponding
    CentralPageAddress object. If not found, it returns None.

    Args:
        scope (str): Scope name
        keyword (str): Keyword to search for in hash tags
    """

    if isinstance(keywords, str):
        keywords = [keywords]

    # Get the keywords that match the first one, and then search those.
    lines = run_ami_helper(f"hashtags find {scope} {keywords[0]}")
    print(lines)
    addresses = []
    for ln in lines:
        parts = ln.split()
        if len(parts) != 4:
            continue
        addr = CentralPageAddress(
            scope=scope,
            hash_tags=tuple(parts),
        )
        addresses.append(addr)

    def has_keyword(addr: CentralPageAddress, keyword: str) -> bool:
        return any(keyword.lower() in t.lower() for t in addr.hash_tags)

    matches = [a for a in addresses if all(has_keyword(a, kw) for kw in keywords)]

    return matches


@cache.memoize()
def get_evtgen_for_address(cpa: CentralPageAddress) -> List[str]:
    """Returns a list of EVTGEN sample names for a given CentralPageAddress.

    Args:
        cpa (CentralPageAddress): CentralPageAddress object
    """
    cmd_args = [*["datasets", "with-hashtags"], f"{cpa.scope}", *cpa.hash_tags]
    output = run_ami_helper(" ".join(cmd_args))
    return output


@cache.memoize()
def get_samples_for_run(scope: str, run_number: str, derivation: str) -> Dict[str, Any]:
    """Returns a list of rucio dataset names for a given EVTGEN sample.

    Args:
        scope (str): Scope name
        evtgen_sample (str): EVTGEN sample name
        derivation (str): Derivation type, e.g. 'PHYS', 'AOD', 'PHYSLITE', 'DAOD_LLP1', etc.
    """
    derivation_flag = ""
    if derivation.upper() == "PHYS":
        derivation_flag = "DAOD_PHYS"
    elif derivation.upper() == "PHYSLITE":
        derivation_flag = "DAOD_PHYSLITE"
    elif derivation.upper().startswith("DAOD_"):
        derivation_flag = derivation.upper()
    else:
        raise RuntimeError(
            "Invalid `derivation` - must be `AOD`, `PHYS`, `PHYSLITE`, `DAOD_xxx`"
        )

    lines = run_ami_helper(
        f"datasets with-datatype {scope} {run_number} {derivation_flag} -o json"
    )

    d = json.loads(" ".join(lines))

    return d


@cache.memoize()
def get_metadata(
    scope: str,
    full_dataset_name: str,
    use_top_of_provenance: bool = False,
) -> Dict[str, Any]:
    """Returns metadata for a given dataset.

    Optionally resolves the dataset to the top of the provenance chain
    (i.e., the original EVNT) before fetching metadata.

    Args:
        scope (str): Scope name (e.g., 'mc20_13TeV', 'mc23_13p6TeV')
        full_dataset_name (str): Full dataset name
        use_top_of_provenance (bool): If True, first call ``get_provenance``
            and use the last dataset in that list as the target for metadata
            lookup. Defaults to False.

    Returns:
        Dict[str, Any]: Dictionary containing metadata fields such as:
            - Physics Comment
            - Physics Short Name
            - Generator Name
            - Filter Efficiency
            - Cross Section (nb)
    """
    target_ds = full_dataset_name
    if use_top_of_provenance:
        prov = get_provenance(scope, full_dataset_name)
        if prov:
            target_ds = prov[-1]

    lines = run_ami_helper(f"datasets metadata {scope} {target_ds} -o json")

    # Join all lines and parse as JSON
    d = json.loads(" ".join(lines))

    return d


@cache.memoize()
def get_provenance(scope: str, dataset_name: str) -> List[str]:
    """Returns the provenance chain for a given dataset.

    Returns all the datasets from the current one back to the original EVNT file.

    Args:
        scope (str): Scope name (e.g., 'mc20_13TeV', 'mc23_13p6TeV')
        dataset_name (str): Dataset name

    Returns:
        List[str]: List of dataset names in the provenance chain, one per line
    """
    lines = run_ami_helper(f"datasets provenance {scope} {dataset_name}")

    return lines
