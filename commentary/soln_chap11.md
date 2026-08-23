# Multiple Regression

The exercises in this chapter move from simple two-variable regression to models with several explanatory variables, a categorical predictor, and a binary response. The core code pattern is Patsy formula notation fed to `smf.ols()` or `smf.logit()`, which hides a great deal of linear algebra and maximum likelihood machinery. Understanding what those calls actually compute — and what assumptions they silently make — is the point of these exercises.

## Exercise: Sex Differences in Birth Weight with and without Maternal Age Control

The formula `"totalwgt_lb ~ C(babysex)"` illustrates how Patsy handles categorical predictors. The `C()` operator tells the model to dummy-encode `babysex`: it picks one value as the **reference level** (boys, coded 1, because it is the numerically smaller value) and creates one indicator column for the other category (girls, coded 2). The model then fits

$$\hat{w} = \beta_0 + \beta_1 \cdot \mathbf{1}[\text{girl}]$$

so $\beta_0$ is the estimated mean weight for boys and $\beta_1$ is the estimated difference girls minus boys. The coefficient `C(babysex)[T.2.0] = -0.296` means girls are about 0.30 lb lighter. The $t$-statistic of $-10.04$ is computed as $\hat{\beta}_1 / \widehat{\text{SE}}(\hat{\beta}_1)$ and is compared against a $t$ distribution with $n - 2$ degrees of freedom; the resulting $p$-value is effectively zero, so the difference is far beyond what chance variation would produce under the null.

Adding `agepreg` and then `agepreg2` to the formula introduces the idea of **control variables**. When the model includes maternal age, OLS finds the coefficient on `babysex` that explains variation in birth weight *after removing the linear trend with age*. Because the `babysex` coefficient barely moves ($-0.296 \to -0.295 \to -0.297$) and the $R^2$ increment is modest, the exercise demonstrates that maternal age is not a confound — it is independently predictive of weight but does not mediate the sex difference.

The quadratic term `agepreg2` is not constructed by Patsy syntax here; it is pre-computed as a column in the DataFrame. This approach sidesteps the `I(agepreg**2)` Patsy idiom but requires care: the squared column and the linear column are highly correlated, inflating standard errors. The statistically significant quadratic term tells us the age–weight relationship curves (weight peaks at intermediate maternal ages), but this does not change the sex-gap estimate.

Hidden assumptions: OLS requires that residuals are independent, have constant variance across values of the predictors (homoskedasticity), and are approximately normally distributed. With NSFG survey data, births are clustered within mothers and the survey uses a complex sampling design; both violations bias the reported standard errors downward. The $p$-values here should be read as approximate.

## Exercise: Logistic Regression for the Trivers-Willard Hypothesis

Because the outcome is binary (boy or girl), OLS is inappropriate — it can produce predicted probabilities outside $[0, 1]$ and has systematically non-constant variance. Logistic regression solves this by modelling the **log-odds**:

$$\log \frac{P(\text{boy})}{1 - P(\text{boy})} = \beta_0 + \beta_1 \cdot \text{agepreg}$$

The `smf.logit()` call estimates $\beta_0$ and $\beta_1$ by **maximum likelihood**, not OLS. The likelihood is the probability of the observed 0/1 sequence under the logistic model; MLE finds the parameter values that maximise it. Because there is no closed-form solution, an iterative algorithm (IRLS) is used internally. Consequently, inference uses a **$z$-statistic** (Wald statistic), $z = \hat{\beta} / \widehat{\text{SE}}(\hat{\beta})$, compared against a standard normal, rather than the $t$-statistic from OLS.

The recoding step `valid["y"] = (valid["babysex"] == 1).astype(int)` is essential: the logit model requires the response to be 0 or 1. The original encoding (1 = boy, 2 = girl) would be accepted numerically but would be meaningless — the model would predict the probability of having a value of 1 vs. 2, which is not a coherent probability.

