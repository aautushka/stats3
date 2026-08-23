I now have all the content I need. Let me write the commentary.

# Exploratory Data Analysis

These exercises ground the chapter's data-wrangling workflow in concrete practice. The central pattern — load a dataset, validate each column against an external codebook, clean or recode anomalies, derive new columns, and filter to subsets of interest — recurs throughout the book. The code makes three statistical ideas tangible: (1) frequency tables as the first sanity check on categorical data; (2) linear unit conversion and what it does (and does not) preserve about a distribution's shape; and (3) row selection by logical predicate as the computational stand-in for conditioning on an event in probability.

## Exercise: Validating Birth-Order Frequencies Against the Codebook

`value_counts()` counts distinct values in a Series and returns a new Series indexed by those values. By default the result is sorted by count descending, so `.sort_index()` re-orders it by the actual birth-order integer — making comparison with the codebook table (which lists values 1 through 10 in order) straightforward.

The deeper statistical point is why this comparison matters. The NSFG pregnancy file contains 13,593 rows, but `birthord` is only populated for live births — all other outcomes (miscarriages, stillbirths, abortions) have a missing value (`NaN`) in this field. `value_counts()` silently drops `NaN` by default, so the row counts shown (4413, 2874, …) apply only to the live-birth subset. Comparing those counts to published CDC totals is a form of **data validation**: if the numbers match, it confirms that the column was read correctly, that the encoding is as documented, and that no rows were silently dropped during loading. A mismatch would signal a parsing error or a version mismatch in the data file — both serious enough to invalidate any downstream analysis. This kind of cross-check against an authoritative codebook is essential any time you work with survey microdata, where the raw encoding is rarely self-explanatory.

Note also that birth order follows a naturally declining pattern (more first births than second, more second than third, etc.) which is a sanity check in itself: a dataset showing more third births than first would be immediately suspicious.

## Exercise: Unit Conversion, Mean, and Standard Deviation of Birth Weight

The solution divides `totalwgt_lb` by 2.2 element-wise — a **linear transformation** $y = x / c$. Linear transforms have a precise effect on summary statistics:

$$\mu_y = \mu_x / c, \qquad \sigma_y = \sigma_x / c$$

So the mean and standard deviation both scale by the same factor $1/c = 1/2.2 \approx 0.4545$. The **shape** of the distribution is unchanged — skewness and kurtosis are unaffected — so any conclusion you draw about, say, whether the distribution is symmetric will hold equally in pounds or kilograms.

The pandas `.std()` method computes the **sample standard deviation** using Bessel's correction:

$$s = \sqrt{\frac{1}{n-1} \sum_{i=1}^{n}(x_i - \bar{x})^2}$$

This divides by $n - 1$ rather than $n$, making it an unbiased estimator of the population variance. NumPy's `np.std()` divides by $n$ (the biased MLE estimator) by default, so the two functions give slightly different answers on the same data — an easy source of confusion. For large datasets like the NSFG the difference is negligible, but it matters for small samples.

The `PerformanceWarning` in the output ("DataFrame is highly fragmented") is a consequence of adding one column at a time to a large DataFrame across multiple cells. It does not affect correctness, only speed.

## Exercise: Filtering Rows by Respondent ID and Compound Conditions

`preg.query("caseid == 2298")` constructs a **boolean mask** — a Series of `True`/`False` values with the same index as `preg` — and returns only the rows where the condition holds. It is equivalent to `preg[preg["caseid"] == 2298]`, but the string syntax is more readable and avoids repeated typing of the DataFrame name. Conceptually this is **conditioning**: you are restricting the sample space to rows belonging to a single respondent, which is necessary because each respondent can appear multiple times (once per pregnancy).

The output for caseid 2298 shows four pregnancies with lengths 40, 36, 30, 40 weeks. The 30-week entry is notably short — likely a preterm birth or a pregnancy that ended before term. The mixed lengths within one respondent illustrate that `prglngth` varies substantially even within a person's reproductive history.

The second part adds a compound condition: `"caseid == 5013 and birthord == 1"`. The `and` keyword inside the query string is evaluated as a row-wise logical AND (not Python's short-circuit `and`), selecting only the row where both conditions are simultaneously true. Looking at all four rows for caseid 5013 first reveals that row 5517 has a `NaN` birth weight — `birthord` for that pregnancy must be missing, meaning it was not a live birth. The compound query cleanly isolates the single first-born live birth (row 5516, 7.375 lb) without needing to inspect the intermediate output. This pattern — progressively narrowing a dataset with chained conditions — is the workhorse operation of exploratory data analysis.
