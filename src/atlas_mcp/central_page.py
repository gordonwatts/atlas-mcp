from typing import Any, Dict, List

import ami_helper.ami as ami
from ami_helper.datamodel import CentralPageHashAddress, get_campaign
from ami_helper.rucio import has_files
from ami_helper.utils import normalize_derivation_name
from pydantic import BaseModel, Field

from atlas_mcp.disk_cache import diskcache_decorator


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


def get_address_for_keyword(
    scope: str,
    keywords: str | List[str],
    ignore_cache: bool = False,
) -> List[CentralPageHashAddress]:
    """Returns a CentralPageHashAddress object for a given scope and keyword.

    This searches the hash tag tree up to depth 4 for a hash tag that
    contains the given keyword. If found, it returns the corresponding
    CentralPageHashAddress object. If not found, it returns None.

    Args:
        scope (str): Scope name
        keyword (str): Keyword to search for in hash tags
    """
    del ignore_cache

    if isinstance(keywords, str):
        keywords = [keywords]

    # Fetch the info from AMI (which is where central_page gets
    # the info from) for any of the hash tags that fit this search
    # string, and then fill in the partial list.
    partial_hashtag_list = ami.find_hashtag(scope, keywords[0])
    ca_list = [t for ht in partial_hashtag_list for t in ami.find_hashtag_tuples(ht)]

    def has_keyword(addr: CentralPageHashAddress, keyword: str) -> bool:
        return any(
            keyword.lower() in t.lower() for t in addr.hash_tags if t is not None
        )

    matches = [a for a in ca_list if all(has_keyword(a, kw) for kw in keywords)]

    return matches


@diskcache_decorator()
def get_evtgen_for_address(cpa: CentralPageHashAddress) -> List[str]:
    """Returns a list of EVTGEN sample names for a given CentralPageHashAddress.

    Args:
        cpa (CentralPageHashAddress): CentralPageHashAddress object
    """

    dids = ami.find_dids_with_hashtags(cpa)
    return dids


@diskcache_decorator()
def get_dataset_with_name(
    scope: str, search_str: str, is_central_page: bool
) -> List[Dict[str, str]]:
    """Returns a list of EVTGEN sample names and tags that contain the given search string
    as a list of dictionaries.

    Args:
        scope (str): Scope name
        search_str (str): Search string to look for in dataset names
        is_central_page (bool): If True, search only central page samples (PMG/central page);
            if False, include non-central-page samples as well.
    Returns:
        List[Dict[str, str]]: List of dictionaries with dataset information. Each entry is a
        dataset, and the name and hash tags are included.
    """

    ds = ami.find_dids_with_name(scope, search_str, require_pmg=is_central_page)

    r_dict = [
        {
            "name": d[0],
            "HashTag 1": d[1].hash_tags[0],
            "HashTag 2": d[1].hash_tags[1],
            "HashTag 3": d[1].hash_tags[2],
            "HashTag 4": d[1].hash_tags[3],
        }
        for d in ds
    ]

    return r_dict


@diskcache_decorator()
def get_samples_for_run(scope: str, run_number: int, derivation: str) -> Dict[str, Any]:
    """Returns a list of rucio dataset names for a given run number.

    Args:
        scope (str): Scope name
        run_number (str): EVTGEN sample name
        derivation (str): Derivation type, e.g. 'PHYS', 'AOD', 'PHYSLITE', 'DAOD_LLP1', etc.
    """

    # Get all the datasets that match, make sure that they have files.
    derivation_flag = normalize_derivation_name(derivation)
    ds_list = ami.get_by_datatype(scope, run_number, derivation_flag)
    good_ds = [ds for ds in ds_list if has_files(scope, ds)]

    # Get the campaign for each dataset.
    short_scope = scope.split("_")[0]

    def get_campaign_with_exception(ds: str) -> str:
        try:
            campaign = get_campaign(short_scope, ds)
        except Exception:
            campaign = ""
        return campaign

    info = {ds: get_campaign_with_exception(ds) for ds in good_ds}

    return info


@diskcache_decorator()
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

    # Make sure we are looking at an EVNT dataset - otherwise
    # metadata may not make sense.
    target_ds = full_dataset_name
    if use_top_of_provenance:
        prov = ami.get_provenance(scope, full_dataset_name)
        if prov:
            target_ds = prov[-1]

    d_meta = ami.get_metadata(scope, target_ds)

    return d_meta


@diskcache_decorator()
def get_provenance(scope: str, dataset_name: str) -> List[str]:
    """Returns the provenance chain for a given dataset.

    Returns all the datasets from the current one back to the original EVNT file.

    Args:
        scope (str): Scope name (e.g., 'mc20_13TeV', 'mc23_13p6TeV')
        dataset_name (str): Dataset name

    Returns:
        List[str]: List of dataset names in the provenance chain, one per line
    """

    ds_list = ami.get_provenance(scope, dataset_name)

    return ds_list
