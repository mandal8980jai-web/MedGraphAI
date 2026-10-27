import re
import json
import time
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.core.logging import logger
from app.services.medicine_matcher import normalize_medicine_name, match_medicine_name
from app.services.gemini_client import call_gemini_with_search, call_gemini_chat

# In-memory evidence cache keyed by normalized query: { findings, sources, evidence_tier, timestamp }
_EVIDENCE_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SECONDS = 3600  # 1 hour

# Common INN / USAN / Generic mappings for accurate database retrieval
GENERIC_ALIASES = {
    "dolo": "acetaminophen",
    "dolo 650": "acetaminophen",
    "paracetamol": "acetaminophen",
    "crocin": "acetaminophen",
    "calpol": "acetaminophen",
    "pacimol": "acetaminophen",
    "panadol": "acetaminophen",
    "brufen": "ibuprofen",
    "ecosprin": "aspirin",
    "disprin": "aspirin",
    "glycomet": "metformin",
    "atorva": "atorvastatin",
    "mox": "amoxicillin",
    "novamox": "amoxicillin",
    "coumadin": "warfarin",
    "warf": "warfarin",
    "klaricid": "clarithromycin",
    "zocor": "simvastatin",
    "pan": "pantoprazole",
    "pan 40": "pantoprazole",
    "pantocid": "pantoprazole",
    "azithral": "azithromycin",
    "azee": "azithromycin",
    "montair": "montelukast",
    "montair lc": "montelukast",
}


def _format_fda_date(raw_date: Optional[str]) -> Optional[str]:
    """Convert openFDA date format 'YYYYMMDD' to 'YYYY-MM-DD'."""
    if not raw_date or len(raw_date) != 8:
        return raw_date
    try:
        dt = datetime.strptime(raw_date, "%Y%m%d")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return raw_date


def query_openfda_drug_label(medicine_name: str, timeout_sec: int = 4) -> Optional[Dict[str, Any]]:
    """
    Query authoritative OpenFDA Drug Label API (U.S. FDA official regulatory database).
    Returns real official label metadata, indications, warnings, effective date, and URL.
    """
    clean_norm = normalize_medicine_name(medicine_name)
    query_term = GENERIC_ALIASES.get(clean_norm, clean_norm)
    if not query_term or len(query_term) < 3:
        return None

    # Search generic_name, brand_name, or substance_name
    encoded_term = urllib.parse.quote(query_term)
    url = f"https://api.fda.gov/drug/label.json?search=(openfda.generic_name:\"{encoded_term}\"+OR+openfda.brand_name:\"{encoded_term}\"+OR+openfda.substance_name:\"{encoded_term}\")&limit=1"

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "MediGraphAI-EvidenceBot/1.0 (Clinical-Decision-Support)"}
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            if resp.status != 200:
                return None
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("results", [])
            if not results:
                return None

            item = results[0]
            openfda = item.get("openfda", {})

            brand_names = openfda.get("brand_name", [])
            generic_names = openfda.get("generic_name", [])
            substance_names = openfda.get("substance_name", [])

            display_name = generic_names[0] if generic_names else (brand_names[0] if brand_names else query_term.capitalize())
            effective_time = _format_fda_date(item.get("effective_time"))

            # Extract official excerpts
            findings: List[str] = []

            # Indications
            indications_raw = item.get("indications_and_usage") or item.get("purpose")
            if indications_raw and isinstance(indications_raw, list) and indications_raw[0]:
                cleaned_ind = " ".join(indications_raw[0].split()[:45]).strip()
                if not cleaned_ind.endswith("."):
                    cleaned_ind += "..."
                findings.append(f"Official Indications: {cleaned_ind}")

            # Warnings / Precautions
            warnings_raw = item.get("boxed_warning") or item.get("warnings_and_cautions") or item.get("warnings")
            if warnings_raw and isinstance(warnings_raw, list) and warnings_raw[0]:
                cleaned_warn = " ".join(warnings_raw[0].split()[:45]).strip()
                if not cleaned_warn.endswith("."):
                    cleaned_warn += "..."
                findings.append(f"Key Precautions: {cleaned_warn}")

            # Drug interactions excerpt
            interactions_raw = item.get("drug_interactions")
            if interactions_raw and isinstance(interactions_raw, list) and interactions_raw[0]:
                cleaned_inter = " ".join(interactions_raw[0].split()[:35]).strip()
                if not cleaned_inter.endswith("."):
                    cleaned_inter += "..."
                findings.append(f"Interaction Profile: {cleaned_inter}")

            if not findings:
                findings.append(f"Official FDA drug label record verified for {display_name}.")

            label_title = f"FDA Official Drug Label: {display_name.title()}"
            if brand_names and brand_names[0].lower() != display_name.lower():
                label_title += f" ({brand_names[0].title()})"

            # Direct DailyMed reference link for label
            dailymed_url = f"https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query={urllib.parse.quote(query_term)}"

            return {
                "findings": findings,
                "sources": [{
                    "title": label_title,
                    "url": dailymed_url,
                    "publication_date": effective_time,
                    "source_type": "official_drug_label",
                    "evidence_excerpt": findings[0] if findings else f"Official regulatory drug monograph for {display_name}."
                }],
                "effective_date": effective_time,
                "verified_name": display_name
            }

    except urllib.error.HTTPError as e:
        if e.code == 404:
            # Clean no-results from openFDA (e.g. invented medicine name)
            logger.debug(f"OpenFDA returned 404 (no match) for '{query_term}'.")
            return None
        logger.warning(f"OpenFDA API HTTP {e.code} for '{query_term}': {e.reason}")
        return None
    except Exception as e:
        logger.warning(f"OpenFDA API connection error for '{query_term}': {e}")
        return None


