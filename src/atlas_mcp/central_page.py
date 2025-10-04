import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

from diskcache import Cache
from pydantic import BaseModel, Field

# Cache location selection:
# - If ATLAS_MCP_CACHE_DIR environment variable is set, use it (useful for tests/CI)
# - Otherwise default to the user's home directory under `.atlas_mcp_cache` for
#   server/external runs.
cache_dir = os.environ.get("ATLAS_MCP_CACHE_DIR", str(Path.home() / ".atlas_mcp_cache"))
cache = Cache(cache_dir)


@dataclass
class CentralPageAddress:
    scope: str
    hash_tags: List[str]


class CentralPageScope(BaseModel):
    scope: str = Field(description="Data Scope name")
    description: str = Field(description="Description of the scope")


class DIDInfo(BaseModel):
    did: str = Field(description="Rucio Dataset Identifier")


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


def run_centralpage(args: List[str]) -> str | List[str]:
    """Runs the centralpage command with the given arguments and returns the output.

    This wraps `run_on_wsl` which runs arbitrary commands on a configured WSL
    distribution. Keeping the high-level behavior the same: we set up the
    ATLAS environment, lsetup centralpage, echo a start marker, then run
    `centralpage` with the provided args and return the output lines after
    the marker.

    Args:
        args (List[str]): List of arguments to pass to the centralpage command

    Returns:
        str | List[str]: If the start marker is present, returns the list of lines
        after the marker. If not present (e.g., in certain mocked or direct
        subprocess scenarios), returns the raw stdout string.
    """
    # Build the command snippet to run inside WSL (after env setup)
    inner_cmd = "echo --start-- && centralpage " + " ".join(args)

    # Run inside the centralpage-configured environment. If the
    # start marker is present in the output, return the list of lines after
    # the marker (this is the original behavior). If not present, return the
    # raw stdout string (this helps unit tests that mock subprocess.run).
    stdout = run_in_centralpage_env(inner_cmd)

    lines = stdout.splitlines()
    try:
        start_index = lines.index("--start--") + 1
        return lines[start_index:]
    except ValueError:
        return stdout


def run_in_centralpage_env(command: str, distro: str = "atlas_al9") -> str:
    """Run a command inside WSL after configuring the ATLAS centralpage environment.

    This sets up the environment by exporting ATLAS_LOCAL_ROOT_BASE, sourcing
    atlasLocalSetup.sh, and performing `lsetup centralpage` before executing
    the provided command. Returns raw stdout from the execution.

    Args:
        command (str): The shell snippet to execute after the environment is set up.
        distro (str): The WSL distribution name.

    Returns:
        str: Raw stdout from the invoked command.
    """
    env_setup = (
        "export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase &&"
        " source /cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase/user/atlasLocalSetup.sh &&"
        " lsetup centralpage &&"
    )

    # Concatenate environment setup with the requested command
    inner = f"{env_setup} {command}" if command else env_setup
    return run_on_wsl(inner, distro=distro)


def run_on_wsl(
    command: str, distro: str = "atlas_al9", start_marker: str = "--start--"
) -> str:
    """Run an arbitrary shell command inside a WSL distro and return raw stdout.

    Note: The ``start_marker`` parameter is ignored and retained only for
    backward compatibility. Callers that need to split output should do so
    themselves after receiving the returned string.

    Args:
        command (str): Shell command to run inside the WSL session.
        distro (str): WSL distribution name to use.
        start_marker (str): Deprecated; ignored.

    Returns:
        str: Raw stdout from the executed command.
    """
    import subprocess

    cmd = ["wsl", "-d", distro, "bash", "-l", "-c", command]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(
            f"command failed with return code {result.returncode}: {result.stderr}"
        )

    # Return raw stdout; higher-level callers can choose to split/parse it.
    return result.stdout


@cache.memoize()
def get_hash_tags(cpa: CentralPageAddress) -> List[str]:
    """Returns a list of hash tags for a given CentralPageAddress.

    Args:
        cpa (CentralPageAddress): CentralPageAddress object
    """
    # Build the command
    # Build a deterministic command args list
    cmd_args = [f"--scope={cpa.scope}", *cpa.hash_tags, "--list_hashtags"]
    output = run_centralpage(cmd_args)

    # If run_centralpage returns a single string, split into lines; if it
    # already returned a list, keep it.
    if isinstance(output, str):
        return [line for line in output.splitlines() if line]
    return output


def get_addresses_for_scope(scope: str) -> List[CentralPageAddress]:
    """Returns a list of CentralPageAddress objects for a given scope.

    These are found by traversing the hash tag tree up to depth 4, which
    is expensive (so the first time this is called it will take a while!).

    Args:
        scope (str): Scope name
    """
    # As we get each new hash tag in depth (up to 4), we need to generate
    # the list from central page. This is potentially expensive, so we cache it.

    stack: List[CentralPageAddress] = [CentralPageAddress(scope=scope, hash_tags=[])]
    result: List[CentralPageAddress] = []

    while len(stack) > 0:
        current = stack.pop()
        tags = get_hash_tags(current)
        if len(tags) == 0:
            result.append(current)
        elif len(current.hash_tags) >= 3:
            for tag in tags:
                new_address = CentralPageAddress(
                    scope=current.scope, hash_tags=current.hash_tags + [tag]
                )
                result.append(new_address)
        else:
            for tag in tags:
                new_address = CentralPageAddress(
                    scope=current.scope, hash_tags=current.hash_tags + [tag]
                )
                stack.append(new_address)

    return result


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
    addresses = get_addresses_for_scope(scope)
    matches = [
        addr
        for addr in addresses
        if all(
            any(keyword.lower() in tag.lower() for tag in addr.hash_tags)
            for keyword in keywords
        )
    ]
    return matches


def get_evtgen_for_address(cpa: CentralPageAddress) -> List[str]:
    """Returns a list of EVTGEN sample names for a given CentralPageAddress.

    Args:
        cpa (CentralPageAddress): CentralPageAddress object
    """
    cmd_args = [f"--scope={cpa.scope}", *cpa.hash_tags]
    output = run_centralpage(cmd_args)
    if isinstance(output, str):
        return [line for line in output.splitlines() if line]
    return output


def get_samples_for_evtgen(evtgen_samples: List[str]) -> List[DIDInfo]:
    """Returns a list of rucio dataset names for a given list of EVTGEN sample names.

    Args:
        evtgen_samples (List[str]): List of EVTGEN sample names
    """
    result = []
    # for sample in evtgen_samples:

    # # Filter to only those that look like rucio dataset names
    # samples = [s for s in evtgen_samples if s.startswith("mc")]
    return result
