# Least Squares

These exercises practice the mechanics and interpretation of ordinary least squares (OLS) regression: fitting lines, reading regression output, quantifying fit via $R^2$, bootstrapping the sampling distribution of estimators, and using variable transformations to handle non-linear relationships. The code patterns — `linregress`, `resample`, `predict`, `compute_residuals` — implement the statistical concepts of MLE-equivalent closed-form estimators, non-parametric uncertainty quantification, and linearisation through monotone transformation.

## Exercise: Culmen Length as a Predictor of Penguin Weight

`linregress` solves the ordinary least squares problem: it finds the slope $\hat{\beta}$ and intercept $\hat{\alpha}$ that minimise the sum of squared residuals $\sum_i (y_i - \hat{\alpha} - \hat{\beta} x_i)^2$. The closed-form solution is

$$\hat{\beta} = \frac{\sum_i (x_i - \bar{x})(y_i - \bar{y})}{\sum_i (x_i - \bar{x})^2}, \qquad \hat{\alpha} = \bar{y} - \hat{\beta}\bar{x}$$

which is algebraically what the hand-rolled `least_squares` function from the chapter computes. For Adelie penguins, fitting body mass on culmen length gives a slope of about 94.5 g/mm and an $r$ of approximately 0.549, yielding $R^2 \approx 0.30$. Compared with the flipper-length regression ($r \approx 0.468$, $R^2 \approx 0.22$), culmen length explains about eight more percentage points of the variance in mass — a modest but real improvement.

The key interpretive step the exercise asks you to perform is reading `result.rvalue` and squaring it to get $R^2$. These two quantities tell different stories: $r$ lives on $[-1, 1]$ and encodes both magnitude and direction of the linear association, while $R^2 \in [0, 1]$ is always non-negative and answers the question "by what fraction does the fitted line reduce mean squared prediction error relative to always guessing the mean?" Because $R^2$ is the square of $r$ in simple linear regression, a modest-looking $r = 0.55$ translates to $R^2 = 0.30$, meaning 70% of the variance in weight is still unexplained by culmen length alone.

A hidden assumption throughout is that the relationship is linear and that the residuals are roughly homoskedastic (constant spread across all values of $x$). Inspecting the scatter plot is the right first check — if the cloud fans out as $x$ increases, a transformation may be more appropriate, as the next exercise explores.

## Exercise: Bootstrap Sampling Distribution of the Intercept

This exercise extends the slope-resampling from the chapter to the intercept, revealing an important asymmetry: the intercept is far more variable than the slope. The bootstrap 90% CI for the intercept spans roughly $[-3895, -1187]$ grams — a range of about 2700 g — while its standard error from resampling (~832 g) is almost double the parametric `intercept_stderr` (~458 g) that `linregress` reports.

The discrepancy is worth understanding. The parametric `intercept_stderr` is derived under the classical OLS assumption that residuals are i.i.d. Normal with constant variance, using the formula $\text{SE}(\hat{\alpha}) = \hat{\sigma}\sqrt{\frac{1}{n} + \frac{\bar{x}^2}{\sum(x_i-\bar{x})^2}}$. Bootstrap resampling makes no distributional assumptions; it treats the observed data as a proxy population and propagates sampling variability empirically. When the residual distribution is not Normal — or when the sample is small — bootstrap standard errors are often more reliable.

The large uncertainty in the intercept has a geometric explanation. The intercept is the predicted value at $x = 0$ (flipper length of 0 mm), which is far outside the range of the data (~172–210 mm). Extrapolating the fitted line that distance amplifies any uncertainty in the slope enormously. This is why evaluating a regression at the mean $\bar{x}$ gives the most precise predictions — that is the pivot point around which all fitted lines from bootstrap samples rotate.

The exercise also reinforces the exchangeability assumption underlying bootstrap validity: resampling rows with replacement is only justified if observations are independent and identically distributed. For these penguin measurements, that's reasonable, but time-series or clustered data would violate it.

## Exercise: Log-Log Regression to Empirically Estimate the BMI Exponent

Body Mass Index uses the formula $\text{BMI} = w / h^2$, with the exponent 2 chosen historically on the basis that average weight scales approximately with height squared. This exercise asks you to test that claim by recovering the exponent from data — a nice demonstration of how a power-law relationship can be linearised with logarithms.

If $w = b \cdot h^a$, taking $\log_{10}$ of both sides gives

$$\log_{10} w = \log_{10} b + a \cdot \log_{10} h$$

which is a linear equation in $(\log_{10} h,\, \log_{10} w)$ with slope $a$ and intercept $\log_{10} b$. Running `linregress(log_heights, log_weights)` therefore estimates $a$ directly as the slope — no algebraic post-processing required. The result, approximately 2.04, is indeed close to 2, providing empirical support for the BMI convention.

The choice of logarithm base is immaterial for the slope: if you use $\ln$ instead of $\log_{10}$, the slope $a$ is unchanged because the change of base is a multiplicative constant that cancels in the ratio that defines slope. Only the intercept changes.

A hidden assumption here is that the power-law model $w = b h^a$ is the correct functional form. The linearity of the log-log scatter plot (along with the symmetric residuals) is evidence in its favour, but not proof. The model also assumes multiplicative noise — that the true relationship is $w = b h^a \cdot \epsilon$ where $\epsilon$ is a positive random variable, which is exactly what the log transformation converts into additive Normal noise. If instead the noise were additive on the raw scale ($w = b h^a + \epsilon$), working on the log scale would not be appropriate. Examining the residual distribution (roughly symmetric on the log scale) is the practical check the solution implicitly performs.
