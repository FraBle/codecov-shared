from shared import ribs
from shared.reports.types import Change


def run_comparison_using_rust(base_report, head_report, diff):
    return ribs.run_comparison(
        base_report.rust_report.get_report(),
        head_report.rust_report.get_report(),
        ribs.rustify_diff(diff),
    )


def get_changes_using_rust(base_report, head_report, diff):
    return _get_changes_from_comparison(
        run_comparison_using_rust(base_report, head_report, diff)
    )


def _get_changes_from_comparison(data):
    changes = []
    for found_change in data["files"]:
        if found_change["unexpected_line_changes"]:
            changes.append(
                Change(
                    path=found_change["head_name"],
                    in_diff=bool(found_change["added_diff_coverage"]),
                    old_path=found_change.get("base_name")
                    if found_change["base_name"] != found_change["head_name"]
                    else None,
                    totals=None,
                    new=(
                        found_change["head_coverage"] is not None
                        and found_change["base_coverage"] is None
                        and not found_change["file_was_added_by_diff"]
                    ),
                    deleted=(
                        found_change["base_coverage"] is not None
                        and found_change["head_coverage"] is None
                        and not found_change["file_was_removed_by_diff"]
                    ),
                )
            )
    return changes
