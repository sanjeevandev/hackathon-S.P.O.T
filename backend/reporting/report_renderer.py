"""Deterministic HTML renderer for structured inspection reports.

Does NOT contain business logic or AI inference logic.
Only renders formatted HTML presentation from an InspectionReport instance.
"""

from backend.reporting.report_contract import InspectionReport


class ReportRenderer:
    """Renders structured inspection reports into clean HTML representations."""

    @staticmethod
    def render_html(report: InspectionReport) -> str:
        grade_display = report.grading.get("prototype_grade") if report.grading else "WITHHELD"
        score_display = f"{report.grading.get('quality_score'):.1f}/100" if report.grading and report.grading.get("quality_score") is not None else "N/A"
        
        stats = report.statistics
        explanation = report.explanation
        model_info = report.model_information
        profile_info = report.grading_profile_information

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>S.P.O.T. Digital Quality Inspection Report - {report.inspection_id}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; color: #0f172a; margin: 0; padding: 24px; }}
        .report-card {{ max-width: 800px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 32px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }}
        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #e2e8f0; padding-bottom: 16px; margin-bottom: 24px; }}
        .title {{ font-size: 24px; font-weight: 700; color: #1e293b; }}
        .disclaimer-banner {{ background-color: #fef2f2; border: 1px solid #fca5a5; color: #991b1b; padding: 12px; border-radius: 6px; font-size: 13px; font-weight: 600; margin-bottom: 24px; }}
        .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }}
        .card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; }}
        .card h3 {{ margin-top: 0; font-size: 14px; text-transform: uppercase; color: #64748b; font-weight: 600; }}
        .grade-badge {{ display: inline-block; font-size: 28px; font-weight: 800; color: #0284c7; margin-top: 4px; }}
        ul {{ margin: 8px 0; padding-left: 20px; }}
        li {{ margin-bottom: 4px; font-size: 14px; }}
        .footer {{ border-top: 1px solid #e2e8f0; padding-top: 16px; margin-top: 32px; font-size: 12px; color: #64748b; display: flex; justify-content: space-between; }}
    </style>
</head>
<body>
    <div class="report-card">
        <div class="header">
            <div>
                <div class="title">S.P.O.T. Digital Quality Inspection Report</div>
                <div style="font-size: 13px; color: #64748b;">Report ID: {report.report_id} (v{report.report_version})</div>
            </div>
            <div style="text-align: right; font-size: 13px; color: #64748b;">
                <div>Inspection: <strong>{report.inspection_id}</strong></div>
                <div>Batch: <strong>{report.batch_id}</strong></div>
                <div>Date: {report.generated_at}</div>
            </div>
        </div>

        <div class="disclaimer-banner">
            ⚠️ {report.disclaimer}
        </div>

        <div class="grid">
            <div class="card">
                <h3>Evaluated Prototype Grade</h3>
                <div class="grade-badge">{grade_display}</div>
                <div style="font-size: 14px; margin-top: 8px;">Commercial Quality Score: <strong>{score_display}</strong></div>
                <div style="font-size: 13px; color: #64748b; margin-top: 4px;">Review Status: <strong>{report.batch_metadata.get('inspection_status', 'COMPLETE')}</strong></div>
            </div>

            <div class="card">
                <h3>Sample Lot Statistics</h3>
                <div style="font-size: 14px;">Total Analyzed Bulbs: <strong>{stats.get('total_analyzed_onions', 0)}</strong></div>
                <ul>
                    <li>Grade-A (Healthy): {stats.get('healthy_percentage', 0.0):.1f}% ({stats.get('healthy_count', 0)})</li>
                    <li>Damaged: {stats.get('damaged_percentage', 0.0):.1f}% ({stats.get('damaged_count', 0)})</li>
                    <li>Rotten: {stats.get('rotten_percentage', 0.0):.1f}% ({stats.get('rotten_count', 0)})</li>
                    <li>Sprouted: {stats.get('sprouted_percentage', 0.0):.1f}% ({stats.get('sprouted_count', 0)})</li>
                    <li>Under-Sized: {stats.get('undersized_percentage', 0.0):.1f}% ({stats.get('undersized_count', 0)})</li>
                </ul>
            </div>
        </div>

        <div class="card" style="margin-bottom: 24px;">
            <h3>Grade Assessment Rationale</h3>
            <div style="font-weight: 600; font-size: 15px; margin-bottom: 8px;">{explanation.get('headline', '')}</div>
            <div style="font-size: 14px; font-weight: 600; color: #334155; margin-top: 8px;">Primary Factors:</div>
            <ul>
                {"".join(f"<li>{factor}</li>" for factor in explanation.get('primary_factors', []))}
            </ul>
        </div>

        <div class="card" style="margin-bottom: 24px;">
            <h3>Mandatory Technical & Physical Limitations</h3>
            <ul>
                {"".join(f"<li>{lim}</li>" for lim in report.limitations)}
            </ul>
        </div>

        <div class="footer">
            <div>Vision Model: <strong>{model_info.get('model_name', '')} ({model_info.get('model_version', '')}) [{model_info.get('source', '')}]</strong></div>
            <div>Grading Profile: <strong>{profile_info.get('profile_name', '')} (v{profile_info.get('version', '')})</strong></div>
        </div>
    </div>
</body>
</html>"""
        return html
