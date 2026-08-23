# Time Series Analysis

These exercises build a complete working vocabulary for time series modelling by moving through three nested layers of complexity: additive decomposition for a slowly-varying signal, multiplicative decomposition for an explosively-growing one, and a full SARIMA specification for a series whose structure resists decomposition. Each exercise asks you to make a modelling choice — additive vs multiplicative, linear vs quadratic trend, which lags to include in AR and MA — and then interrogate that choice with a quantitative accuracy measure. The through-line is that every method is ultimately a way of separating what is predictable (trend plus seasonality) from what is not (residual), and the residual structure tells you whether your model is adequate.

## Exercise: Additive Decomposition and Trend Rate for US Surface Temperature

`seasonal_decompose` with `model="additive"` assumes the observed series can be written as

$$y_t = T_t + S_t + \varepsilon_t$$

where $T_t$ is a slowly-varying trend, $S_t$ is a periodic seasonal component, and $\varepsilon_t$ is a residual. Internally, the function estimates $T_t$ using a centred moving average over the specified period (12 months here), which is a low-pass filter that removes oscillations at the seasonal frequency. $S_t$ is then estimated by averaging the detrended values within each calendar month across all years, producing 12 fixed offsets that repeat identically. This is the classical Census X-11 decomposition logic.

The critical hidden assumption is **stationarity of the seasonal amplitude**: the additive model treats the 12 month-offsets as constant across the entire sample. For temperature, this is defensible because the seasonal swing (summer–winter contrast) does not obviously grow with the trend. If you tried this on the solar data you would see the assumption fail badly.

The linear OLS fit on the trend — `smf.ols("trend ~ months", data=data).fit()` — uses ordinary least squares on the moving-average trend rather than on the raw series. This is intentional: the moving average has already removed the seasonal variation, so the regression is not confounded by it. The explanatory variable `months` is a simple integer index, so the fitted coefficient $\hat\beta_1$ has units of °C per month. Multiplying by 12 converts to an annual rate. The result (approximately 0.041 °C per year over 2000–2024) is a descriptive estimate, not a causal inference — it captures whatever combination of anthropogenic forcing, natural variability, and local measurement effects operated over this window.

Two subtleties are worth flagging. First, the moving average leaves `NaN` values at both ends of the trend series (six months at each end for a 12-month window), so `.dropna()` is necessary before fitting. Second, the $R^2$ from regressing on the moving-average trend is not the same as the $R^2$ of the full model against the raw data — the decomposition has already absorbed seasonal variance, so the linear fit is only being judged against residual trend variability.

## Exercise: Multiplicative Decomposition and Quadratic Forecast for Utility-Scale Solar

The choice of `model="multiplicative"` encodes the assumption that the series satisfies

$$y_t = T_t \cdot S_t \cdot \varepsilon_t$$

meaning the seasonal component and the noise are proportional to the level of the trend. Equivalently, $\log y_t = \log T_t + \log S_t + \log \varepsilon_t$, which is an additive model on the log scale. Utility-scale solar grew by roughly an order of magnitude over the training window, so a fixed additive seasonal offset would make no physical sense: a summer surplus of 1 GWh is negligible when total output is 5 GWh but meaningful when it is 50 GWh. The multiplicative model captures this by expressing the seasonal component as a dimensionless ratio (approximately 0.75 in winter, 1.25 in summer) rather than an absolute deviation.

The quadratic trend model, `smf.ols("trend ~ months + I(months**2)", data=data).fit()`, adds a second-order polynomial term. The `I()` wrapper in Patsy is required because `**` in a formula string otherwise denotes a crossing interaction between variables, not exponentiation; `I(months**2)` forces the expression to be evaluated as pure Python, yielding the squared integer. The quadratic fits the accelerating growth phase of solar adoption better than a linear model, which would underestimate recent values. Both the linear and quadratic coefficients are highly significant, confirming that curvature is real in the training window.

Forecasting proceeds by evaluating the fitted polynomial at future integer month indices and multiplying by the average seasonal ratios:

$$\hat{y}_t = \hat{T}(t) \cdot \bar{S}_{m(t)}$$

where $m(t)$ is the calendar month of time $t$ and $\bar{S}_{m}$ is the mean seasonal factor for that month. The MAPE of roughly 10.7% (versus 3.8% for nuclear in the same framework) reflects a fundamental limitation: a polynomial extrapolated beyond its fitting range eventually diverges, and the quadratic underestimates continued near-exponential adoption. The exercise illustrates that model form selection is not just about in-sample fit but about whether the assumed functional form is physically reasonable over the forecast horizon.

## Exercise: SARIMA Specification and Forecasting for Hydroelectric Generation

The SARIMA model fitted here, `order=([1, 6], 0, [6])` with `seasonal_order=(0, 1, 0, 12)`, deserves element-by-element unpacking because each number reflects a modelling decision.

The `seasonal_order=(0, 1, 0, 12)` instructs the model to take one round of seasonal differencing at lag 12, forming $\tilde{y}_t = y_t - y_{t-12}$. This is analogous to year-over-year differencing and removes a seasonal unit root — a pattern where the series in each calendar month follows a random walk rather than reverting to a fixed seasonal level. The differencing stabilises the variance of the seasonal component and is the "I" (integrated) part of the acronym.

The `order=([1, 6], 0, [6])` specifies the non-seasonal AR and MA structure applied to the differenced series. Including lags 1 and 6 in the AR component means the model predicts $\tilde{y}_t$ from the values six months ago and one month ago — plausible for hydroelectric generation, which depends on snowpack and rainfall patterns that carry multi-month memory. The MA lag at 6 models the persistence of forecast errors at a half-year horizon.

The `get_forecast(steps=60)` call uses the fitted state-space representation of the ARIMA model (via a Kalman filter) to propagate the model forward 60 steps. Crucially, the confidence interval widens with the forecast horizon because prediction error variance accumulates: each step adds the one-step-ahead innovation variance $\hat\sigma^2$, so the interval grows roughly as $\sqrt{h}$ for an AR(1)-type process. The `conf_int()` method returns the 95% interval by default, derived from the asymptotic normality of the forecast distribution — an assumption that may be too optimistic if the residuals are fat-tailed or if the model is misspecified.

The `n_missing=24` burn-in period reflects a practical constraint: seasonal differencing consumes 12 observations, and the longest non-seasonal lag (6 in both AR and MA) consumes up to 6 more, leaving the first 18 to 24 fitted values unreliable. Trimming them before computing $R^2$ avoids artificially inflating or deflating the fit statistic due to initialisation artefacts.
