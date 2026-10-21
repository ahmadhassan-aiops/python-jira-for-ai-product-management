"""Email an acknowledgement to the reporter of every new, unassigned Jira task.

Run it every 3 hours with cron. Settings come from environment variables:
JIRA_SERVER, JIRA_EMAIL, JIRA_API_TOKEN, SENDER_EMAIL, GMAIL_APP_PASSWORD, SUPPORT_CC (optional),
JIRA_PROJECT (default MYP) and LOOKBACK (default -3h, keep it equal to the cron interval).
"""
import os
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from jira import JIRA

PROJECT = os.environ.get("JIRA_PROJECT", "MYP")
LOOKBACK = os.environ.get("LOOKBACK", "-3h")
JQL = (f"project = {PROJECT} AND issuetype = Task AND created >= {LOOKBACK} "
       "AND assignee is EMPTY AND resolution = Unresolved")


def build_body(name, key):
    return (
        f"<p>Dear {name},<br><br>"
        "Thank you for writing to us.<br><br>"
        f"This email confirms that we have received your Jira ticket <b>{key}</b>. "
        "Please send the approval from your reporting manager. Our team is looking into it "
        "and will get back to you soon.<br><br>"
        "Thank you,<br>CloudOps Support Team</p>"
    )


def main():
    jira = JIRA(server=os.environ["JIRA_SERVER"],
                basic_auth=(os.environ["JIRA_EMAIL"], os.environ["JIRA_API_TOKEN"]))
    issues = jira.search_issues(JQL)
    if not issues:
        print("No new Jira tickets in the window", LOOKBACK)
        return

    sender = os.environ["SENDER_EMAIL"]
    cc = os.environ.get("SUPPORT_CC")
    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(sender, os.environ["GMAIL_APP_PASSWORD"])
        for issue in issues:
            reporter = issue.fields.reporter
            email = getattr(reporter, "emailAddress", None)
            if not email:
                print(f"{issue.key}: reporter email is hidden, skipped")
                continue
            msg = MIMEMultipart()
            msg["Subject"] = f"{issue.key}: {issue.fields.summary}"
            msg["From"] = sender
            msg["To"] = email
            if cc:
                msg["Cc"] = cc
            msg.attach(MIMEText(build_body(reporter.displayName, issue.key), "html"))
            smtp.send_message(msg)
            print(f"{issue.key}: mail sent to {reporter.displayName}")
            time.sleep(3)


if __name__ == "__main__":
    main()
