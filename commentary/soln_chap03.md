Now I have everything I need. Let me write the commentary.

# Probability Mass Functions

This chapter's exercises use the National Survey of Family Growth (NSFG) respondent file to practice constructing and interpreting Probability Mass Functions for discrete count data. The core coding pattern — build a `FreqTab`, clean sentinel values, convert to a `Pmf`, and then summarize or transform it — is repeated across all three exercises and embodies the fundamental move from raw counts to a normalized probability measure. The exercises also develop three distinct but related ideas: recognizing when coded non-responses corrupt summary statistics, quantifying distributional asymmetry through the standardized third central moment, and understanding how the act of sampling can itself distort a distribution.

## Exercise: Constructing a PMF for Live Births and Identifying Special Codes

`FreqTab.from_seq` performs a simple frequency count: it groups identical values and records how many times each appears. This is the unnormalized form of a distribution — a map from each observed value to its raw count. Inspecting the `FreqTab` against the codebook reveals value 97, which is a sentinel code meaning "not ascertained" in NSFG documentation. Leaving 97 in place would silently corrupt every moment computed from the data: the mean would be inflated by nearly 100 for those rows, and variance and skewness would be dominated by this artifact rather than reflecting actual birth counts.

Replacing 97 with `np.nan` is the correct fix because pandas and empiricaldist both propagate `NaN` as a missing value, excluding it automatically from `mean()`, `std()`, and probability normalization. `Pmf.from_seq` then divides each remaining frequency by the total count of non-missing observations, converting the `FreqTab` into a proper probability distribution where all probabilities sum to 1.

The resulting bar chart shows right skew: the distribution has a hard lower bound at 0 (a respondent cannot have fewer than zero live births), but no corresponding upper bound compresses the right tail. Most mass sits at 0–2, with a rapidly thinning right tail extending to 22. This is the structural signature of non-negative count data — the left is truncated by a floor and the right tail is free to stretch. Right skew is visually confirmed when the tail on the high-value side is longer than the tail on the low-value side.

## Exercise: Computing Skewness from a Sample and from a PMF

Skewness is the third standardized central moment:

$$g_1 = \frac{E\left[(X - \mu)^3\right]}{\sigma^3}$$

Cubing the deviations rather than squaring them is the key design choice. Variance uses squared deviations, which are always non-negative and cannot distinguish left from right asymmetry. Cubing preserves the sign of each deviation: large positive deviations (values well above the mean) contribute a large positive cube, and large negative deviations contribute a large negative cube. A right-skewed distribution has a few very large positive deviations that outweigh many small negative ones, so the numerator is positive and $g_1 > 0$.

The sample computation uses `ddof=0` to compute the biased (population-formula) standard deviation $\hat{\sigma} = \sqrt{\frac{1}{n}\sum(x_i - \bar{x})^2}$, which matches the denominator convention used in the formula above. Using `ddof=1` would give a slightly different value because the sample standard deviation and the skewness formula's denominator would no longer be on the same footing.

The `pmf_skewness` function reexpresses the same computation in terms of the PMF's quantities (`pmf.qs`) and probabilities (`pmf.ps`). Instead of averaging over $n$ observations, it computes the probability-weighted expectation $\sum_k p_k (k - \mu)^3$ and then divides by $\sigma^3$. The two results agree exactly because `Pmf.from_seq` assigns each distinct value a probability of $\text{count}(k)/n$ — so the probability-weighted sum is algebraically identical to the sample average. This equivalence is worth pausing over: the PMF is not an approximation of the sample; it is the sample, re-expressed as a discrete probability measure.

A hidden sensitivity: because deviations are cubed, a single extreme outlier has an outsized effect on skewness. The original value 97 (before replacement with `NaN`) would have produced a skewness statistic several orders of magnitude larger, illustrating why sentinel-value cleaning must precede any moment calculation.

## Exercise: The Class Size Paradox Applied to Family Size

The class size paradox is a general consequence of size-biased sampling. When you sample units that belong to groups, and larger groups contribute more units to the sample, you systematically over-represent large groups. Here the groups are households and the sampled units are the children within them: a household with 4 children contributes 4 potential survey respondents, while a household with 1 child contributes only 1, and a household with 0 children contributes none at all.

The `bias` function implements this analytically. If $P(k)$ is the actual probability that a randomly chosen respondent's household has $k$ children, then the probability a randomly chosen child reports $k$ household members is:

$$P_{\text{biased}}(k) = \frac{k \cdot P(k)}{\sum_j j \cdot P(j)} = \frac{k \cdot P(k)}{E[X]}$$

In code, `pmf.ps * pmf.qs` computes the unnormalized weight $k \cdot P(k)$ for each $k$; dividing by their sum (via `normalize()`) yields the biased probabilities. Notice that $k = 0$ always contributes zero weight, so the 3,563 respondents with no children under 18 vanish entirely from the biased distribution — they are structurally invisible to a child survey.

The means shift from approximately 1.02 (actual) to 2.40 (biased), a factor of roughly 2.4. This is not a sampling error in the statistical sense but a systematic structural effect: any survey methodology that recruits respondents through group membership rather than directly from the population of groups will produce this inflation. The key hidden assumption in the `bias` calculation is that every child in a household is equally likely to be selected — if, for example, only the oldest child were surveyed, the weighting would differ.