def query_pubmed_literature(medicine_name: str, timeout_sec: int = 4) -> Optional[Dict[str, Any]]:
    """
    Query NCBI PubMed E-Utilities for real peer-reviewed medical citations.
    Returns article title, PubMed link, publication year, and journal.
    """
    clean_norm = normalize_medicine_name(medicine_name)
    query_term = GENERIC_ALIASES.get(clean_norm, clean_norm)
    if not query_term or len(query_term) < 3:
        return None

    encoded_term = urllib.parse.quote(f"{query_term} AND (clinical indication OR adverse effects)")
    search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={encoded_term}&retmode=json&retmax=2"

    req = urllib.request.Request(
        search_url,
        headers={"User-Agent": "MediGraphAI-EvidenceBot/1.0 (PubMed-Research)"}
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            if resp.status != 200:
                return None
            search_data = json.loads(resp.read().decode("utf-8"))
            id_list = search_data.get("esearchresult", {}).get("idlist", [])
            if not id_list:
                return None

        # Fetch summaries for PMIDs
        pmids_str = ",".join(id_list[:2])
        summary_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmids_str}&retmode=json"
        req_sum = urllib.request.Request(
            summary_url,
            headers={"User-Agent": "MediGraphAI-EvidenceBot/1.0 (PubMed-Research)"}
        )

        with urllib.request.urlopen(req_sum, timeout=timeout_sec) as s_resp:
            if s_resp.status != 200:
                return None
            sum_data = json.loads(s_resp.read().decode("utf-8"))
            result_map = sum_data.get("result", {})

            sources = []
            findings = []

            for pmid in id_list[:2]:
                doc = result_map.get(pmid)
                if not doc or not isinstance(doc, dict):
                    continue
                title = doc.get("title", "").strip().rstrip(".")
                pubdate = doc.get("pubdate", "")
                source_journal = doc.get("source", "PubMed")

                if title:
                    findings.append(f"Clinical Evidence ({source_journal}): {title}.")
                    sources.append({
                        "title": f"{title} [{source_journal}]",
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                        "publication_date": pubdate,
                        "source_type": "peer_reviewed_research",
                        "evidence_excerpt": f"Peer-reviewed study published in {source_journal} regarding {query_term}."
                    })

            if sources:
                return {"findings": findings, "sources": sources}
            return None

    except Exception as e:
        logger.warning(f"PubMed E-utilities query error for '{query_term}': {e}")
        return None


