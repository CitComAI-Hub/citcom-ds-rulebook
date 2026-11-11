#!/usr/bin/env bash
# Runs the policy-class tests against the Rego that odrl-pap generates.
# Local only: starts throwaway odrl-pap + postgres containers, builds each
# provider's bundle (tests/opa/build.py) and runs `opa test` on it.
# Versions = the ones deployed by dataspace-on-upv (modules/dsc_v10, chart 10.0.0).
set -euo pipefail
PAP_IMAGE=${PAP_IMAGE:-quay.io/fiware/odrl-pap:1.4.10}
OPA_IMAGE=${OPA_IMAGE:-openpolicyagent/opa:1.11.0}
PORT=${PORT:-18080}
cd "$(dirname "$0")/../.."
OUT=tests/opa/out

cleanup() { docker rm -f rb-pap rb-pg >/dev/null 2>&1 || true; docker network rm rb-opa-test >/dev/null 2>&1 || true; }
trap cleanup EXIT
cleanup
docker network create rb-opa-test >/dev/null
docker run -d --name rb-pg --network rb-opa-test -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=pap postgres:16-alpine >/dev/null
until docker exec rb-pg pg_isready -U postgres -d pap >/dev/null 2>&1; do sleep 1; done
# GENERAL_ORGANIZATION_DID as in the connectors: vc:role matches roles with this target.
docker run -d --name rb-pap --network rb-opa-test -p "127.0.0.1:$PORT:8080" \
  -e QUARKUS_DATASOURCE_JDBC_URL=jdbc:postgresql://rb-pg:5432/pap \
  -e GENERAL_ORGANIZATION_DID=roles-dataspace "$PAP_IMAGE" >/dev/null
for _ in $(seq 60); do curl -sf "localhost:$PORT/policy" >/dev/null && break; sleep 1; done

python3 -m tests.opa.build --pap "http://localhost:$PORT" --out "$OUT"
rc=0
for dir in "$OUT"/*/; do
  echo "== $(basename "$dir")"
  docker run --rm -v "$PWD/$dir:/b:ro" "$OPA_IMAGE" test /b ${VERBOSE:+-v} || rc=1
done
exit $rc
