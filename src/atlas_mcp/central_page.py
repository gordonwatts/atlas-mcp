from dataclasses import dataclass
from typing import List
from pydantic import BaseModel, Field

# Disk-backed cache for expensive calls
from diskcache import Cache

# Initialize cache (default location: .cache directory in project root)
cache = Cache(".cache")


@dataclass
class CentralPageAddress:
    scope: str
    hash_tags: List[str]


class CentralPageScope(BaseModel):
    scope: str = Field(description="Data Scope name")
    description: str = Field(description="Description of the scope")


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


def run_centralpage(args: List[str]) -> List[str]:
    """Runs the centralpage command with the given arguments and returns the output.

    This is run on an atlas_al9 wsl2 instance. The following commands are run:

    > setupATLAS
    > lsetup centralpage
    > centralpage <args>

    All output is returned.

    Args:
        args (List[str]): List of arguments to pass to the centralpage command

    Returns:
        str: Output of the centralpage command
    """
    import subprocess

    # Build the command to run on WSL2 instance 'atlas_al9'
    wsl_cmd = (
        "export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase &&"
        " source /cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase/user/atlasLocalSetup.sh &&"
        " lsetup centralpage &&"
        " echo --start-- &&"
        " centralpage " + " ".join(args)
    )
    cmd = [
        "wsl",
        "-d",
        "atlas_al9",
        "bash",
        "-l",
        "-c",
        wsl_cmd,
    ]

    # Run the command
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(
            f"centralpage command failed with return code {result.returncode}: {result.stderr}"
        )

    lines = result.stdout.splitlines()
    try:
        start_index = lines.index("--start--") + 1
        output_lines = lines[start_index:]
    except ValueError:
        raise ValueError(
            f"Could not find start marker in centralpage output: {result.stdout}"
        )

    return output_lines


@cache.memoize()
def get_hash_tags(cpa: CentralPageAddress) -> List[str]:
    """Returns a list of hash tags for a given CentralPageAddress.

    Args:
        cpa (CentralPageAddress): CentralPageAddress object
    """
    # Build the command
    cmd_args = [f"--scope={cpa.scope}", *cpa.hash_tags, "--list_hashtags"]
    output = run_centralpage(cmd_args)
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
