# Introduction

`dictk` (Digital Image Correlation Toolkit) is a Python library for digital
image correlation (DIC) — comparing images of a specimen before and after
deformation to measure displacement and strain fields.

## Installation

```bash
pip install dictk
```

## Overview

DIC compares a reference image (often of an undeformed specimen) to a subject image
(often of a deformed specimen) as a means to optically quantify displacement and
strain fields.

Before we discuss the *image* portion of DIC, it is useful to introduce basic
concepts of [Continuum Mechanics](./getting_started/continuum_mechanics.md)
and the [Finite Element Method](./getting_started/finite_element_method.md).
This introduction will formalize definitions of displacement and strain and
lay the groundwork for motion of discrete points locatable in reference/subject image
pairs that are mapped to nodes of a finite element mesh (i.e., *nodes*).

The basic workflow is as follows:

* Collect a pair of before and after images that capture an area of interest.  The *before* image, often called the reference image, captures some (possibly undeformed or deformed) configuration of the specimen.  The *after* image captures the specimen in a newly deformed state, different from the *before* state.
* Within each pair of images, identify points of interest.
* Use the $(X, Y)$ coordinates of the image points as coordinates of nodes that compose a finite element mesh.
* Use DIC to quantify the displacement field of each (nodal) point.
* Use the mesh (nodal) deformation to calculate a discrete strain field at Gauss points.

The following sections explicate this workflow in detail.
