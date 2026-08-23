Now I have everything I need. Let me write the commentary.

# Hypothesis Testing

This chapter trains the core computational loop of permutation-based hypothesis testing: observe a test statistic on real data, construct a null distribution by repeatedly destroying the structure the null hypothesis denies, and report the fraction of simulated values that meet or exceed the observed value. Every exercise instantiates exactly this loop with a different test statistic and a different method of null-hypothesis simulation — `simulate_groups` for two-sample mean comparisons and `permute` for correlation — making the pattern's generality visible. The helper function `compute_p_value` is deliberately simple (a single mean of a boolean array), keeping the probabilistic logic legible: the p-value is an empirical proportion, not a black-box formula.

## Exercise: Permutation Test for Sex Differences in Chinstrap Penguin Weight

The exercise tests whether the observed 0.412 kg difference in mean body mass between male and female Chinstrap penguins could plausibly have arisen by chance if both sexes were drawn from the same weight distribution.

The workhorse is `simulate_groups`. It pools all 68 observations into a single array with `np.hstack(data)`, shuffles that array in place with `np.random.shuffle`, then slices off the first $n$ elements as group 1 and the last $m$ as group 2. This preserves the original group sizes exactly. The key statistical justification is **exchangeability**: under the null hypothesis that sex has no effect on weight, the label "male" or "female" attached to any bird is arbitrary — every assignment of 34 birds to each label is equally likely. The shuffle enumerates that space of assignments uniformly at random.

The test statistic is $|\bar{x}_{\text{male}} - \bar{x}_{\text{female}}|$, the absolute difference in group means. Taking the absolute value makes the test two-sided in spirit while remaining one-sided in implementation: we ask whether the gap in either direction is surprisingly large.

Running 1001 permutations and computing `compute_p_value` — which evaluates $\hat{p} = \frac{1}{B}\sum_{b=1}^{B} \mathbf{1}[\delta^{(b)} \geq \delta_{\text{obs}}]$ — yields 0.0. This does not mean the true p-value is zero; it means none of the 1001 simulated differences reached 0.412 kg. The comment in the solution correctly interprets this as $p < 1/1001 \approx 0.001$.

A hidden assumption is that observations within each group are independent and that the two samples are exchangeable under $H_0$. Sexual dimorphism is real in this species (the original paper documents it), so the result is unsurprising — but the permutation framework would give a valid test regardless of the shape of the weight distribution, requiring no normality assumption.

## Exercise: Permutation Test for Correlation Between Culmen Dimensions in Female Penguins

This exercise asks whether a Pearson correlation of 0.256 between culmen depth and culmen length in female Chinstrap penguins is consistent with the null hypothesis of no linear association.

`abs_correlation` calls `np.corrcoef(xs, ys)[0, 1]`, which computes Pearson's $r = \frac{\sum_i (x_i - \bar{x})(y_i - \bar{y})}{(n-1)\,s_x\,s_y}$. Taking the absolute value again makes the test agnostic to the direction of any linear relationship.

The `permute` function simulates the null hypothesis by shuffling only the $x$ values (culmen depths) while leaving the $y$ values (culmen lengths) in their original order. This destroys every pairing between a specific bird's depth and that same bird's length, which is precisely what the null hypothesis claims: depth and length are independent, so knowing one tells you nothing about the other. The asymmetry — shuffling $x$ but not $y$ — is immaterial; shuffling either variable, or both, equally destroys the pairwise structure. The resulting null distribution is the set of correlations you would see in data with no real association.

With 1001 simulations, `compute_p_value` returns approximately 0.14, meaning about 14% of null-hypothesis datasets produced a correlation at least as large as 0.256. This is not small enough to rule out chance as an explanation.

An important hidden assumption is that Pearson's $r$ measures only **linear** dependence. If the true relationship between culmen depth and length were curved or monotone but nonlinear, Pearson's $r$ would understate it, and this test would have low power to detect it. A rank-based test statistic (Spearman's $\rho$) inside the same permutation loop would be more sensitive to monotone relationships without requiring normality. The permutation framework itself remains valid either way — only the test statistic needs to change.
