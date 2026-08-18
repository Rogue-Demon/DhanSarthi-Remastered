""""
RAG Evaluation Tool for DhanSarthi.

Computes:
  - Intent Accuracy
  - Hit@1, Hit@3, Hit@5
  - MRR (Mean Reciprocal Rank)
  - Authority Accuracy
  - Citation Accuracy
  - Abstention Accuracy

Generates:
  1. Category-Level Performance Table (9 categories).
  2. Detailed Query-Level Failure Diagnostics.

Can be run via:
  python -m app.ai.evaluate_rag
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.ai.providers.mock import MockEmbeddingProvider
from app.ai.rag.retriever import PostgresRAGRetriever
from app.ai.router import IntentRouter, QueryIntent
from app.core.database import SessionLocal


def load_benchmark_dataset() -> List[Dict[str, Any]]:
    path = Path(__file__).resolve().parent.parent.parent / "data" / "evaluation" / "rag" / "benchmark.json"
    if not path.exists():
        raise FileNotFoundError(f"Benchmark file not found at: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_query_category(item_id: str) -> str:
    if item_id.startswith("c"):
        return "Casual"
    elif item_id.startswith("fb"):
        return "Finance Basics"
    elif item_id.startswith("inv"):
        return "Investments"
    elif item_id.startswith("bk"):
        return "Banking/Credit"
    elif item_id.startswith("tx"):
        return "Tax"
    elif item_id.startswith("h"):
        return "Historical"
    elif item_id.startswith("pf"):
        return "Personal Finance"
    elif item_id.startswith("mx"):
        return "Mixed"
    elif item_id.startswith("adv"):
        return "Adversarial"
    return "Other"


async def evaluate_pipeline(
    benchmark: List[Dict[str, Any]],
    retriever: PostgresRAGRetriever,
    router: IntentRouter,
    legacy_mode: bool = False,
    print_failures: bool = False,
) -> Tuple[Dict[str, float], Dict[str, Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Evaluate retrieval pipeline across benchmark test queries.
    """
    total_queries = len(benchmark)
    correct_intents = 0

    hit1_count = 0
    hit3_count = 0
    hit5_count = 0
    mrr_sum = 0.0
    rag_query_count = 0

    authority_correct_count = 0
    authority_evaluated_count = 0

    citation_valid_count = 0
    citation_evaluated_count = 0

    abstain_correct_count = 0
    abstain_evaluated_count = 0

    category_stats: Dict[str, Dict[str, Any]] = {}
    failed_queries: List[Dict[str, Any]] = []

    categories = [
        "Casual", "Finance Basics", "Investments", "Banking/Credit",
        "Tax", "Historical", "Personal Finance", "Mixed", "Adversarial"
    ]
    for cat in categories:
        category_stats[cat] = {
            "total": 0,
            "rag_total": 0,
            "hit1": 0,
            "hit3": 0,
            "hit5": 0,
            "mrr_sum": 0.0,
            "auth_correct": 0,
            "auth_total": 0,
            "abstain_correct": 0,
            "abstain_total": 0,
        }

    for item in benchmark:
        item_id = item["id"]
        cat_name = get_query_category(item_id)
        category_stats[cat_name]["total"] += 1

        query_text = item["query"]
        expected_intent = item["intent"]
        expected_behavior = item.get("expected_behavior", "RETRIEVE_RAG")
        acceptable_sources = item.get("acceptable_sources", [])
        expected_authority = item.get("expected_authority")
        acceptable_authorities = item.get("acceptable_authorities", [])

        if expected_authority and expected_authority not in acceptable_authorities:
            acceptable_authorities.append(expected_authority)

        # 1. Intent Accuracy
        classified_intent = router.classify(query_text).value
        if classified_intent == expected_intent:
            correct_intents += 1

        # 2. Non-RAG Queries / Abstention Evaluation
        if expected_behavior in ("NO_RAG", "FINANCIAL_ENGINE", "MARKET_DATA", "ABSTAIN"):
            abstain_evaluated_count += 1
            category_stats[cat_name]["abstain_total"] += 1

            retrieved_docs = await retriever.retrieve(query_text, legacy_mode=legacy_mode)

            # Verification of correct non-RAG routing / abstention
            if len(retrieved_docs) == 0:
                abstain_correct_count += 1
                category_stats[cat_name]["abstain_correct"] += 1
            elif expected_behavior == "NO_RAG" and classified_intent == "CASUAL":
                abstain_correct_count += 1
                category_stats[cat_name]["abstain_correct"] += 1
            elif expected_behavior == "FINANCIAL_ENGINE" and classified_intent == "PERSONAL_FINANCE":
                abstain_correct_count += 1
                category_stats[cat_name]["abstain_correct"] += 1

            continue

        # 3. RAG Retrieval Queries Evaluation (RETRIEVE_RAG or MIXED)
        rag_query_count += 1
        category_stats[cat_name]["rag_total"] += 1

        retrieved_docs = await retriever.retrieve(query_text, legacy_mode=legacy_mode)

        if not retrieved_docs:
            failure_info = {
                "id": item_id,
                "query": query_text,
                "intent": expected_intent,
                "expected_topic": item.get("expected_topic"),
                "expected_authority": expected_authority,
                "normalized_query": retriever._query_processor.normalize(query_text) if hasattr(retriever, "_query_processor") else query_text,
                "expanded_terms": retriever._query_processor.expand_query(query_text) if hasattr(retriever, "_query_processor") else [],
                "retrieved_docs": [],
                "reason": "Retriever returned zero docs (abstained or similarity below threshold)."
            }
            failed_queries.append(failure_info)
            continue

        # Citation Completeness Check
        citation_evaluated_count += len(retrieved_docs)
        for doc in retrieved_docs:
            if doc.document_id and doc.title and doc.source and doc.metadata.get("source_url"):
                citation_valid_count += 1

        # Calculate Hit@1, Hit@3, Hit@5 and MRR
        first_match_rank = 0
        expected_topic = item.get("expected_topic", "").lower()

        for idx, doc in enumerate(retrieved_docs, start=1):
            title_lower = doc.title.lower()
            content_lower = doc.content.lower()

            match = False
            for acc in acceptable_sources:
                acc_l = acc.lower()
                if acc_l in title_lower or acc_l in content_lower:
                    match = True
                    break

            if not match and expected_topic:
                if expected_topic in title_lower or expected_topic in content_lower or expected_topic in str(doc.metadata.get("category")).lower():
                    match = True

            if match:
                first_match_rank = idx
                break

        if first_match_rank > 0:
            reciprocal_rank = 1.0 / first_match_rank
            mrr_sum += reciprocal_rank
            category_stats[cat_name]["mrr_sum"] += reciprocal_rank

            if first_match_rank == 1:
                hit1_count += 1
                category_stats[cat_name]["hit1"] += 1
            if first_match_rank <= 3:
                hit3_count += 1
                category_stats[cat_name]["hit3"] += 1
            if first_match_rank <= 5:
                hit5_count += 1
                category_stats[cat_name]["hit5"] += 1
        else:
            failure_info = {
                "id": item_id,
                "query": query_text,
                "intent": expected_intent,
                "expected_topic": item.get("expected_topic"),
                "expected_authority": expected_authority,
                "normalized_query": doc.metadata.get("query_normalized", query_text),
                "expanded_terms": doc.metadata.get("query_expanded_terms", []),
                "retrieved_docs": [
                    {
                        "title": d.title,
                        "source": d.source,
                        "authority": d.metadata.get("authority"),
                        "score": d.relevance_score,
                        "breakdown": d.metadata.get("score_breakdown", {})
                    }
                    for d in retrieved_docs[:5]
                ],
                "reason": "Top-5 retrieved chunks did not match expected topic or acceptable source titles."
            }
            failed_queries.append(failure_info)

        # Authority Accuracy check
        if acceptable_authorities:
            authority_evaluated_count += 1
            category_stats[cat_name]["auth_total"] += 1
            top_doc = retrieved_docs[0]
            doc_auth = top_doc.metadata.get("authority")
            doc_auth_str = str(doc_auth).replace("KnowledgeAuthority.", "").upper() if doc_auth else ""

            auth_matched = False
            for acc_auth in acceptable_authorities:
                if acc_auth.upper() in doc_auth_str or acc_auth.upper() in top_doc.source.upper():
                    auth_matched = True
                    break

            if auth_matched:
                authority_correct_count += 1
                category_stats[cat_name]["auth_correct"] += 1

    intent_acc = (correct_intents / total_queries) * 100.0 if total_queries else 0.0
    hit1_rate = (hit1_count / rag_query_count) * 100.0 if rag_query_count else 0.0
    hit3_rate = (hit3_count / rag_query_count) * 100.0 if rag_query_count else 0.0
    hit5_rate = (hit5_count / rag_query_count) * 100.0 if rag_query_count else 0.0
    mrr = (mrr_sum / rag_query_count) if rag_query_count else 0.0

    authority_acc = (authority_correct_count / authority_evaluated_count) * 100.0 if authority_evaluated_count else 100.0
    citation_acc = (citation_valid_count / citation_evaluated_count) * 100.0 if citation_evaluated_count else 100.0
    abstain_acc = (abstain_correct_count / abstain_evaluated_count) * 100.0 if abstain_evaluated_count else 100.0

    overall_metrics = {
        "intent_accuracy": round(intent_acc, 2),
        "hit1": round(hit1_rate, 2),
        "hit3": round(hit3_rate, 2),
        "hit5": round(hit5_rate, 2),
        "mrr": round(mrr, 4),
        "authority_accuracy": round(authority_acc, 2),
        "citation_accuracy": round(citation_acc, 2),
        "abstention_accuracy": round(abstain_acc, 2),
    }

    return overall_metrics, category_stats, failed_queries


