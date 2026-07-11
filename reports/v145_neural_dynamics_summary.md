# Step 145 — Experimental Neural Dynamics Sandbox

- Experiment ID: `EXP-145-0e11bccbcb-f2843280b3`
- Dataset SHA-256: `0e11bccbcb47ae6d34f32c5e791ca76cf199aca2ebefe77798c16ab4b4fbc579`
- Latest draw: **2026-53**
- Initial training draws: **9823**
- Holdout draws: **240**
- Package size: **12** combinations
- Random trials: **50**
- Seed: **1452026**

## Architecture

- Model: `continuous_time_inspired_leaky_reservoir_with_online_ridge_readout`
- State equation: `h_t=(1-leak)h_(t-1)+leak*tanh(W_in*x_t+W_rec*h_(t-1)+b)`
- Reservoir size: **32**
- Actual spectral radius: **0.82**
- Production integration: **No**

## Historical holdout results

- Neural dynamics average best hits: **1.987500**
- Frequency baseline average best hits: **2.075000**
- Recency baseline average best hits: **2.054167**
- Uniform-random mean average best hits: **2.080333**
- Neural minus frequency: **-0.087500**
- Neural minus recency: **-0.066667**
- Neural minus random mean: **-0.092833**
- Empirical p-value versus random trials: **1.000000**
- Promotion gate passed: **No**

## Reproducibility

- Configuration hash: `f2843280b3384c5130b5bee2dacfcd4340cb1e9c8459959920af897d0eff953d`
- Code hash: `7145ba895f27c069591c34db896676fe939234e1b4137b5a7df8edd106bcc1d8`
- Result signature: `efcfc98d7674ddadf81443cb8cd35264b07913075f262ee5821b7ef77c38901f`
- Command: `python tools/run_experimental_neural_dynamics.py --holdout-draws 240 --minimum-training-draws 500 --package-size 12 --random-trials 50 --frequency-pool-size 49 --recency-decay 0.985 --reservoir-size 32 --leak-rate 0.28 --spectral-radius 0.82 --input-scale 0.65 --bias-scale 0.05 --ridge-alpha 12.0 --score-power 1.4 --seed 1452026`

## Conclusion

The neural-dynamics sandbox did not pass the promotion gate on this historical holdout. It remains research-only and is not connected to ticket generation.

Това е изолиран исторически sandbox експеримент. Neural-dynamics моделът не е включен в production pipeline, не създава реални фишове и не доказва предвидимост на бъдещи случайни тиражи.
