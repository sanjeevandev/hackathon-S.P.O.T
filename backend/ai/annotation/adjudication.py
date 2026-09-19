import math
from typing import Dict, Any, List, Tuple

class AnnotationAdjudicator:
    """Calculates inter-annotator agreement metrics & manages double-annotation adjudication."""

    @staticmethod
    def calculate_cohens_kappa(labels_a: List[int], labels_b: List[int]) -> float:
        """Computes Cohen's Kappa coefficient between two binary annotator sequences."""
        if len(labels_a) != len(labels_b) or len(labels_a) == 0:
            return 0.0

        n = len(labels_a)
        tp = sum(1 for a, b in zip(labels_a, labels_b) if a == 1 and b == 1)
        tn = sum(1 for a, b in zip(labels_a, labels_b) if a == 0 and b == 0)
        fp = sum(1 for a, b in zip(labels_a, labels_b) if a == 0 and b == 1)
        fn = sum(1 for a, b in zip(labels_a, labels_b) if a == 1 and b == 0)

        po = (tp + tn) / n
        pe_a = ((tp + fn) / n) * ((tp + fp) / n)
        pe_b = ((tn + fp) / n) * ((tn + fn) / n)
        pe = pe_a + pe_b

        if pe == 1.0:
            return 1.0
        kappa = (po - pe) / (1.0 - pe)
        return round(kappa, 4)

    @staticmethod
    def evaluate_agreement(records_a: List[Dict[str, Any]], records_b: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluates Inter-Annotator Agreement across 4 defect categories for double-annotated subset."""
        # Index records by image_id
        map_a = {r["image_id"]: r for r in records_a}
        map_b = {r["image_id"]: r for r in records_b}

        common_images = sorted(list(set(map_a.keys()) & set(map_b.keys())))
        total_common = len(common_images)

        if total_common == 0:
            return {
                "double_annotated_count": 0,
                "overall_percent_agreement": 0.0,
                "cohens_kappa_by_defect": {},
                "disagreements": []
            }

        defects_keys = ["healthy", "damage", "rot", "sprout"]
        kappa_results = {}
        matching_labels_count = 0
        total_label_evals = total_common * len(defects_keys)
        disagreements = []

        for def_key in defects_keys:
            seq_a = [1 if map_a[img]["multi_label_defects"].get(def_key, False) else 0 for img in common_images]
            seq_b = [1 if map_b[img]["multi_label_defects"].get(def_key, False) else 0 for img in common_images]

            kappa = AnnotationAdjudicator.calculate_cohens_kappa(seq_a, seq_b)
            kappa_results[def_key] = kappa

            for idx, img in enumerate(common_images):
                if seq_a[idx] == seq_b[idx]:
                    matching_labels_count += 1
                else:
                    disagreements.append({
                        "image_id": img,
                        "defect_dimension": def_key,
                        "annotator_a_value": bool(seq_a[idx]),
                        "annotator_b_value": bool(seq_b[idx]),
                        "adjudication_status": "PENDING_ADJUDICATION"
                    })

        overall_agreement = round((matching_labels_count / total_label_evals) * 100, 2)

        return {
            "double_annotated_count": total_common,
            "overall_percent_agreement": overall_agreement,
            "cohens_kappa_by_defect": kappa_results,
            "disagreement_count": len(disagreements),
            "disagreements_sample": disagreements[:50]
        }