async def main():
    print("========================================")
    print("DhanSarthi Phase J — RAG Quality Audit & Evaluation")
    print("========================================")

    benchmark = load_benchmark_dataset()
    print(f"Loaded benchmark dataset: {len(benchmark)} test queries\n")

    db = SessionLocal()
    try:
        embedding_provider = MockEmbeddingProvider()
        router = IntentRouter()
        retriever = PostgresRAGRetriever(db, embedding_provider)

        print("Executing Baseline Retrieval Pipeline Evaluation...")
        base_metrics, base_cats, base_failures = await evaluate_pipeline(benchmark, retriever, router, legacy_mode=True)

        print("Executing Upgraded Phase J Pipeline Evaluation...\n")
        upgraded_metrics, upgraded_cats, upgraded_failures = await evaluate_pipeline(benchmark, retriever, router, legacy_mode=False, print_failures=True)

        # 1. OVERALL BEFORE vs AFTER METRICS
        print("=" * 60)
        print(f"{'Metric':<25} | {'BEFORE (Baseline)':<18} | {'AFTER (Phase J)':<15}")
        print("=" * 60)
        print(f"{'Intent Accuracy':<25} | {base_metrics['intent_accuracy']:<17}% | {upgraded_metrics['intent_accuracy']:<15}%")
        print(f"{'Hit@1':<25} | {base_metrics['hit1']:<17}% | {upgraded_metrics['hit1']:<15}%")
        print(f"{'Hit@3':<25} | {base_metrics['hit3']:<17}% | {upgraded_metrics['hit3']:<15}%")
        print(f"{'Hit@5':<25} | {base_metrics['hit5']:<17}% | {upgraded_metrics['hit5']:<15}%")
        print(f"{'MRR':<25} | {base_metrics['mrr']:<18} | {upgraded_metrics['mrr']:<15}")
        print(f"{'Authority Accuracy':<25} | {base_metrics['authority_accuracy']:<17}% | {upgraded_metrics['authority_accuracy']:<15}%")
        print(f"{'Citation Accuracy':<25} | {base_metrics['citation_accuracy']:<17}% | {upgraded_metrics['citation_accuracy']:<15}%")
        print(f"{'Abstention Accuracy':<25} | {base_metrics['abstention_accuracy']:<17}% | {upgraded_metrics['abstention_accuracy']:<15}%")
        print("=" * 60 + "\n")

        # 2. CATEGORY-LEVEL RESULTS TABLE
        print("=" * 105)
        print(f"{'Category':<18} | {'Total':<6} | {'Hit@1':<8} | {'Hit@3':<8} | {'Hit@5':<8} | {'MRR':<8} | {'Auth Acc':<10} | {'Abstain Acc':<10}")
        print("=" * 105)
        for cat_name, stats in upgraded_cats.items():
            tot = stats["total"]
            rag_tot = stats["rag_total"]
            h1 = round((stats["hit1"] / rag_tot) * 100, 1) if rag_tot else 0.0
            h3 = round((stats["hit3"] / rag_tot) * 100, 1) if rag_tot else 0.0
            h5 = round((stats["hit5"] / rag_tot) * 100, 1) if rag_tot else 0.0
            mrr_val = round(stats["mrr_sum"] / rag_tot, 4) if rag_tot else 0.0
            auth_val = round((stats["auth_correct"] / stats["auth_total"]) * 100, 1) if stats["auth_total"] else 100.0
            abst_val = round((stats["abstain_correct"] / stats["abstain_total"]) * 100, 1) if stats["abstain_total"] else 100.0

            print(f"{cat_name:<18} | {tot:<6} | {h1:<7}% | {h3:<7}% | {h5:<7}% | {mrr_val:<8} | {auth_val:<9}% | {abst_val:<9}%")
        print("=" * 105 + "\n")

        # 3. QUERY-LEVEL FAILURES REPORT
        print(f"FAILED RETRIEVALS REPORT ({len(upgraded_failures)} total failures out of {len(benchmark)} queries):")
        print("=" * 90)
        for f in upgraded_failures:
            print(f"Query ID [{f['id']}] Category: {get_query_category(f['id'])}")
            print(f"  Query: \"{f['query']}\"")
            print(f"  Intent: {f['intent']} | Expected Topic: {f['expected_topic']} | Expected Auth: {f['expected_authority']}")
            print(f"  Normalized: \"{f['normalized_query']}\" | Expanded: {f['expanded_terms']}")
            print(f"  Reason: {f['reason']}")
            if f["retrieved_docs"]:
                print("  Top Retrieved Chunks:")
                for d in f["retrieved_docs"]:
                    print(f"    - {d['title']} ({d['source']}) | Final Score: {d['score']} | Breakdown: {d['breakdown']}")
            print("-" * 90)

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