The **pseudo $R^2$** shown in the output is McFadden's statistic, $1 - \mathcal{L}_{\text{model}} / \mathcal{L}_{\text{null}}$, where the likelihoods are on the log scale. It is not directly comparable to OLS $R^2$ but values near zero indicate the model explains almost nothing beyond the intercept. Here pseudo $R^2 \approx 0.00001$: maternal age accounts for essentially none of the variation in infant sex, consistent with the near-zero, high-$p$-value coefficient on `agepreg`. The quadratic formula in the solution accidentally repeats `agepreg + agepreg` rather than adding `agepreg2`, so the output is identical to the linear model — a subtle copy-paste error that produces the same result.

## Exercise: Multiple Regression for Penguin Mass with a Categorical Sex Predictor

The formula `"mass ~ flipper_length + culmen_depth + C(Sex)"` combines two continuous predictors with one binary categorical predictor. OLS fits:

$$\hat{m} = \beta_0 + \beta_1 \cdot \text{flipper} + \beta_2 \cdot \text{depth} + \beta_3 \cdot \mathbf{1}[\text{MALE}]$$

The coefficient `C(Sex)[T.MALE] = 505.5` is the estimated mass difference between males and females **holding flipper length and culmen depth constant**. This is the crucial distinction from a simple comparison of group means: because male penguins also have longer flippers and deeper bills on average, a naive male-minus-female mean would mix the sex effect with those morphological differences. Multiple regression partitions the variance algebraically so $\beta_3$ captures only the sex contribution that is orthogonal to the other predictors.

The prediction block constructs a synthetic `DataFrame` with `flipper_length` swept across its observed range and `culmen_depth` pinned to its sample mean, then calls `result.predict(df)` twice — once with `Sex = "MALE"` and once with `Sex = "FEMALE"`. Because the model has no interaction terms, the male and female prediction lines are parallel; the vertical gap between them is exactly $\hat{\beta}_3 = 505.5$ g at every flipper length. If you wanted the gap to vary with flipper length, you would add the interaction term `flipper_length:C(Sex)` to the formula. The $R^2 = 0.61$ shows this three-predictor model explains about 61% of the variance in Adelie penguin mass — a substantial improvement over a single-predictor model.

A hidden assumption in this additive model is **no interaction between sex and the continuous predictors**. If male penguins gain mass faster per millimetre of flipper than females do, the parallel-lines model is misspecified and $\hat{\beta}_3$ is an average of a sex gap that actually varies.

## Exercise: Comparing Sexual Dimorphism Across Penguin Species via Pseudo $R^2$

Logistic regression is repurposed here as a **quantitative index of sexual dimorphism**: if physical measurements can predict sex reliably, the species is more dimorphic; if they cannot, it is less so. The pseudo $R^2$ from McFadden's formula serves as that index because it measures how much better the fitted model is than a trivial intercept-only model (which always predicts the majority sex).

The formula `"y ~ mass + flipper_length + culmen_length + culmen_depth"` uses all four morphometric variables simultaneously. MLE estimates coefficients for each predictor on the log-odds scale. The resulting pseudo $R^2 = 0.686$ for Chinstrap penguins is very high (compare to near-zero for the maternal-age model in Exercise 11.2, where the predictor was irrelevant). This indicates that the four measurements together almost perfectly discriminate male from female Chinstrap penguins. Individual $p$-values reveal that `culmen_length` ($p = 0.006$) and `culmen_depth` ($p = 0.012$) carry most of the discriminating power, while `mass` and `flipper_length` are not individually significant given the others are in the model — a classic sign of **multicollinearity** among morphometric variables.

The comparison across species is informal here: to formally test whether Chinstrap dimorphism differs from Adelie or Gentoo, one would need a single model with species as a categorical variable, or a likelihood-ratio test between species-specific models. The pseudo $R^2$ comparison is a useful heuristic but not a statistical test.

---

File written to: `/Users/anton/proj/bayes2/chap11_commentary.md`
