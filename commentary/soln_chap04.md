Now I have all five exercises. Let me write the commentary.

# Cumulative Distribution Functions

These exercises build practical fluency with the empirical CDF as a tool for probability queries. The central pattern — construct a `Cdf` from data, evaluate it to get probabilities, invert it to get quantiles — reappears in every exercise, and collectively they demonstrate that a CDF encodes the entire distribution: it answers questions about individual values (percentile ranks), intervals (probability mass between two thresholds), location (median), spread (IQR), and shape (quartile skewness). Where PMFs and histograms require binning choices that can mislead, the empirical CDF is exact and displays every observation without distortion.

## Exercise: Birth Weight Percentile Rank

`Cdf.from_seq` constructs the empirical CDF by sorting the data and assigning to each value $x$ the fraction of observations $\leq x$:

$$F_n(x) = \frac{1}{n}\sum_{i=1}^{n} \mathbf{1}[x_i \leq x]$$

This is the empirical counterpart of the population CDF $F(x) = P(X \leq x)$. Evaluating the CDF at a point — `live_cdf(8.5)` — directly returns the percentile rank as a proportion (multiply by 100 to get a percentage). No binning, no kernel smoothing, no parametric assumption: the empirical CDF is a non-parametric estimate of the true CDF, and by the Glivenko-Cantelli theorem it converges uniformly to $F$ as $n \to \infty$.

The solution builds three separate CDFs (all live births, first babies, others) and queries each at the same weight. This reveals something important: the correct reference population matters. Using the wrong group — say, comparing a first baby's weight to the "others" distribution — would yield a misleading percentile rank, because first babies tend to weigh slightly less. The hidden assumption throughout is that the NSFG sample is representative of the population of interest; percentile ranks are meaningless if the reference distribution is not the right one.

## Exercise: Comparing Male and Female Birth Weight Distributions

This exercise introduces two operations: plotting overlaid CDFs for visual comparison, and using `Cdf.inverse` to perform a quantile-matching query across groups.

When two CDFs are plotted together, vertical separation at any value $x$ equals the difference in proportions below $x$ — a direct, distortion-free view of distributional shift. If one CDF lies entirely to the right of another (stochastic dominance), every percentile of the first group exceeds the corresponding percentile of the second. In practice the curves cross or run nearly parallel, indicating a location shift with similar shape.

`cdf_birth_weight_female.inverse(percentile_rank / 100)` inverts the empirical CDF: given a probability $p$, it returns the quantile $Q(p) = \inf\{x : F(x) \geq p\}$. This is the generalised inverse (quantile function). The chain — compute percentile rank from the male CDF at 8.5 lb, then feed that rank into the female quantile function — answers "what female weight sits at the same relative position in its distribution as 8.5 lb does in the male distribution?" It is a form of distributional standardisation that does not require normality, only the assumption that both distributions are measured on the same scale with comparable units.

## Exercise: Interval Probability from CDF Subtraction

The key insight here is the additivity property of the CDF: for any $a < b$,

$$P(a < X \leq b) = F(b) - F(a)$$

This follows directly from the definition of $F$. The solution computes `cdf_ages(20)` and `cdf_ages(30)` separately and subtracts them, giving the fraction of pregnancies with conception age strictly above 20 and at most 30.

A subtlety worth noting: the empirical CDF is right-continuous, so `cdf(20)` includes exactly age 20. The subtraction therefore gives $P(20 < X \leq 30)$, not $P(20 \leq X \leq 30)$. Whether this distinction matters depends on whether the data are truly continuous (ages might be recorded as discrete years or fractional years). The `agepreg` column in the NSFG is stored in hundredths of a year, so many exact ties are possible and the distinction is non-trivial. This is the kind of boundary condition that the CDF formalism forces you to confront explicitly, which is one of its pedagogical advantages over summary statistics.

## Exercise: Quartile-Based Summary Statistics for Running Speeds

The three functions — `median`, `iqr`, `quartile_skewness` — all extract information from the CDF via quantiles, demonstrating that the quantile function $Q(p)$ is as information-complete as the CDF itself.

The **median** is $Q(0.5)$, the value splitting the distribution in half. Unlike the mean, it is resistant to outliers, which matters here because race finishing times have a long right tail.

The **IQR** (interquartile range) is $Q(0.75) - Q(0.25)$, a spread measure that excludes the outer 50% of the distribution and is similarly resistant to extremes.

**Quartile skewness** (Bowley's coefficient) is:

$$\text{QS} = \frac{Q(0.75) - 2\,Q(0.5) + Q(0.25)}{Q(0.75) - Q(0.25)}$$

It measures whether the median sits closer to $Q_1$ or $Q_3$. When $\text{QS} > 0$ the upper half of the middle 50% is stretched relative to the lower half — a right skew. For these race speeds the result is approximately $+0.13$, confirming modest right skew: there is a longer tail of slow runners than fast runners, which makes physical sense because there is a hard floor on how fast a person can run but no comparable ceiling on how slow.

All three statistics assume nothing about the shape of the distribution and are computed directly from the empirical CDF.

## Exercise: Verifying Uniformity of a Pseudo-Random Generator

For a true Uniform$(0, 1)$ random variable, the CDF is $F(x) = x$ for $x \in [0,1]$ — a straight line with slope 1. The empirical CDF of a large sample from `np.random.random` should therefore look like a diagonal line.

What you actually see is a staircase that hugs the diagonal closely. The deviations from perfect linearity are finite-sample noise: by the Kolmogorov-Smirnov (KS) statistic, the maximum deviation between $F_n$ and $F$ is $O(n^{-1/2})$, so with $n = 1001$ you expect random wiggles of order $\pm 0.03$. Visually, the CDF plot is an informal KS test — you are asking whether the staircase stays within the expected noise envelope around the diagonal.

This exercise embeds a critical habit of mind: using the CDF to check a model assumption (uniformity) non-parametrically. The same technique generalises: plot the empirical CDF against any theoretical CDF and deviations reveal where the model fails. The hidden assumption is that successive outputs of `np.random.random` are independent; dependence would not necessarily appear in the CDF plot but would show up in lag-correlation plots or runs tests.
