# Deployment Guide - Enterprise RAG Assistant

## Overview

This guide covers deploying the Enterprise RAG system across different environments: **development**, **staging**, and **production**.

## Environment Setup

### Prerequisites

- Docker Desktop 4.15+ (or Docker Engine + Docker Compose)
- Python 3.11 (for local development)
- Git 2.40+
- 8GB RAM minimum, 16GB recommended
- 20GB disk space for Qdrant storage

### 1. Local Development Setup

```bash
# Clone the repository
cd challenge/team-c

# Create .env file from template
cp .env.example .env

# Edit .env with your credentials
nano .env
# Required: OPENAI_API_KEY=sk-...

# Start all services
docker-compose up

# Monitor startup (wait for health checks)
docker-compose ps

# Check service status
curl http://localhost/health          # Nginx → Backend
curl http://localhost:8000/health     # Backend directly
curl http://localhost:6333/health     # Qdrant
```

**Expected output after ~2 minutes**:
```
rag-postgres    ✓ UP (healthy)
rag-qdrant      ✓ UP (healthy)
rag-redis       ✓ UP (healthy)
rag-backend     ✓ UP
rag-frontend    ✓ UP
rag-nginx       ✓ UP
```

### 2. Seed Demo Data

```bash
# Generate sample documents
docker-compose exec backend python scripts/seed_documents.py

# Verify
ls -la sample_docs/
# Should show 4 files:
# - hr_policy_handbook_2024.txt
# - engineering_deployment_guide.txt
# - operations_incident_tracking.txt
# - support_faq.txt
```

### 3. Test Ingestion (via API)

```bash
# 1. Login to get access token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

echo "Token: $TOKEN"

# 2. Upload a document
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample_docs/hr_policy_handbook_2024.txt" \
  -F "metadata={\"department\":\"hr\",\"category\":\"policy\",\"version\":\"2.1\"}"

# 3. Query
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"What is the annual leave entitlement?","session_id":"demo-1"}'
```

### 4. Run Tests

```bash
# Unit tests
docker-compose exec backend pytest tests/ -v

# With coverage report
docker-compose exec backend pytest tests/ --cov=backend --cov-report=html

# View report
open htmlcov/index.html
```

### 5. Run Experiments

```bash
docker-compose exec backend python scripts/run_experiments.py

# Output: experiment_report_YYYYMMDD_HHMMSS.md
cat experiment_report_*.md
```

## Staging Deployment

### Create Staging Environment

```bash
# Create staging .env
cat > .env.staging << EOF
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://rag_user:rag_password@postgres-staging:5432/rag_db
QDRANT_URL=http://qdrant-staging:6333
REDIS_URL=redis://redis-staging:6379
JWT_SECRET_KEY=change-this-to-secure-value
API_TITLE=Enterprise RAG (Staging)
ENVIRONMENT=staging
EOF

# Start with staging compose file
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d
```

### Staging Checklist

- [ ] All services passing health checks
- [ ] OPENAI_API_KEY configured
- [ ] JWT_SECRET_KEY changed from default
- [ ] Database backed up
- [ ] Tests passing (100% coverage)
- [ ] Load testing completed (50 concurrent users)
- [ ] Security scanning passed (no critical vulnerabilities)

## Production Deployment

### Prerequisites

- Kubernetes cluster (EKS, GKE, AKS) OR managed container service
- PostgreSQL managed database (RDS, CloudSQL, Azure Database)
- Qdrant cluster deployment (3+ nodes)
- Redis cluster (Sentinel mode minimum)
- Domain name with SSL certificate
- Secrets management (AWS Secrets Manager, Azure Key Vault)

### Production Checklist

**Security**:
- [ ] Change JWT_SECRET_KEY to cryptographically random value
- [ ] Enable HTTPS (SSL/TLS certificates)
- [ ] Configure firewall rules
- [ ] Enable API rate limiting
- [ ] Set up DDoS protection (AWS Shield, Cloudflare)

**Infrastructure**:
- [ ] PostgreSQL replication enabled (primary + 2 replicas)
- [ ] Qdrant cluster mode (3+ nodes)
- [ ] Redis Sentinel configured (automatic failover)
- [ ] Load balancer in front (auto-scaling)
- [ ] CDN for static assets (CloudFront, Cloudflare)

**Monitoring**:
- [ ] Prometheus metrics exported
- [ ] Grafana dashboards configured
- [ ] CloudWatch/Datadog alarms set up
- [ ] Log aggregation (ELK, DataDog)
- [ ] Uptime monitoring (StatusPage)

**Backup & Recovery**:
- [ ] PostgreSQL automated backups (daily)
- [ ] Qdrant snapshots (daily)
- [ ] Disaster recovery plan tested
- [ ] RTO/RPO targets defined

### Kubernetes Deployment Example

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-backend
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: rag-backend
  template:
    metadata:
      labels:
        app: rag-backend
    spec:
      containers:
      - name: backend
        image: ghcr.io/myorg/rag-backend:v1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: rag-secrets
              key: database-url
        - name: QDRANT_URL
          value: "http://qdrant-cluster:6333"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: rag-backend-service
  namespace: production
spec:
  selector:
    app: rag-backend
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
  type: ClusterIP
