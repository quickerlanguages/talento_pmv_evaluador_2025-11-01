#!/usr/bin/env bash
set -euo pipefail

# --- Inputs con defaults coherentes ---
DIST_NAME="${DIST_NAME:-talento_pmv_evaluador_2025-11-01}"
ZIP="${ZIP:-${DIST_NAME}.clean.zip}"
TAG="${CUSTOM_TAG:-rel/${DIST_NAME}}"

[[ -n "$TAG" ]] || { echo "✖ TAG vacío"; exit 1; }
command -v gh >/dev/null 2>&1 || { echo "✖ Falta la CLI de GitHub (brew install gh)"; exit 1; }

# --- Artefactos ya generados por 'dist' ---
[[ -f "../${ZIP}" ]] || { echo "✖ Falta ../${ZIP} (ejecuta: make dist)"; exit 1; }
[[ -f "../SHA256SUMS.txt" ]] || { echo "✖ Falta ../SHA256SUMS.txt (ejecuta: make dist)"; exit 1; }

ZIP_SHA="$(awk '{print $1}' ../SHA256SUMS.txt)"
TS="$(date +%Y-%m-%d_%H%M%S)"
NOTES="$(mktemp -t talento_notesXXXXXX)"

echo "→ usando tag: ${TAG}"

# 1) Tag local idempotente
if git show-ref --tags --verify --quiet "refs/tags/${TAG}"; then
  echo "→ tag ${TAG} ya existe localmente"
else
  echo "→ creando tag ${TAG}"
  git tag -a "${TAG}" -m "Release ${DIST_NAME} (zip SHA256=${ZIP_SHA})"
fi

# 2) Push
git push || true
git push --tags || true

# 3) Notas
{
  echo "# Talento PMV Evaluador — ${DIST_NAME}"
  echo
  echo "- Tag: ${TAG}"
  echo "- SHA256: ${ZIP_SHA}"
  echo "- Build time: ${TS}"
  echo "- Artefacto ZIP: ${ZIP}"
  echo
  echo "## Verificación local"
  echo "\`shasum -a 256 -c SHA256SUMS.txt\` → OK"
} > "${NOTES}"

# 4) Release en GitHub
echo "→ Publicando release en GitHub…"
if gh release view "${TAG}" >/dev/null 2>&1; then
  echo "→ release existe; actualizando assets y notas"
  gh release upload "${TAG}" "../${ZIP}" "../SHA256SUMS.txt" --clobber
  gh release edit "${TAG}" --notes-file "${NOTES}" --title "Talento PMV Evaluador ${DIST_NAME}"
else
  gh release create "${TAG}" "../${ZIP}" "../SHA256SUMS.txt" \
    --title "Talento PMV Evaluador ${DIST_NAME}" \
    --notes-file "${NOTES}" --verify-tag
fi

echo "✔ Release publicado/actualizado en GitHub"
rm -f "${NOTES}" || true