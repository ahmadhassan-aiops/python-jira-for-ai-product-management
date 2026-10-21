"""Create one Jira issue per row of a CSV file.

Usage:  python3 bulk_create_from_csv.py ../data/sample_jira_issues.csv [--dry-run]
Columns: Summary, Project Key, Issue Type, Description, Priority
Settings: JIRA_SERVER, JIRA_EMAIL, JIRA_API_TOKEN
"""
import csv
import os
import sys

PRIORITY_MAP = {"Critical": "Highest"}     # Jira Cloud has no "Critical" priority by default


def read_rows(path):
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            row["Priority"] = PRIORITY_MAP.get(row["Priority"], row["Priority"])
            yield row


def main(path, dry_run):
    jira = None
    if not dry_run:
        from jira import JIRA
        jira = JIRA(server=os.environ["JIRA_SERVER"],
                    basic_auth=(os.environ["JIRA_EMAIL"], os.environ["JIRA_API_TOKEN"]))
    for row in read_rows(path):
        label = f"{row['Project Key']} | {row['Issue Type']:<5} | {row['Priority']:<7} | {row['Summary']}"
        if dry_run:
            print("would create:", label)
            continue
        issue = jira.create_issue(project=row["Project Key"], summary=row["Summary"],
                                  description=row["Description"],
                                  issuetype={"name": row["Issue Type"]},
                                  priority={"name": row["Priority"]})
        print(f"created {issue.key}:", label)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1], "--dry-run" in sys.argv)
