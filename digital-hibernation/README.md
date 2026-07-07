# Digital Hibernation

## Asymmetric-Cost Idle-State Selection for Modern Processors

---

### Overview

This project revisits processor idle-state selection through decision theory. Existing Linux governors (`menu`, `teo`) rely on point-estimation, which fails to account for the asymmetric nature of prediction errors:

- **Under-prediction** (choosing shallow for long idle) → wastes power linearly.
- **Over-prediction** (choosing deep for short idle) → pays transition penalty without benefit.

**Expected-Cost** replaces point-estimation with distribution-aware energy minimization, achieving **28.57% energy savings** on real Intel Core i7-7xxx hardware, confirmed by 10 independent runs with RAPL measurements (p < 0.00001).

---

### Repository Structure
