"""Seed enterprise documents for evaluation."""

import logging
import tempfile
from pathlib import Path

from rag.ingestion import IngestPipeline, QdrantClientManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_sample_documents() -> dict:
    """Create sample PDF and TXT documents for seeding.

    Returns:
        Dictionary with file_path: content pairs.
    """
    sample_docs = {
        "company_policy.txt": """
COMPANY POLICY HANDBOOK
Version: 1.0
Department: HR

1. CODE OF CONDUCT

All employees must adhere to our code of conduct. This includes:
- Professional behavior at all times
- Respectful communication with colleagues
- Compliance with company policies
- Ethical decision making

2. REMOTE WORK POLICY

Employees working remotely must:
- Maintain regular communication with team leads
- Complete assigned tasks on time
- Use company-approved communication tools
- Ensure data security and privacy

3. TIME OFF POLICY

Employees are entitled to:
- 20 days of paid vacation per year
- 10 days of sick leave per year
- Federal holidays observed

4. PROFESSIONAL DEVELOPMENT

The company invests in employee growth through:
- Training programs and certifications
- Conference attendance support
- Mentorship opportunities
- Career advancement paths
""",
        "technical_docs.txt": """
TECHNICAL DOCUMENTATION
Version: 2.1
Department: Engineering

SYSTEM ARCHITECTURE OVERVIEW

The enterprise system consists of:

1. Frontend Layer
   - React-based user interface
   - WebSocket connections for real-time updates
   - Responsive design for mobile and desktop

2. API Layer
   - FastAPI backend
   - RESTful endpoints
   - JWT authentication
   - Rate limiting

3. Data Layer
   - PostgreSQL for transactional data
   - Redis cache for performance
   - Vector database for similarity search
   - S3 for document storage

4. Processing Pipeline
   - Async task queue with Celery
   - Document processing workers
   - Scheduled jobs for maintenance
   - Logging and monitoring

DEPLOYMENT

Deployments use Docker and Kubernetes:
- Docker containers for all services
- Kubernetes orchestration
- CI/CD with GitHub Actions
- Automated testing on every commit
""",
        "budget_report.txt": """
ANNUAL BUDGET REPORT
Date: 2024-01-15
Department: Finance
Version: 1.0

EXECUTIVE SUMMARY

Total budget allocation: $5,000,000
YTD Spending: $3,200,000
Remaining budget: $1,800,000

DEPARTMENTAL BREAKDOWN

Engineering: $2,000,000
- Infrastructure: $800,000
- Development: $900,000
- Operations: $300,000

Sales & Marketing: $1,500,000
- Sales team: $800,000
- Marketing campaigns: $500,000
- Events: $200,000

Operations: $1,000,000
- HR: $400,000
- Finance: $300,000
- Administration: $300,000

Research & Development: $500,000
- Innovation projects: $300,000
- Tools and licenses: $200,000

QUARTERLY FORECAST

Q1 2024: 85% budget utilized
Q2 2024: 90% budget utilized
Q3 2024: 95% budget utilized
Q4 2024: Full budget allocated

Recommendations for cost optimization:
- Renegotiate vendor contracts
- Implement resource consolidation
- Reduce redundant licenses
""",
    }

    return sample_docs


def seed_documents() -> None:
    """Load and ingest sample documents with both chunking strategies."""
    logger.info("Starting document seeding process")

    # Initialize pipeline and Qdrant
    pipeline = IngestPipeline()
    qdrant_manager = QdrantClientManager()

    # Create collection
    logger.info("Ensuring Qdrant collection exists")
    qdrant_manager.create_collection()

    # Health check
    if not qdrant_manager.health_check():
        logger.error("Qdrant server is not accessible")
        return

    sample_docs = create_sample_documents()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create temporary document files
        doc_files = []
        for filename, content in sample_docs.items():
            file_path = tmpdir_path / filename
            file_path.write_text(content, encoding="utf-8")
            doc_files.append(file_path)

        logger.info(f"Created {len(doc_files)} sample documents")

        # Ingest each document with BOTH strategies
        for doc_path in doc_files:
            filename = doc_path.name

            # Define metadata for this document
            if "policy" in filename:
                category = "policies"
                department = "hr"
            elif "technical" in filename:
                category = "technical"
                department = "engineering"
            elif "budget" in filename:
                category = "financial"
                department = "finance"
            else:
                category = "general"
                department = "operations"

            metadata = {
                "department": department,
                "category": category,
                "version": "1.0",
                "date": "2024-01-15",
            }

            # Ingest with FIXED strategy
            logger.info(
                f"Ingesting {filename} with FIXED chunking strategy"
            )
            result_fixed = pipeline.ingest_document(
                file_path=str(doc_path),
                metadata=metadata,
                chunking_strategy="fixed",
            )

            if result_fixed["status"] == "success":
                logger.info(
                    f"✓ Fixed: {filename} - "
                    f"{result_fixed['chunks_created']} chunks, "
                    f"doc_id={result_fixed['doc_id']}"
                )
            else:
                logger.error(
                    f"✗ Fixed: {filename} - {result_fixed.get('error')}"
                )

            # Ingest with ADVANCED strategy
            logger.info(
                f"Ingesting {filename} with ADVANCED chunking strategy"
            )
            result_advanced = pipeline.ingest_document(
                file_path=str(doc_path),
                metadata=metadata,
                chunking_strategy="advanced",
            )

            if result_advanced["status"] == "success":
                logger.info(
                    f"✓ Advanced: {filename} - "
                    f"{result_advanced['chunks_created']} chunks, "
                    f"doc_id={result_advanced['doc_id']}"
                )
            else:
                logger.error(
                    f"✗ Advanced: {filename} - {result_advanced.get('error')}"
                )

    logger.info("Document seeding completed")

    # Summary
    try:
        client = qdrant_manager.get_client()
        collection_info = client.get_collection(
            qdrant_manager.COLLECTION_NAME
        )
        logger.info(
            f"Collection '{qdrant_manager.COLLECTION_NAME}' "
            f"contains {collection_info.points_count} points"
        )
    except Exception as e:
        logger.error(f"Failed to get collection info: {e}")


if __name__ == "__main__":
    seed_documents()
