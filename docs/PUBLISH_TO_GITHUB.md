# Publish to GitHub

Recommended repository name:

```text
sc0002-solar-vegetation-repro
```

## 1. Verify before first commit

Windows:

```powershell
.\verify.ps1
```

macOS/Linux:

```bash
./verify.sh
```

Do not publish unless the final line is `ALL PASS`.

## 2. Initialize repository

```bash
git init
git add .
git commit -m "Initial public reproducibility release"
git branch -M main
```

Create an empty GitHub repository, then:

```bash
git remote add origin https://github.com/<OWNER>/sc0002-solar-vegetation-repro.git
git push -u origin main
```

## 3. Confirm GitHub Actions

The workflow under:

```text
.github/workflows/verify-reference.yml
```

should complete successfully after push.

## 4. Optional release tag

After the GitHub Actions run passes:

```bash
git tag -a v1.0.0 -m "SC0002 reproducibility release v1.0.0"
git push origin v1.0.0
```

## 5. Suggested GitHub About metadata

Description:

```text
Reproducible Sentinel-2 case study of post-development spectral vegetation change at SC0002, Kaohsiung, with archived government-data AOI, matched controls, raw GEE exports, RGB review evidence, and offline verification.
```

Topics:

```text
remote-sensing
sentinel-2
google-earth-engine
ndvi
ndmi
solar-pv
reproducible-research
environmental-monitoring
taiwan
geospatial
```

## 6. Citation metadata

Before a formal academic release, add a `CITATION.cff` containing the actual author name(s), ORCID(s), repository URL, and preferred citation. Those fields are intentionally not fabricated by this repository package.
