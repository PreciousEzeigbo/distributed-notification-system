# CONTRIBUTING.md

## How to Contribute to the Notification System

This guide helps team members contribute code without breaking the system.

---

## 📋 Quick Rules

1. **Use snake_case** for all variables, functions, routes, database columns
2. **Follow the standard response format** (see PROJECT_CHARTER.md)
3. **Test locally** before pushing (`docker-compose up`)
4. **Write tests** for new features (70% coverage minimum)
5. **Update docs** if you change APIs

---

## 🔄 Workflow

### 1. Before Starting

```bash
# Pull latest changes
git pull origin main

# Create feature branch
git checkout -b feat/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Making Changes

**Branch Naming:**

- `feat/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation only
- `test/` - Adding tests

**Examples:**

- `feat/add-sms-service`
- `fix/rate-limit-bug`
- `docs/update-api-examples`
- `test/add-user-service-tests`

### 3. Coding Standards

**Use snake_case everywhere:**

```python
# ✅ GOOD
def send_notification(user_id: str, template_code: str):
    notification_type = "email"
    return {"notification_id": "123"}

# ❌ BAD
def sendNotification(userId: str, templateCode: str):
    notificationType = "email"
    return {"notificationId": "123"}
```

**Follow response format:**

```python
# ✅ GOOD
return {
    "success": True,
    "message": "User created",
    "data": {"user_id": user.id},
    "meta": {"timestamp": "...", "correlation_id": "..."}
}

# ❌ BAD
return {"id": user.id, "status": "ok"}
```

### 4. Testing Locally

```bash
# Build and run all services
docker-compose up --build

# Check health endpoints
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health

# Run tests
cd api-gateway && pytest
cd user-service && pytest
cd template-service && pytest

# View logs
docker-compose logs -f api-gateway
docker-compose logs -f email-service
```

### 5. Committing Changes

**Commit Message Format:**

```
<type>: <short description>

<optional longer description>
```

**Types:**

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `test:` - Tests
- `refactor:` - Code refactoring
- `style:` - Formatting, no code change

**Examples:**

```bash
git commit -m "feat: add SMS notification support"
git commit -m "fix: resolve rate limiting Redis connection issue"
git commit -m "docs: update API_TESTING.md with new endpoints"
git commit -m "test: add unit tests for template rendering"
```

### 6. Pushing Changes

```bash
# Push your branch
git push origin feat/your-feature-name

# Create Pull Request on GitHub
# - Clear title describing the change
# - Description with what changed and why
# - Link to any related issues
# - Screenshots if UI changes
```

---

## 🚫 What NOT to Commit

Never commit these files:

- `.env` - Contains secrets
- `__pycache__/` - Python cache
- `*.pyc` - Compiled Python
- `node_modules/` - Node dependencies
- `.venv/` - Virtual environment
- Database files (`.db`, dumps)
- Log files (`.log`)
- IDE configs (`.vscode/`, `.idea/`)

They're already in `.gitignore` but double-check before committing!

---

## 📝 Pull Request Checklist

Before creating a PR, make sure:

- [ ] Code uses `snake_case` naming
- [ ] All responses follow standard format
- [ ] Tests pass locally (`pytest`)
- [ ] Services start successfully (`docker-compose up`)
- [ ] Health checks return 200
- [ ] No `.env` or secrets committed
- [ ] Documentation updated (if API changed)
- [ ] Commit messages are clear
- [ ] Code is reviewed by yourself first

---

## 🔧 Changing APIs or Message Formats

If you need to change an endpoint or RabbitMQ message format:

1. **Update PROJECT_CHARTER.md** - Document the new format
2. **Notify team** - Post in group chat about the change
3. **Update all affected services** - Don't break existing code
4. **Test end-to-end** - Register user → send notification → check delivery
5. **Update API_TESTING.md** - Add curl examples

**Example:**

