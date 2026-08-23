Now I have everything I need. Let me write the commentary.

# Relationships between variables

This chapter's exercises build fluency with the core toolkit for exploring bivariate relationships: scatter plots with jitter and transparency to fight overplotting, decile plots to reveal conditional distributions, and two flavours of correlation — Pearson's $r$ and Spearman's $\rho$ — that capture different aspects of association. The code patterns recurring throughout are `pd.qcut` for equal-count binning, `groupby` + `quantile` for within-group summaries, and the contrast between `corrcoef` and `rankcorr`, which exposes when a distribution's shape (skewness, heavy tails) makes the choice of correlation measure non-trivial.

## Exercise: Decile Plot of PIAT Math Scores versus Income

`decile_plot` wraps three operations that together sidestep the overplotting problem. First, `pd.qcut(x, 10, labels=False)` partitions the x-variable into ten equal-count bins — the bin boundaries are chosen so that roughly 10 % of observations fall in each group, not so that the bins have equal width. This is a crucial distinction: equal-width bins would put most data in a few central bins, hiding the relationship at the tails. Second, `groupby` on those bin labels splits the DataFrame, and third, `quantile` at 0.1, 0.5, and 0.9 summarises the conditional distribution of $y$ within each x-decile. The plot then shows the median as a line and the 10th–90th percentile range as a shaded band.

The exercise asks whether the relationship between PIAT math scores and income looks linear. The solution notes it is "close to linear, although it might level off a little at the high end." This matters because Pearson's $r$ measures only linear association: if the true relationship is curved, $r$ will understate it. When the decile plot shows curvature — especially at the extremes — a transformation (log-income, say) or a rank-based measure is more appropriate. Here the modest levelling-off suggests Pearson is a reasonable but not perfect summary. A hidden assumption throughout this kind of analysis is that the relationship is the same across the support of $x$; the decile plot is precisely the tool that tests this, so inspecting it before trusting a single correlation number is good practice.

## Exercise: Income versus SAT Math and Verbal Scores

`corrcoef(nlsy, "sat_math", "income")` computes Pearson's product-moment correlation:

$$r = \frac{\sum_i (x_i - \bar{x})(y_i - \bar{y})}{\sqrt{\sum_i(x_i-\bar{x})^2 \sum_i(y_i-\bar{y})^2}}$$

This is sensitive to both scale and outliers, and assumes the relationship is linear. `rankcorr` replaces each value with its rank within the sample and then computes Pearson's $r$ on those ranks — this is Spearman's $\rho$. Ranking is a monotone transformation, so $\rho$ captures any monotone relationship, not just linear ones. It is also much less sensitive to outliers, because an extreme value simply takes the highest (or lowest) rank rather than pulling the mean and standard deviation.

For SAT math versus income, Pearson $r \approx 0.30$ and Spearman $\rho \approx 0.31$ — nearly identical. This agreement suggests that the relationship is approximately linear and that outliers in income are not distorting Pearson here, even though income is right-skewed. For SAT verbal versus income, both are lower ($r \approx 0.20$, $\rho \approx 0.23$), with a slightly larger gap; the higher-rank correlation hints at a mild nonlinearity or slightly more extreme income outliers influencing the Pearson value downward. The substantive conclusion — that SAT math scores are a better predictor of later income than SAT verbal scores — should be tempered by the fact that correlation does not establish causation, and both variables may be driven by socioeconomic background.

## Exercise: GPA versus SAT Math and Verbal Scores

The same `corrcoef` and `scatter` machinery applies here, and the exercise tests whether GPA is more tightly coupled to the math or verbal section of the SAT. The results ($r \approx 0.49$ for math, $\approx 0.43$ for verbal) are noticeably higher than the SAT-to-income correlations from Exercise 7.2. This makes conceptual sense: GPA is measured concurrently with the SAT and both reflect academic performance in school, whereas income is measured years later and depends on many additional factors.

The slightly higher correlation with math scores than verbal scores parallels the finding in Exercise 7.2. One interpretation is that quantitative reasoning, captured by both PIAT math and SAT math, is a more consistent predictor of outcomes than verbal skill in this dataset.

A hidden assumption worth naming is that Pearson's $r$ is being applied to GPA, which is bounded in $[0.0, 4.0+]$ and is approximately but not perfectly continuous — grades cluster at discrete values, and the top of the scale is censored (a 4.0 means "at least 4.0"). Neither violation is severe enough to invalidate the analysis here, but if GPA were more severely censored the attenuation of $r$ near the ceiling could hide a stronger true relationship.

## Exercise: Education Degree versus Income (NLSY)

Degree is an ordinal categorical variable, not a continuous one, so this exercise requires a different approach than computing a single correlation. The first part — jittering — treats degree values (0 through 7) as if they were continuous, adding Gaussian noise with a small standard deviation (0.15 units) purely for display. This is valid because it does not alter the analysis, only spreads the markers horizontally so that overlapping points at each integer become visible. The note to use jitter only for visualisation, not analysis, is important: computing a correlation on jittered data would introduce artificial variance.

The groupby-and-quantile approach mirrors the decile plot construction but on pre-defined groups (degree levels) rather than quantile-based bins. `df_groupby["income"].quantile(0.1)` computes the 10th percentile of income within each degree group; `fill_between(xs, low, high)` then draws the interquartile-like band. This is a form of conditional quantile estimation: it makes no distributional assumptions, only requiring enough data in each group for the quantile estimates to be stable.

The solution commentary notes that professional degrees (medical, legal) show the largest income premium. This observation is consistent with the skewed nature of professional earnings, where a few very high earners lift the 90th percentile substantially. The Pearson correlation applied across this ordinal variable would conflate the spacing between degree levels (is a PhD "twice as educated" as a Bachelor's?), making the groupby visualisation more informative here than a single summary statistic.

## Exercise: Height versus Weight in the BRFSS Dataset

With roughly 400,000 respondents, every visualisation decision is forced by overplotting. The jitter applied to height (standard deviation 2.8 cm) is calibrated to smear the rounding artifact: reported heights are rounded to the nearest centimetre, so without jitter the scatter plot shows discrete vertical stripes. Similarly, weights are jittered by 1 kg. The choice of $s=0.1$ (marker size) and $\alpha = 0.01$ (transparency) means that a region needs approximately 100 overlapping points before it appears solid — appropriate for a dataset this dense.

`xlim` and `ylim` clip to a biologically reasonable range. This is not just cosmetic: clinical outliers (e.g., individuals over 200 kg) can compress the visible portion of the plot and obscure the pattern for the majority of respondents.

The decile plot reveals an approximately linear relationship, and the correlation comparison is instructive: Pearson $r \approx 0.51$, Spearman $\rho \approx 0.54$. The gap is larger than in Exercise 7.2 and in a consistent direction — rank correlation is higher. This is the expected signature of right-skewed outliers: a small number of individuals with very high weights are far from the main cloud, pulling the Pearson estimate down (since they inflate $\sigma_y$ without contributing proportionally to the covariance), while the rank transformation neutralises their influence by assigning them the top ranks. In this context, Spearman's $\rho$ is the more trustworthy summary of the strength of the height-weight relationship across the bulk of the population.
