"""Open a Highest-priority Jira ticket when a server's available memory is low.

Settings: JIRA_SERVER, JIRA_EMAIL, JIRA_API_TOKEN, SSH_HOSTS (comma separated), SSH_USER,
SSH_PASSWORD or SSH_KEY_FILE, ONCALL_ACCOUNT_ID, JIRA_PROJECT (default IIP),
ISSUE_TYPE (default Issue) and THRESHOLD_GB (default 1).
"""
import os

import paramiko
from jira import JIRA

PROJECT = os.environ.get("JIRA_PROJECT", "IIP")
ISSUE_TYPE = os.environ.get("ISSUE_TYPE", "Issue")
THRESHOLD_GB = int(os.environ.get("THRESHOLD_GB", "1"))


def available_memory_gb(host):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=os.environ["SSH_USER"],
                   password=os.environ.get("SSH_PASSWORD"),
                   key_filename=os.environ.get("SSH_KEY_FILE"))
    try:
        _, stdout, _ = client.exec_command("free -g")
        mem_line = stdout.readlines()[1]          # the "Mem:" line
        return int(mem_line.split()[6])           # the "available" column
    finally:
        client.close()


def main():
    jira = JIRA(server=os.environ["JIRA_SERVER"],
                basic_auth=(os.environ["JIRA_EMAIL"], os.environ["JIRA_API_TOKEN"]))
    for host in [h.strip() for h in os.environ["SSH_HOSTS"].split(",") if h.strip()]:
        available = available_memory_gb(host)
        if available > THRESHOLD_GB:
            print(f"{host}: memory is good ({available}GB available)")
            continue

        summary = f"Memory available {available}GB and Server name is {host}"
        open_tickets = jira.search_issues(
            f'project = {PROJECT} AND summary ~ "\\"{host}\\"" AND resolution = Unresolved')
        if open_tickets:
            jira.add_comment(open_tickets[0], f"Still low: {available}GB available")
            print(f"{host}: updated {open_tickets[0].key}")
            continue

        new_issue = jira.create_issue(fields={
            "project": {"key": PROJECT},
            "issuetype": {"name": ISSUE_TYPE},
            "summary": summary,
            "description": f"Hi Team, we found a low memory issue on this server {host}.\n{summary}",
            "priority": {"name": "Highest"},
        })
        if os.environ.get("ONCALL_ACCOUNT_ID"):
            new_issue.update(assignee={"accountId": os.environ["ONCALL_ACCOUNT_ID"]})
        print(f"{host}: created {new_issue.key}")


if __name__ == "__main__":
    main()
