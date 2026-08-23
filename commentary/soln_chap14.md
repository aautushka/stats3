Now I have everything needed to write the commentary. Let me compose it.

# Analytic Methods

The exercises in this chapter practice replacing computational simulation with exact analytic results derived from the properties of the normal distribution. The key code pattern throughout is constructing `Normal` objects — each parameterised by a mean $\mu$ and variance $\sigma^2$ — and then composing them using arithmetic operators whose implementations encode statistical facts: sums of normals are normal with additive means and variances, and scaling by $1/n$ gives the sampling distribution of the mean. The exercises then apply this analytic machinery to confidence intervals, correlation $t$-tests, chi-squared tests of independence, and differences-in-differences designs.

## Exercise: Analytic Confidence Interval for Flipper Length Difference

The solution calls `sampling_dist_mean(data, n)` for each sex group separately, then subtracts the resulting `Normal` objects. Understanding each step is essential.

`sampling_dist_mean` does four things in two lines: it computes the sample mean $\bar{x}$ and variance $s^2$, wraps them into a `Normal(\bar{x}, s^2)` representing the population model, calls `.sum(n)` which returns `Normal(n\bar{x},\, n s^2)` (using the additive-variance rule for the sum of $n$ iid normals), and finally divides by $n$, giving `Normal(\bar{x},\, s^2/n)`. That last object is exactly the **sampling distribution of the sample mean**: centred on the true mean, with variance $\sigma^2/n$ — the familiar standard error formula $\text{SE} = \sigma/\sqrt{n}$ emerges automatically from the algebra of Normal objects.

The subtraction `dist_male - dist_female` exploits a further closure property: if $X \sim \mathcal{N}(\mu_1, \sigma_1^2)$ and $Y \sim \mathcal{N}(\mu_2, \sigma_2^2)$ independently, then $X - Y \sim \mathcal{N}(\mu_1 - \mu_2,\, \sigma_1^2 + \sigma_2^2)$. Note that variances **add** even when computing a difference — the uncertainty from two independent estimates compounds. The 90% CI is then read off via `dist_diff.ppf([0.05, 0.95])`, which inverts the normal CDF to find the 5th and 95th percentiles.

A critical hidden assumption: `sampling_dist_mean` uses the **plug-in** estimator — it treats $s^2$ as if it were the true population variance $\sigma^2$. This is valid when $n$ is large (both groups have over 70 Adelie penguins), but for small samples a $t$-distribution with $n-1$ degrees of freedom would be more appropriate. The exercise also assumes the two groups are independent samples, which is satisfied by design in the Palmer Penguins data.

## Exercise: Correlation t-Test for Birth Weight and Father's Age

The correlation between father's age (`hpagelb`) and birth weight (`totalwgt_lb`) is computed on complete cases only (`.dropna(subset=[...])`), then tested with `transform_correlation`, which applies the classical transformation:

$$t = r\sqrt{\frac{n-2}{1-r^2}}$$

This converts the sample Pearson correlation $r$ into a statistic that, under $H_0: \rho = 0$, follows a $t$-distribution with $n - 2$ degrees of freedom. The intuition: fitting a bivariate normal uses up 2 degrees of freedom (one for each marginal), leaving $n-2$ for the residuals. The transformation is monotone in $r$, so testing $t = 0$ is equivalent to testing $r = 0$.

The p-value is computed as `student_t.cdf(-t_actual, df=n-2) * 2` — a two-sided test that asks: if the true correlation were zero, what fraction of samples would produce an absolute correlation at least this large? With $n = 8933$ and $r \approx 0.065$, the p-value is $\approx 9.4 \times 10^{-10}$, which is extremely significant despite the small effect size. This is a textbook illustration of the **power problem**: with nearly 9,000 observations even tiny correlations become detectable, so statistical significance here says almost nothing about practical importance.

Key assumptions: the $t$-test for Pearson $r$ assumes bivariate normality and a linear relationship. Father's age in survey data is likely right-skewed, so normality may be mildly violated — though with $n \approx 9000$ the CLT makes the $t$ approximation robust. `pearsonr` from `scipy.stats` confirms the result to 15 significant figures, providing a useful sanity check.

## Exercise: Chi-Squared Test of Baby Sex and Maternal Marital Status (Trivers-Willard)

This exercise applies the chi-squared goodness-of-fit test to a two-way count table. The observed counts are a 5×2 DataFrame (marital status × baby sex). The expected counts are constructed by multiplying the **null-hypothesis marginal distribution** of marital status — estimated from the full dataset — by each column total:

$$E_{ij} = \hat{p}_i \cdot n_j$$

where $\hat{p}_i$ is the overall proportion in marital-status category $i$ and $n_j$ is the total for sex group $j$. This null hypothesis says that the distribution of marital status is identical for mothers of male and female babies.

`chi_squared_stat` computes $\chi^2 = \sum_{ij} (O_{ij} - E_{ij})^2 / E_{ij}$, the sum over all cells of the squared standardised residual. Under $H_0$ and assuming expected counts are not too small (a common rule of thumb is $E_{ij} \geq 5$, satisfied here), this statistic follows a $\chi^2$ distribution. The degrees of freedom are `n - 1 = 9`, where $n = 10$ is the total number of cells. Using `axis=None` in `scipy.stats.chisquare` treats the whole 5×2 table as one joint test rather than performing separate column-wise tests — this is essential for correctly pooling evidence across all cells.

The p-value of 0.925 is large: the observed pattern is entirely consistent with the null hypothesis. The conclusion — no support for the Trivers-Willard hypothesis using this proxy — illustrates that a statistically non-significant result can be substantively informative when the sample is large enough that a real effect would likely have been detected.

## Exercise: Difference-in-Differences for Gender Gap in Engineering Teams

This exercise demonstrates that the `Normal` class machinery extends directly to published summary statistics: when a study reports estimated means and standard errors (but not raw data), you can construct `Normal(mu, se**2)` objects directly, since the standard error **is** the standard deviation of the sampling distribution of the mean.

The solution creates four `Normal` objects with variances set to $\text{SE}^2$ rather than $\sigma^2/n$. This bypasses the need to know sample sizes — the standard error already encodes that information. The differences `male_before - female_before` and `male_after - female_after` give sampling distributions for the gender gap at each time point. Their variances add because the male and female group estimates are independent:

$$\text{Var}(\bar{X}_m - \bar{X}_f) = \text{SE}_m^2 + \text{SE}_f^2$$

The difference-in-differences `diff_after - diff_before` then gives the change in the gap, again with compounding variances. The `summarize` function computes a p-value for each quantity by evaluating `dist.cdf(0)` (or its complement): if the distribution's mean is positive, the p-value for testing whether the true quantity is zero or negative is the probability mass below zero.

The key result — mean $-1.4$, 95% CI $[-2.34, -0.46]$, $p \approx 0.002$ — provides strong evidence that the gender gap in self-reported programming contribution narrowed after the intervention. A hidden assumption throughout is that the reported standard errors are **frequentist** standard errors (not Bayesian posterior standard deviations), and that the four group estimates are mutually independent — the study design (separate pre/post surveys with different male/female groups) makes this plausible but worth examining for repeated-measures structures.
