# Survival Analysis

This chapter builds the full survival analysis pipeline from first principles: constructing survival and hazard functions from raw frequency data, handling right-censored observations via Kaplan-Meier estimation, correcting for stratified sampling with a weighted bootstrap, and computing conditional remaining-lifetime distributions. The code patterns — complementing a CDF to get a survival curve, dividing a PMF by an at-risk count to get hazard probabilities, taking a cumulative product of complementary hazards to recover a survival function — are direct implementations of the underlying probability calculus, not black-box calls.

## Exercise: Divorce Survival Analysis by Marriage Cohort

The exercise constructs a survival function for marriage duration, where the "event" is divorce. Two populations must be separated before calling `estimate_hazard`: *complete* cases (respondents whose first marriage ended in a divorce recorded in the data) and *ongoing* cases (respondents still in their first marriage at the time of interview).

For complete cases, the duration is $(\texttt{cmdivorcx} - \texttt{cmmarrhx}) / 12$, converting century-months to years. No censoring applies here — the event was observed. The `dropna` behaviour inside `estimate_hazard` is therefore critical: rows where `cmdivorcx` is `NaN` (marriages that did not end in divorce) must not leak into the complete sequence. In the raw data both divorced and still-married respondents are present, so simply subtracting columns without filtering would silently pollute the complete set with `NaN`-difference rows that `FreqTab.from_seq` would then ignore — harmless only because pandas drops `NaN` from value counts, but fragile if the implementation changed.

For ongoing cases the selection `fmarno == 1 and rmarital == 1` isolates respondents who have married exactly once and are currently married. Their duration is time-from-marriage to interview, which is a right-censored observation: all we know is that the divorce (if it ever occurs) must happen after this duration. Kaplan-Meier uses these observations by adding them to the at-risk denominator at every age up to their censoring time without incrementing the event numerator — formally,

$$\hat{h}(t) = \frac{d_t}{n_t}$$

where $d_t$ is the number of divorces at duration $t$ and $n_t$ is the number of marriages still intact and under observation just before $t$, including both the censored ongoing marriages and those that later divorced.

The cumulative hazard $\sum_t \hat{h}(t)$ is steepest in roughly years 2–10, identifying the window of highest divorce risk. The survival curve flattens near 0.5, which is consistent with the often-quoted "50% of marriages end in divorce" figure — but note that this estimate is population-averaged across all cohorts and conditioning on marriage occurring at all; the optional cohort breakdown reveals that the 1940s cohort has markedly lower divorce rates than later cohorts, so the aggregate statistic conceals substantial generational heterogeneity. A hidden assumption throughout is that the censoring mechanism is non-informative: respondents who happen to be surveyed early in their marriage are not systematically different from those surveyed later, which is plausible given the survey design but worth acknowledging.

## Exercise: Historical Swedish Mortality and the Infant-Mortality Paradox

This exercise converts a digitised hazard function — age-specific mortality rates from an 1800s Swedish birth cohort — into a full lifetime distribution and then computes conditional remaining life expectancy at every age.

The `make_hazard` function performs two non-obvious operations. First, it uses `scipy.interpolate.interp1d` to fill in integer ages between the sparse digitised data points; the `fill_value="extrapolate"` flag extends the fit linearly beyond the observed range, which is a strong assumption at extreme ages where mortality curves are poorly characterised. Second, it applies `np.exp` to the interpolated values. This implies the original data was stored on a log scale — a common practice because log-mortality is approximately linear in age (the Gompertz law: $\log h(t) \approx a + bt$), making interpolation in log-space more numerically stable than in probability space.

The survival function is recovered via the Kaplan-Meier product formula implemented in `make_surv`:

$$S(t) = \prod_{s \leq t} (1 - h(s))$$

This is the discrete-time analogue of $S(t) = \exp\!\left(-\int_0^t h(s)\,ds\right)$. Because the hazard values come from a model rather than empirical event counts, there is no sampling uncertainty in this step; the uncertainty all lives in the digitisation error and interpolation choices.

`make_cdf` gives $F(t) = 1 - S(t)$, and `make_pmf` converts this to the probability mass $P(T = t) = F(t) - F(t-1)$, which is the lifetime distribution treated as discrete in one-year bins.

The remaining-lifetime calculation at age $t$ conditions on survival to $t$: it selects the tail $\{s \geq t\}$ of the lifetime PMF, shifts the time axis to zero, renormalises, and takes the mean. The key insight is that renormalisation is mandatory — the selected tail probabilities do not sum to 1 because they are unconditional; dividing by their sum implements Bayes' rule, converting $P(T = s)$ into $P(T = s \mid T \geq t)$.

The counterintuitive rise in remaining life expectancy during the first few years of life is a direct consequence of the selection effect of surviving infant mortality. Formally, $E[T - t \mid T \geq t]$ can increase in $t$ whenever the hazard decreases sharply — a survivor of the high-mortality infant years faces a suddenly lower hazard going forward, more than compensating for the time already consumed. This is the discrete analogue of the inspection paradox and is a clean example of how conditioning on survival changes the effective distribution an analyst is working with.
