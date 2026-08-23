Now I have all the information I need to write the commentary. Here it is:

# Estimation

The exercises in this chapter practice the core ideas of statistical estimation: what makes an estimator good (unbiasedness, consistency), how bootstrap resampling constructs a sampling distribution from a single sample, and how the validity of a confidence interval depends on assumptions that the data may or may not satisfy. The recurring code pattern — compute a statistic, resample thousands of times, compute the same statistic on each resample, then read off the spread and quantiles — embodies the plug-in principle: treat your sample as if it were the population, and simulate the act of repeated sampling.

## Exercise: Bootstrap Sampling Distribution of the Standard Deviation

The solution uses `np.std(weights)` without the `ddof` argument, which defaults to dividing by $n$ rather than $n-1$. This computes the biased (population-formula) standard deviation — a deliberate choice that will resurface in Exercise 8.4.

The bootstrap works by treating the observed sample as a stand-in for the unknown population and re-drawing from it with replacement. Each call to `resample(weights)` produces a new array of the same length as the original by sampling with replacement; the 1001 resulting standard deviations form an approximate sampling distribution of $\hat{\sigma}$. This is valid under an exchangeability assumption: the observations must be i.i.d. (or at least exchangeable), so that shuffling and re-drawing preserves the relevant structure of the data. If the penguins were not an independent random sample — say, if weights were collected from family groups — the bootstrap would understate variability.

The standard error is then just `np.std(sample_stds)`: the standard deviation of the bootstrap distribution measures how much $\hat{\sigma}$ would vary across repeated samples of the same size. The 90% confidence interval uses `np.percentile(sample_stds, [5, 95])`, the percentile (basic) bootstrap CI. This interval is only approximately correct; it relies on the bootstrap distribution of $\hat{\sigma}$ being a good proxy for the true sampling distribution. For standard deviation, unlike for the mean, there is no Central Limit Theorem guarantee, so the approximation is less tight at small $n$.

## Exercise: Mean Height from BRFSS with Non-Sampling Error Sources

The mechanics here mirror Exercise 8.1 — 1001 bootstrap resamples, each of length equal to the full BRFSS male sample (~154,000 observations), computing `np.mean` on each resample. The resulting CI is extremely narrow (approximately 178.04–178.10 cm) because the standard error of the mean scales as $\sigma/\sqrt{n}$, and $n$ is very large.

This tightness reveals a fundamental distinction between sampling variability and other sources of error. The standard error quantifies only random-sampling noise — how much the estimate would jump around if you drew a fresh probability sample of the same size. But the BRFSS uses a complex stratified design with deliberate oversampling of subgroups; failing to apply survey weights introduces selection bias that is entirely invisible to the bootstrap, because the bootstrap only resamples the data you have, not from a corrected population. Similarly, self-reported heights are known to be systematically overstated, creating measurement bias. And the anomalous spikes in the data at extreme values (61 cm, 243 cm) suggest recording or transmission errors. All of these biases can be much larger in magnitude than the 0.06 cm CI width. The lesson is that narrow confidence intervals signal precision of the estimate conditional on the data being representative — they say nothing about whether the data-generating process itself is unbiased.

## Exercise: Consistency and Bias of Mean vs. Median for Exponential Data

For an exponential distribution with mean $\lambda$, the probability density is $f(x) = \frac{1}{\lambda} e^{-x/\lambda}$. The population median is the value $m$ satisfying $F(m) = 0.5$, giving $1 - e^{-m/\lambda} = 0.5$, so $m = \lambda \ln 2$. The code evaluates this as `np.log(2) * actual_mean`, approximately 6.93 for $\lambda = 10$.

The solution generates a sequence of samples of increasing size $n$ and plots both the sample mean and sample median against their respective population targets. Both converge as $n$ grows — both estimators are **consistent**. But the mean is also **unbiased**: the average of 100,001 sample means with $n=10$ is approximately 10.005, indistinguishable from $\lambda=10$ within simulation noise. The sample median is not unbiased for the population median: the average of 100,001 sample medians lies noticeably below the population median $\ln 2 \cdot \lambda \approx 6.93$. This bias arises because the median of a small sample from a skewed distribution has a finite-sample distribution that is itself skewed — Jensen's inequality applied to the CDF inversion. The distinction matters for practice: if you were trying to estimate the mean time between goals using the median (perhaps as a more robust alternative), you would need to correct for this bias, or use the plug-in relationship $\hat{\lambda} = \hat{m} / \ln 2$ to recover an unbiased estimate of $\lambda$ from the sample median.

