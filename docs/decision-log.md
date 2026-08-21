# Decision Log

An entry gets appended whenever a choice is made that could have gone another way,
including the option not taken and why. See the change protocol in `CLAUDE.md`. This log
is a deliverable, not internal notes.

## 2026-08-21 Dependency management: requirements.txt over pyproject.toml/poetry

**Decision:** Pin the project's Python dependencies in a plain `requirements.txt`,
installed with `pip install -r requirements.txt`.

**Alternative considered:** A `pyproject.toml` managed by Poetry or a similar tool.

**Why:** This project is a build script, not a distributed package, so there is nothing to
publish and no need for a build backend or lockfile tooling. `requirements.txt` is the
smallest thing that lets a clean clone reproduce the environment, which is the actual
requirement in section 7 of `PROJECT_BRIEF.md`.

## 2026-08-21 Fitting library: statsmodels over scikit-learn

**Decision:** Use statsmodels for the quota-to-premium fits in section 4.1 of
`PROJECT_BRIEF.md`.

**Alternative considered:** scikit-learn.

**Why:** The fits are reduced-form OLS specifications (log-log, with a lagged premium term
and a time trend under consideration), and section 6 requires perturbing the fitted
coefficients across their confidence intervals for the sensitivity sweep. statsmodels
exposes coefficient standard errors, confidence intervals and residual diagnostics
directly. scikit-learn does not expose these without extra work, and installing a second
library just for inference would push past the dependency ceiling in section 7 of
`PROJECT_BRIEF.md` ("pymoo, numpy, pandas, a fitting library and Plotly").