```

Deploy:
```bash
kubectl apply -f deployment.yaml
kubectl get pods -n production
```

## Health Checks & Monitoring

### Health Endpoints

```bash
# Backend health
curl http://localhost:8000/health
# {"status":"healthy","uptime_seconds":3600}

# PostgreSQL
docker-compose exec postgres pg_isready -U rag_user

# Qdrant
curl http://localhost:6333/health
# {"status":"ok"}

# Redis
docker-compose exec redis redis-cli ping
# PONG
```

### Key Metrics to Monitor

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| API Response Time (p95) | < 2s | > 5s |
| Database Connection Pool | < 50% | > 80% |
| Qdrant Indexing Time | < 500ms | > 1000ms |
| Error Rate | < 0.1% | > 1% |
| Cache Hit Rate | > 80% | < 50% |
| Vector Search Latency | < 100ms | > 500ms |

### Alerting Rules (Prometheus)

```yaml
groups:
- name: rag_alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
    for: 5m
    annotations:
      summary: "High error rate on {{ $labels.instance }}"

  - alert: SlowAPI
    expr: histogram_quantile(0.95, api_request_duration_seconds) > 5
    for: 5m
    annotations:
      summary: "API p95 latency > 5s"

  - alert: QdrantIndexLag
    expr: qdrant_points_indexed < qdrant_points_total
    for: 10m
    annotations:
      summary: "Qdrant indexing lag detected"
```

## Rollback Procedures

### If Deployment Fails

```bash
# 1. Check service status
docker-compose ps

# 2. View logs
docker-compose logs backend
docker-compose logs postgres

# 3. Restart failed service
docker-compose restart backend

# 4. Full rollback (restart all)
docker-compose down
docker-compose up

# 5. Verify health
curl http://localhost/health
```

### If Database Migration Fails

```bash
# 1. Restore from backup
pg_restore -d rag_db /backup/rag_db_backup.dump

# 2. Restart backend
docker-compose restart backend

# 3. Test recovery
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### If Qdrant Collection Corrupts

```bash
# 1. Create new snapshot
curl -X POST http://localhost:6333/snapshots

# 2. Restore from previous snapshot
curl -X POST http://localhost:6333/snapshots/recover \
  -H "Content-Type: application/json" \
  -d '{"snapshot_name":"snapshot_xxx"}'

# 3. Verify collection
curl http://localhost:6333/collections
```

## Performance Tuning

### PostgreSQL

```sql
-- Increase shared_buffers (25% of RAM)
shared_buffers = 4GB

-- Increase effective_cache_size (50-75% of RAM)
effective_cache_size = 12GB

-- Enable parallel queries
max_parallel_workers = 4

-- Increase connection pool
max_connections = 200
```

### Qdrant

```yaml
# Increase optimization threads
performance:
  max_optimization_threads: 4

# Increase batch size
  max_search_batch_size: 200

# Increase WAL capacity
storage:
  wal:
    wal_capacity_mb: 500
```

### Redis

```bash
# Increase memory
maxmemory 2gb
maxmemory-policy allkeys-lru

# Enable persistence
save 900 1
save 300 10
save 60 10000
```

## Cleanup & Maintenance

### Daily

```bash
# Backup
docker-compose exec postgres pg_dump rag_db > backup_$(date +%Y%m%d).sql

# Check disk usage
docker system df

# Monitor logs
docker-compose logs backend --tail 100
```

### Weekly

```bash
# Prune unused Docker artifacts
docker system prune -a

# Vacuum PostgreSQL
docker-compose exec postgres vacuumdb -U rag_user rag_db

# Reindex Qdrant
curl -X POST http://localhost:6333/collections/documents_fixed/optimize
```

### Monthly

```bash
# Full database backup
docker-compose exec postgres pg_dump -Fc rag_db > backup_$(date +%Y%m%d_%H%M%S).dump

# Snapshot Qdrant
curl -X POST http://localhost:6333/snapshots

# Review and update dependencies
docker-compose pull
docker-compose up -d
```

## Troubleshooting

### "Database connection timeout"
```bash
# Check PostgreSQL is healthy
docker-compose exec postgres pg_isready -U rag_user

# Check connection pool
docker-compose exec postgres psql -U rag_user -c "SELECT count(*) FROM pg_stat_activity;"

# Restart postgres
docker-compose restart postgres
```

### "Qdrant collection not found"
```bash
# Create collection
curl -X POST http://localhost:6333/collections \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "documents_fixed",
    "vectors": {
      "size": 1536,
      "distance": "Cosine"
    }
  }'
```

### "Redis connection refused"
```bash
# Check Redis is running
docker-compose ps redis

# Check Redis memory
docker-compose exec redis redis-cli INFO memory

# Clear expired keys
docker-compose exec redis redis-cli FLUSHDB
```

### "Out of memory"
```bash
# Check container limits
docker-compose exec backend free -h

# Increase Docker memory limit
# Edit docker-compose.yml: deploy.resources.limits.memory

# Or increase system swap
```

## Support

- **Logs**: `docker-compose logs [service]`
- **Metrics**: Prometheus at `http://localhost:9090`
- **Tracing**: Jaeger at `http://localhost:16686`
- **Team**: Slack #rag-infrastructure channel
