# Research Note — Neural Dynamical Systems Reference

## Source context

The project owner supplied a low-resolution scientific figure showing an evolution from theory models and discrete neural-network models toward continuous neural dynamical-system models. The figure also presents neural numerical integration, adaptive step-size control, in-memory or analogue computation, and a dedicated hardware system.

The image is retained only as a conceptual reference. It is not included in this repository, its original publication was not established during this checkpoint, and no claim is made that the illustrated method has been implemented here.

## What the figure appears to describe

The visible structure connects several ideas:

1. physical modelling, interaction modelling, planning, and reasoning;
2. transformation of a state through a continuous dynamical system;
3. neural approximation of numerical integration;
4. adaptive integration step sizes controlled by estimated error;
5. acceleration through in-memory, analogue, or specialised hardware.

## Relevance to this lottery project

The figure is technically interesting, but it should not be transferred directly into the current lottery pipeline. Lottery draws are discrete stochastic observations rather than measurements from a known continuous physical system. A continuous neural dynamical model could therefore fit historical structure without establishing a causal or stable forecasting signal.

Possible future experiments are limited to research comparisons:

- compare a continuous-time latent model with the existing discrete feature pipeline;
- enforce strict chronological train/validation/test separation;
- compare against random, frequency, and simple statistical baselines;
- measure calibration and stability across rolling windows;
- reject the method if it does not outperform baselines consistently after costs and multiple-testing controls.

## Decision for Step 143.1

No continuous neural dynamical-system code, adaptive solver, or hardware-specific component is added in this checkpoint. The current project architecture and mathematical logic remain unchanged. The figure is documented as a future research direction requiring an identified primary source, a separate experimental branch, and independent validation.