## Exercise: The Square Root of an Unbiased Estimator is Not Unbiased

This exercise demonstrates one of the more counterintuitive facts in estimation theory. The **biased** variance estimator divides by $n$:

$$S^2_n = \frac{1}{n}\sum_{i=1}^n (x_i - \bar{x})^2$$

The **unbiased** variance estimator divides by $n-1$ (Bessel's correction):

$$s^2 = \frac{1}{n-1}\sum_{i=1}^n (x_i - \bar{x})^2, \quad E[s^2] = \sigma^2$$

Taking square roots of both and averaging over many samples of size 10 from Normal(3.7, 0.46), neither `biased_std` (sqrt of $S^2_n$) nor `unbiased_std` (sqrt of $s^2$) produces an average close to 0.46. Both underestimate the population $\sigma$.

The reason is Jensen's inequality: the square root is a concave function, so $E[\sqrt{X}] \leq \sqrt{E[X]}$. Because $E[s^2] = \sigma^2$, it follows that $E[s] = E[\sqrt{s^2}] \leq \sqrt{E[s^2]} = \sigma$. Correcting for this would require a correction factor that depends on $n$ and on the assumed distribution — for the normal case the correction uses the chi distribution's mean, giving $c_4(n)$. No single clean formula works distribution-free. This is why, in practice, we accept that sample standard deviations are slightly biased and treat the bias as negligible for large $n$.

## Exercise: German Tank Problem — An Exactly Unbiased Discrete Estimator

The estimator here is

$$\hat{N} = m + \frac{m - k}{k}$$

where $m$ is the maximum observed serial number and $k$ is the number of tanks captured. This can be rearranged to $\hat{N} = m \cdot \frac{k+1}{k} - 1$. The setup assumes serial numbers are drawn without replacement from a discrete uniform distribution on $\{1, 2, \ldots, N\}$ — a finite population sampling problem, not an i.i.d. one, so this is a rare situation where `replace=False` is the correct model.

The minimum sufficient statistic for $N$ is $(m, k)$ alone. The formula inflates $m$ by the average gap between order statistics: if $k$ tanks are drawn uniformly from $N$, the expected spacing between consecutive order statistics is $\frac{N+1}{k+1}$, so the expected gap between the maximum observation and $N$ is also approximately $\frac{m-k}{k}$. The simulation confirms near-unbiasedness: 10,001 estimates average to about 121.7 against the true $N=122$. The residual shortfall (about 0.3) is a small-sample finite-population correction that vanishes as $k/N \to 0$.

A key hidden assumption is that the captures are a simple random sample without replacement from all tanks. If certain serial number ranges (say, tanks on the front line) were more likely to be captured, $m$ would be biased upward and the estimate would be inflated.

## Exercise: Hot Hand Fallacy and the Bias of Conditional Probability on Finite Sequences

This exercise replicates the Miller and Sanjurjo (2018) finding: the statistic "fraction of hits following three consecutive hits," computed on a finite i.i.d. Bernoulli(0.5) sequence, has expected value strictly less than 0.5 even though the shots are truly independent.

The mechanism in the code: `np.correlate(seq, [1,1,1], mode="valid")` slides a window of length 3 over the sequence and returns the dot product with the all-ones kernel at each position — equivalent to computing the sum of each consecutive triple. Positions where this sum equals 3 identify the end of a run of three hits; the element at index `i+3` is the successor. The function carefully excludes the last position (where no successor exists), which is itself a source of bias: runs of three hits that fall at the very end of the sequence are excluded from the denominator but would have contributed a hit had the sequence continued.

Running 10,001 simulations with sequence length 50 gives an average conditional probability of about 0.42 — far below 0.5. Increasing to length 100 gives ~0.46, and to 200 gives ~0.48. The statistic converges to 0.5 as sequence length grows (it is **consistent**) but is downward biased for any finite $n$ — exactly the property that fooled Gilovich, Vallone, and Tversky (1985) into concluding no hot hand existed. `np.nanmean` correctly ignores simulations where no triple-hit occurred (which returns `np.nan`), avoiding the misleading anchor of treating "no qualifying events" as a zero probability.
