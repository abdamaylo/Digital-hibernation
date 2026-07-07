# Digital Hibernation: Asymmetric-Cost C-State Selection

**A decision-theoretic framework for processor idle-state selection, validated on real Intel hardware.**

---

## Overview

This project revisits the problem of idle-state selection in modern processors. Existing Linux governors rely on point-estimation, which fails to account for the asymmetric cost of prediction errors. We propose Expected-Cost, a governor that minimizes expected energy over the empirical distribution of recent idle durations.

**Key result:** 28.57% energy savings on real Intel Core i7-7xxx hardware, confirmed by 10 independent runs with RAPL measurements (p < 0.00001).

---

## Repository Structure