```bash
# Before: POST /notifications/
# After: POST /api/v1/notifications/

# 1. Update routes in api-gateway
# 2. Update workers (email-service, push-service)
# 3. Update PROJECT_CHARTER.md
# 4. Test everything
# 5. Open PR with migration notes
```

---

## 🐛 Reporting Issues

Found a bug? Create a GitHub Issue:

**Template:**

```markdown
## Bug Description

Clear description of the bug

## Steps to Reproduce

1. Start services with `docker-compose up`
2. Register user at POST /users/
3. Send notification at POST /notifications/
4. See error...

## Expected Behavior

What should happen

## Actual Behavior

What actually happens

## Logs
```

Paste relevant logs from `docker-compose logs`

```

## Environment
- OS: Ubuntu 22.04
- Docker version: 24.0.6
- Python version: 3.11
```

---

## 🏗️ Adding a New Service

If you need to add a new service (e.g., SMS Service):

1. **Create directory:** `sms-service/`
2. **Add to docker-compose.yml:**

```yaml
sms-service:
  build: ./sms-service
  ports:
    - "8003:8000"
  environment:
    - DATABASE_URL=postgresql://...
    - REDIS_URL=redis://redis:6380
  depends_on:
    - redis
    - rabbitmq
```

3. **Create Dockerfile** in `sms-service/`
4. **Implement `/health` endpoint**
5. **Follow standard response format**
6. **Add tests**
7. **Update PROJECT_CHARTER.md**
8. **Update README.md**

---

## 📚 Code Review Guidelines

When reviewing PRs:

**Check for:**

- [ ] `snake_case` naming used everywhere
- [ ] Standard response format followed
- [ ] Tests included (70%+ coverage)
- [ ] No hardcoded secrets
- [ ] Clear commit messages
- [ ] Documentation updated
- [ ] Services start successfully
- [ ] Health checks pass

**Be constructive:**

- ✅ "Consider using snake_case for this variable name"
- ✅ "Could you add a test for this edge case?"
- ✅ "Great work! Just need to update the docs"
- ❌ "This is wrong, rewrite it"

---

## 🚀 Deployment (CI/CD)

We use GitHub Actions for CI/CD:

1. **On Push** - Runs tests, checks formatting
2. **On PR** - Runs full test suite, builds Docker images
3. **On Merge to main** - Deploys to server (after approval)

**CI Workflow checks:**

- Linting (flake8, pylint)
- Unit tests (pytest)
- Integration tests (docker-compose)
- Build Docker images
- Check for secrets

---

## 💡 Tips for Success

### For API Gateway

- Always validate JWT tokens
- Check idempotency keys
- Log every request with correlation ID
- Handle RabbitMQ connection failures

### For User Service

- Hash passwords with bcrypt
- Validate email format
- Generate secure JWT tokens
- Store preferences correctly

### For Template Service

- Validate template variables
- Support multiple languages
- Keep version history
- Cache rendered templates

### For Workers (Email/Push)

- Implement circuit breaker
- Use exponential backoff for retries
- Send failures to DLQ
- Update status in API Gateway

---

## 🤝 Getting Help

**Stuck? Ask for help:**

- GitHub Issues - Technical problems
- Team Chat - Quick questions
- Code Review - Ask team members

**Good questions include:**

- What you're trying to do
- What you've already tried
- Error messages / logs
- Code snippets

---

## ✅ Checklist for First Contribution

For new team members:

- [ ] Clone repository
- [ ] Copy `.env.example` to `.env`
- [ ] Run `docker-compose up`
- [ ] Check all health endpoints
- [ ] Read PROJECT_CHARTER.md
- [ ] Read API_TESTING.md
- [ ] Create test branch
- [ ] Make small change
- [ ] Test locally
- [ ] Commit and push
- [ ] Create PR
- [ ] Get code review
- [ ] Merge!

---

**Questions?** Ask in the team chat or create a GitHub Issue.

**Document Version:** 1.0  
**Last Updated:** November 10, 2025  
**Team:** Group 21
