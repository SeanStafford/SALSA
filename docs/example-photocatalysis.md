# Example Application: Photocatalytic Water-Splitting

This document describes how SALSA was applied to discover semiconductor materials for artificial photosynthesis, as published in Stafford et al. (2023). This concrete example illustrates how the general SALSA workflow operates.

## Problem Definition

Photocatalytic water-splitting requires a semiconductor that can:

1. **Absorb sunlight efficiently** - Band gap in the 1.23-2.80 eV range (visible/near-UV)
2. **Resist reduction** - Reduction potential < 0.0 V vs NHE (stable photocathode)
3. **Resist oxidation** - Oxidation potential > 1.23 V vs NHE (stable photoanode)
4. **Be cost-effective** - Composed of Earth-abundant elements

No known material simultaneously satisfies all four criteria.

## SALSA Configuration

### Initial Dataset

34 binary semiconductors with experimentally known band gaps and computationally derived redox potentials. Examples:

| Compound | Band Gap (eV) | Oxidation (V) | Reduction (V) |
|----------|---------------|---------------|---------------|
| AgBr     | 2.89          | 2.16          | 0.07          |
| TiO2     | 3.00          | 1.75          | -0.83         |
| PbSe     | 0.27          | 0.76          | -0.61         |
| Ag2Te    | 0.17          | 1.38          | -0.74         |

Note that each compound fails at least one criterion - AgBr and TiO2 have band gaps too high, while PbSe and Ag2Te have band gaps too low.

### Target Property Space

```
Band gap:           1.03 - 3.00 eV
Oxidation potential: > 1.03 V
Reduction potential: < 0.20 V
```

The 0.2 eV/V tolerance beyond ideal bounds accounts for interpolation error.

### Substitution Parameters

- **Threshold:** 0 (only positive likelihood substitutions)
- **Order:** Up to second-order (producing ternary and quaternary compounds)
- **Unit cell limit:** 20 atoms maximum

## Workflow Execution

### Stage 1: Substitution

Generated millions of candidate compositions by swapping ionic components between known compounds using the substitution likelihood matrix.

### Stage 2: Approximation

Filtered to ~13,600 compositions compatible with the interpolation scheme. Of these:
- ~1,250 fell within the target property region
- ~484 fell within the ideal region

Key insight: Most successful interpolations paired high-bandgap/high-oxidation compounds (AgBr, AgCl, TiO2, CuCl) with low-bandgap compounds (Ag2Te, Ag2Se, PbSe, PbTe).

### Stage 3: Evolutionary Search (USPEX)

USPEX converged stable crystal structures for ~50 hybrid compositions. Settings:
- DFT code: VASP (GGA-PBE functional)
- Plane-wave cutoff: 500 eV
- Force convergence: 0.02 eV/A

### Stage 4: Ab-initio (CRYSTAL)

Higher-fidelity calculations with HSE06 hybrid functional refined band gaps and eliminated unstable candidates.

## Results

Several novel semiconductors with properties in the target region:

| Compound       | Band Gap (eV) | Oxidation (V) | Reduction (V) | Space Group |
|----------------|---------------|---------------|---------------|-------------|
| Ti2O4Pb3Se3    | 2.33          | 1.26          | -0.72         | P1          |
| PbCuSeCl       | 1.51          | 1.23          | -0.25         | P3m1 (156)  |
| Ag4Br2S        | 2.74          | 1.45          | 0.01          | P1          |

PbCuSeCl is notable for having a space group (156) different from either parent compound - a structure that traditional substitution-only approaches would not have discovered.

## Lessons for Other Applications

This application demonstrates several general principles:

1. **Complementary parents** - The best candidates came from interpolating between compounds with complementary strengths (e.g., one with good oxidation potential, one with good band gap)

2. **Property space geometry** - Understanding how initial compounds distribute in property space guides which interpolations are worth exploring

3. **Tolerance margins** - Including tolerance beyond ideal bounds prevents false negatives from interpolation error

4. **Structure prediction value** - USPEX found structures with different symmetry than parent compounds, expanding the search beyond simple substitution

## Reference

> Stafford, S.M., Aduenko, A., Djokic, M., Lin, Y.-H., & Mendoza-Cortes, J.L.
> "Transforming Materials Discovery for Artificial Photosynthesis: High-Throughput
> Screening of Earth-Abundant Semiconductors."
> *Journal of Applied Physics* **134**, 235706 (2023). [DOI: 10.1063/5.0178907](https://doi.org/10.1063/5.0178907)
