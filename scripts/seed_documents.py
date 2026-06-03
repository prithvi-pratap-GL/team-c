"""Seed documents for demo - creates sample documents across all departments"""
import uuid
import os
from datetime import datetime


SAMPLE_DOCUMENTS = [
    {
        "filename": "hr_policy_handbook_2024.txt",
        "department": "hr",
        "category": "policy",
        "version": "2.1",
        "doc_date": "2024-01-15",
        "content": """HR POLICY HANDBOOK 2024

Annual Leave Entitlement
========================
Each employee is entitled to the following:
- Base annual leave: 20 days per year
- Bank holidays: 8 days per year
- Parental leave: Up to 12 weeks unpaid
- Sick leave: 5 days per year
- Compassionate leave: 3 days per year

Leave requests should be submitted at least 2 weeks in advance through the HR portal.
Approval is granted on a first-come, first-served basis.

Overtime Calculation
====================
Overtime is calculated as follows:
- Weekday overtime: 1.5x hourly rate
- Weekend work: 2x hourly rate
- Public holidays: 2.5x hourly rate

Overtime must be pre-approved by your manager.
"""
    },
    {
        "filename": "engineering_deployment_guide.txt",
        "department": "engineering",
        "category": "guide",
        "version": "3.2",
        "doc_date": "2024-02-01",
        "content": """DEPLOYMENT GUIDE - ENGINEERING

Deployment Process
==================
1. Merge to main branch
2. Automated tests must pass
3. Code review approval required (2 reviewers)
4. Deployment automatically triggered

Rollback Procedure
==================
If a deployment fails or introduces critical bugs:

Step 1: Identify the issue
- Check error logs in CloudWatch
- Monitor application metrics
- Verify database state

Step 2: Rollback the deployment
Use ONE of these methods:

METHOD A: Git revert (preferred)
$ git revert <commit-hash>
$ git push origin main
This automatically triggers redeployment of previous version

METHOD B: Deploy previous release
$ aws s3 cp s3://releases/app-v3.1.0.zip ./
$ deploy.sh

Step 3: Verify rollback
- Monitor deployment logs (5-10 minutes)
- Run smoke tests
- Check critical endpoints

Step 4: Post-rollback
- Notify on-call team in #incidents
- Schedule postmortem for next day
- Update JIRA ticket with root cause

Expected recovery time: 15 minutes
Typical downtime: 2-3 minutes
"""
    },
    {
        "filename": "operations_incident_tracking.txt",
        "department": "operations",
        "category": "incident",
        "version": "1.0",
        "doc_date": "2024-03-01",
        "content": """INCIDENT TRACKING AND MANAGEMENT

Incident INC-2024-003
====================
Date: 2024-03-15
Time: 14:30 UTC
Duration: 2 hours 15 minutes
Severity: P1 (Critical)

Summary:
Database connection pool exhausted, causing API timeouts for all services.

Root Cause:
A database migration script was left running in production, consuming all 100 available connections.
The script was supposed to run only in staging but was executed in production due to a missing environment check.

Timeline:
14:30 - Alerts triggered for 5xx errors
14:35 - On-call engineer paged
14:40 - Identified high connection count to RDS
14:45 - Killed long-running migration process
14:50 - Services recovered
16:45 - Full recovery and verification

Impact:
- 450 failed API requests
- 180 affected users
- $2,400 in SLA credits owed

Resolution:
1. Killed long-running database process
2. Restarted connection pool
3. Deployed fix to prevent env-based execution

Prevention:
- Added environment checks before migrations
- Reduced migration script timeout
- Improved monitoring for connection pool usage

SLA Tiers
=========
Incident Severity: P1 (Critical - Org-wide outage)
Response Time: 15 minutes
Resolution Target: 4 hours
Escalation: VP of Engineering at 30 minutes no progress
"""
    },
    {
        "filename": "support_faq.txt",
        "department": "product_support",
        "category": "faq",
        "version": "4.1",
        "doc_date": "2024-02-20",
        "content": """FREQUENTLY ASKED QUESTIONS - CUSTOMER SUPPORT

How do I reset a user password?
==============================
If a user has forgotten their password:

1. Go to the admin dashboard
2. Navigate to Users section
3. Search for the user by email or ID
4. Click "Reset Password"
5. A password reset link will be emailed to the user
6. User clicks link and creates new password
7. Password expires after 24 hours if not used

Note: Users should NOT share passwords. If a password is compromised:
- Reset immediately
- Force logout from all sessions
- Review account activity logs

How long are support tickets retained?
======================================
Support ticket data retention policy:

Active tickets: Kept indefinitely
Closed tickets: Retained for 90 days, then archived
Archived tickets: Kept for 2 years, then deleted
Confidential tickets: Marked for 1-year retention

Ticket search is available for all retained tickets.
Customers can request a ticket export within 30 days of closure.

API gateway ports
=================
The API gateway exposes these ports:
- Port 80: HTTP (redirects to HTTPS)
- Port 443: HTTPS (secure, use this)
- Port 8080: Internal metrics endpoint (no auth)

Example API calls:
$ curl https://api.example.com/v1/status
$ curl -H "Authorization: Bearer <token>" https://api.example.com/v1/data
"""
    },
]


def create_sample_doc(doc_info: dict) -> None:
    """Create a sample document file"""
    filename = f"sample_docs/{doc_info['filename']}"
    os.makedirs("sample_docs", exist_ok=True)

    with open(filename, 'w') as f:
        f.write(doc_info['content'])

    print(f"✓ Created {filename}")


def main():
    """Create all sample documents"""
    print("Creating sample documents for demo...\n")

    for doc in SAMPLE_DOCUMENTS:
        create_sample_doc(doc)

    print("\n✓ All sample documents created in sample_docs/")
    print(f"✓ Total documents: {len(SAMPLE_DOCUMENTS)}")
    print("\nTo ingest these documents:")
    print("1. Start the backend: uvicorn app.main:app")
    print("2. Login: curl -X POST http://localhost:8000/api/v1/auth/login \\")
    print('     -d \'{"username":"admin","password":"admin123"}\'')
    print("3. Ingest: for file in sample_docs/*; do")
    print("     curl -X POST http://localhost:8000/api/v1/ingest \\")
    print('       -H "Authorization: Bearer $TOKEN" \\')
    print('       -F "file=@$file" \\')
    print('       -F "metadata={\\"department\\":\\"engineering\\", ...}"')
    print("   done")


if __name__ == "__main__":
    main()
