Now I have all the information needed. Let me write the commentary.

# Distributions

The exercises in this chapter practice building and interrogating empirical frequency tables — the most elementary form of a distribution — using the `FreqTab` class from `empiricaldist`. Each exercise follows the same workflow: construct a `FreqTab` from raw survey data with `from_seq`, visualise the shape with `.bar()`, and then interrogate the tails or compare groups numerically. The key statistical ideas in play are ordinal encoding versus true quantitative measurement, right-skewed count distributions, and Cohen's $d$ as a standardised measure of between-group difference — all grounded in real data from the National Survey of Family Growth (NSFG).

## Exercise: Income Distribution as a Frequency Table

`FreqTab.from_seq(resp.totincr, name="totincr")` scans the column once and records, for each distinct value $v$, its frequency $f(v)$ — the count of rows where the column equals $v$. Internally `FreqTab` is a pandas `Series` whose index holds the unique values and whose data holds the corresponding counts. The `from_seq` constructor is equivalent to calling `pd.Series(data).value_counts().sort_index()`, but the `FreqTab` wrapper adds domain-specific methods (`.bar()`, `.mode()`, callable lookup, etc.).

A critical thing to notice about `totincr` is that its values (1 through 14) are **ordinal codes**, not dollar amounts. The integer labels encode ordered income brackets whose widths are unequal. Treating the codes as if they were quantitative — computing a mean of the code numbers, for example — would be misleading, because the distance between code 1 and code 2 is not the same as the distance between code 13 and code 14 in dollar terms. A frequency table is the right first tool precisely because it sidesteps this pitfall: it shows you how many respondents fall into each labelled category without imposing any arithmetic on the labels. The bar chart's x-axis still uses the numeric codes, so the reader must remember to consult the codebook to translate codes back to income ranges before drawing any substantive conclusions about the income distribution's shape.

## Exercise: Parity Distribution and Outlier Detection

Parity is a count variable — a non-negative integer that can in principle take any value, but where very large values are biologically constrained. Because most respondents have zero, one, or two children, and a diminishing tail has three or more, the distribution is strongly right-skewed: the bulk of probability mass sits at low values and a long, sparse tail extends to the right. This shape is characteristic of many count phenomena and often motivates Poisson or negative-binomial modelling in later analyses.

The `largest(ftab, n=10)` function exploits the fact that a `FreqTab`, as a sorted pandas Series, stores values in ascending order by index. The slice `ftab[-n:]` therefore selects the $n$ highest-valued rows — no sorting step is needed because `from_seq` already sorts by value. The output reveals counts for parity values up to 22. Values of 16 and 22 are suspicious: while biologically possible, they are extremely rare. Before treating them as valid data points, a careful analyst should cross-check against the respondent's age and interview record. Such extreme values are a common source of data entry errors or coding anomalies in large government surveys. Including them unchanged would inflate the sample mean and variance, distorting any subsequent comparison. The decision whether to cap, remove, or leave them is a substantive judgment, not a purely mechanical one.

## Exercise: Parity by Income Group and Cohen's Effect Size

`resp.query("totincr == 14")` uses pandas' query mini-language to return only the rows where `totincr` equals 14 (the highest income bracket). The complementary group (`totincr < 14`) is everyone else. Comparing the sample means directly — approximately 1.08 children for high-income versus 1.25 for lower-income respondents — shows a raw difference of about 0.17 children.

`cohen_effect_size` translates this raw difference into a standardised effect size (Cohen's $d$):

$$d = \frac{\bar{x}_1 - \bar{x}_2}{\sigma_{\text{pooled}}}, \quad \sigma_{\text{pooled}} = \sqrt{\frac{n_1 \sigma_1^2 + n_2 \sigma_2^2}{n_1 + n_2}}$$

The pooled standard deviation weights each group's variance by its sample size, which is appropriate when the two groups have unequal $n$ (as they do here). The result, $d \approx -0.125$, means the high-income group's mean is about one-eighth of a pooled standard deviation lower — roughly four times larger in magnitude than the effect observed for first babies versus others in the main chapter text. By conventional benchmarks (Cohen's $|d| < 0.2$ is "small") this is still a small effect, but not negligible.

The solution's comments flag the crucial confound: `totincr` and `parity` both depend on a respondent's age and cohort. Older women have had more time to accumulate children and may also have reached higher income brackets; younger women may show low parity simply because they are early in their reproductive lives, not because income suppresses fertility. Any causal claim about income and childbearing would require conditioning on age — for example, by comparing women of similar ages across income groups — before the observed difference can be attributed to income itself.
