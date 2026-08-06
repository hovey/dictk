# Introduction

`dictk` (Digital Image Correlation Toolkit) is a Python library for digital
image correlation (DIC) — comparing images of a specimen before and after
deformation to measure displacement and strain fields.

This guide is a work in progress. See the following pages for what dictk
currently provides, starting with generating a synthetic reference image.

## Installation

```bash
pip install dictk
```

## Overview

DIC compares a reference image (often an image of an undeformed specimen) to a subject image
(often of a deformed specimen) as a means to optically quantify strain experienced by a specimen.

Before we embark on the image portion of DIC, it is useful to introduce basic
concepts of [Continuum Mechanics](./getting_started/continuum_mechanics.md)
and the [Finite Element Method](./getting_started/finite_element_method.md).

This introduction will not only formalize definitions of deformation and strain; it will
also lay the groundwork for discrete motion of points in a finite element mesh (i.e., *nodes*), as landmarks to be located (and then correlated) across pairs of a reference and a subject image.