def retrieve_medicine_evidence(
    medicine: Dict[str, Any],
    other_medicines: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Hybrid Evidence Retrieval:
    Combines deterministic local catalog checking with live external medical evidence.

    Clearly distinguishes:
      - 'local_catalog': Known medicine in curated catalog
      - 'live_evidence': Live authoritative data retrieved from openFDA / DailyMed / PubMed / Grounding
      - 'cached_evidence': Retrieved from session cache
      - 'ai_generated': Synthesized general pharmacology explanation
      - 'not_confidently_identified': Unknown / unindexed medication (e.g. invented names)
      - 'research_unavailable': Provider failure / timeout / missing config
    """
    med_id = medicine.get("id", "")
    med_name = medicine.get("name_text", "")
    normalized_name = normalize_medicine_name(med_name)

    # Step 0: Check in-memory cache
    if normalized_name in _EVIDENCE_CACHE:
        cached = _EVIDENCE_CACHE[normalized_name]
        if time.time() - cached.get("timestamp", 0) < CACHE_TTL_SECONDS:
            return {
                "medicine_id": med_id,
                "medicine_name": med_name,
                "findings": cached["findings"],
                "sources": cached["sources"],
                "evidence_tier": "cached_evidence",
                "status": "ok",
                "flags": []
            }

    # Step 1: Check local catalog matching
    cat_match = match_medicine_name(med_name)
    is_in_local_catalog = cat_match.get("match_status") == "matched"
    matched_ingredients = cat_match.get("ingredients", [])

    # Step 2: Attempt Gemini Google Search Grounding (if supported on account)
    gemini_search_attempted = False
    gemini_grounding_success = False
    grounding_findings: List[str] = []
    grounding_sources: List[Dict[str, Any]] = []

    prompt = (
        f"You are a Clinical Pharmacist Research Assistant investigating medication evidence.\n"
        f"Target Medication: {med_name}.\n"
        "Research verified medical evidence regarding:\n"
        f"1. Common clinical indications / uses for {med_name}.\n"
        "2. Important precautions or patient cautions.\n"
        "Respond in valid JSON: {\"findings\": [\"Statement 1\", \"Statement 2\"]}"
    )

    try:
        res = call_gemini_with_search(prompt)
        gemini_search_attempted = True
        if res.get("status") == "ok" and res.get("sources"):
            gemini_grounding_success = True
            raw_sources = res["sources"]
            grounding_sources = [
                {
                    "title": s.get("title") or "Medical Web Reference",
                    "url": s.get("url"),
                    "publication_date": None,
                    "source_type": "google_search_grounding",
                    "evidence_excerpt": "Verified web source citation from Gemini Search Grounding."
                }
                for s in raw_sources if s.get("url")
            ]
            if res.get("parsed_json") and isinstance(res["parsed_json"], dict):
                grounding_findings = [str(f) for f in res["parsed_json"].get("findings", [])]
    except Exception as e:
        logger.debug(f"Gemini search call bypassed or unavailable: {e}")

    if gemini_grounding_success and grounding_sources and grounding_findings:
        evidence_result = {
            "medicine_id": med_id,
            "medicine_name": med_name,
            "findings": grounding_findings,
            "sources": grounding_sources,
            "evidence_tier": "live_evidence",
            "status": "ok",
            "flags": []
        }
        _EVIDENCE_CACHE[normalized_name] = {**evidence_result, "timestamp": time.time()}
        return evidence_result

    # Step 3: Authoritative Public Medical APIs (openFDA Drug Label API + PubMed NCBI)
    fda_data = query_openfda_drug_label(med_name)
    pubmed_data = query_pubmed_literature(med_name)

    combined_findings = []
    combined_sources = []

    if fda_data:
        combined_findings.extend(fda_data.get("findings", []))
        combined_sources.extend(fda_data.get("sources", []))

    if pubmed_data:
        combined_findings.extend(pubmed_data.get("findings", []))
        combined_sources.extend(pubmed_data.get("sources", []))

    if combined_findings and combined_sources:
        evidence_result = {
            "medicine_id": med_id,
            "medicine_name": med_name,
            "findings": combined_findings,
            "sources": combined_sources,
            "evidence_tier": "live_evidence",
            "status": "ok",
            "flags": []
        }
        _EVIDENCE_CACHE[normalized_name] = {**evidence_result, "timestamp": time.time()}
        return evidence_result

    # Step 4: Unknown / Unindexed Medicine (No results from FDA or PubMed)
    if not is_in_local_catalog and not fda_data and not pubmed_data:
        # Honest no-results for unknown or invented medicine names (e.g. 'Zylocran 50mg')
        return {
            "medicine_id": med_id,
            "medicine_name": med_name,
            "findings": [
                f"No verified medical evidence or official drug labels found in authoritative medical databases (FDA, DailyMed, PubMed) for '{med_name}'.",
                "Uncatalogued medicine name. Please confirm exact spelling and formulation directly with your prescribing physician or pharmacist."
            ],
            "sources": [],
            "evidence_tier": "not_confidently_identified",
            "status": "no_results",
            "flags": ["Uncatalogued and unverified medicine name"]
        }

    # Step 5: If in local catalog but live external network APIs were unreachable
    if is_in_local_catalog:
        ing_str = ", ".join(matched_ingredients) if matched_ingredients else "active ingredients"
        catalog_findings = [
            f"Catalog Match: Identified as {cat_match.get('candidates', [med_name])[0]} with active ingredient ({ing_str}).",
            "Deterministic clinical safety rules and duplicate ingredient checks are active.",
            "External live evidence databases were temporarily unreachable; displayed results are based on verified local demonstration catalog."
        ]
        return {
            "medicine_id": med_id,
            "medicine_name": med_name,
            "findings": catalog_findings,
            "sources": [],
            "evidence_tier": "local_catalog",
            "status": "ok",
            "flags": ["External evidence retrieval fallback to local catalog"]
        }

    # Step 6: Total failure / service unavailable
    return {
        "medicine_id": med_id,
        "medicine_name": med_name,
        "findings": [
            "Evidence research is currently unavailable for this medication. External medical research services could not be reached."
        ],
        "sources": [],
        "evidence_tier": "research_unavailable",
        "status": "unavailable",
        "flags": ["Evidence research service unavailable"]
    }
