#!/bin/bash
# Delete all history on GitHub and rebuild with one-by-one commits.
# Run from project root. Then: git push --force origin master

set -e
cd "$(dirname "$0")"

echo "=== Creating fresh branch with NO history ==="
git branch -D fresh 2>/dev/null || true
git checkout --orphan fresh
git reset

echo ""
echo "=== Committing files ONE BY ONE ==="

commit() {
  local msg="$1"
  shift
  git add "$@"
  git commit -m "$msg"
}

# 1
commit "Add .gitignore" .gitignore

# 2
commit "Add .dockerignore" .dockerignore

# 3
commit "Add GitHub workflows" .github/

# 4
commit "Add Dockerfile" Dockerfile

# 5
commit "Add docker-compose" docker-compose.yml docker-compose.dev.yml

# 6
commit "Add deploy script and pytest config" deploy_minimal.sh pytest.ini

# 7
commit "Add requirements.txt" requirements.txt

# 8
commit "Add verification checklist" VERIFICATION_CHECKLIST.md

# 9
commit "Add config" config/

# 10
commit "Add data preprocessor" src/data/

# 11
commit "Add utils" src/utils/

# 12
commit "Add API" src/api/

# 13
commit "Add compliance" src/compliance/

# 14
commit "Add MLOps" src/mlops/

# 15
commit "Add services" src/services/

# 16
commit "Add visualization" src/visualization/

# 17
commit "Add main pipeline" src/main.py

# 18
commit "Add MERN backend" mern-backend/

# 19
commit "Add dashboards" dashboards/

# 20
commit "Add dbt" dbt/

# 21
commit "Add Databricks notebooks" databricks/

# 22
commit "Add scripts" scripts/

# 23
commit "Add docs" docs/

# 24
commit "Add BI exports" bi_exports/

# 25
commit "Add tests" tests/

# 26
commit "Add Kubernetes configs" k8s/

# 27
commit "Add Terraform" terraform/

# 28
commit "Add monitoring" monitoring/

# 29
commit "Add reports" reports/

# 30
commit "Add output figures" output_final_all_figures/

# 31
commit "Add README" README.md

# 32 (optional - add this script)
test -f commit_one_by_one.sh && commit "Add commit script" commit_one_by_one.sh

# Replace master with this fresh history
echo ""
echo "=== Replacing master branch ==="
git branch -D master 2>/dev/null || true
git branch -m master

echo ""
echo "=== Done. 31 commits, one by one. ==="
echo "Run: git push --force origin master"
git log --oneline
