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

* Collect a **pair** of **before** and **after** images that capture an area of interest.
  * The *before* image, often called the reference image, captures some (possibly undeformed or deformed) configuration of the specimen.  
  * The *after* image, often called the current image or subject image, captures the specimen in a newly deformed state, different from the *before* state.
* Within each pair of images, identify points of interest.
* Use the $(X, Y)$ coordinates of the image points as coordinates of nodes that compose a finite element mesh.
* Use DIC to quantify the displacement field of each (nodal) point.
* Use the mesh (nodal) deformation to calculate a discrete strain field at Gauss points.

The following sections explicate this workflow in detail.

## Literature Overview

Sutton, Orteu, and Schreier provide the field's most comprehensive reference text: basic image-correlation and computer-vision theory, camera calibration and optics, two-dimensional, stereo, and volumetric correlation methods, and the continuum-mechanics, statistics, and optimization background needed to apply them all.[^Sutton_2009] For a shorter, more recent introduction alongside an annotated bibliography of the field, see Brown.[^Brown_2025] The development of modern Digital Image Correlation (DIC) spans from specialized hardware acquisition to advanced mathematical frameworks and open-source implementations. For high-resolution SEM imaging, Lenthe et al. describe advanced detector signal acquisition and scanning methods,[^Lenthe_2018] while Black et al. demonstrate high-throughput measurements using multi-beam SEM imaging.[^Black_2023] When dealing with plastic localization, the Heaviside-DIC approach offers a robust method for capturing discontinuities.[^Bourdin_2018]

Mathematical foundations for the DICe engine are established through the work of Turner, covering gradient-based local formulations,[^Turner_2016] stereo correlation and triangulation,[^Turner_2017] and the implementation of virtual strain gauges.[^Turner_2018] Alternatively, the Augmented Lagrangian DIC (ALDIC) framework provides a global approach to displacement fields, available as both a theoretical framework[^Yang_2019] and a MATLAB implementation.[^Yang_2018] For complex geometries and large deformations, the SpatioTemporally Adaptive Quadtree (STAQ) mesh offers significant improvements in resolution.[^Yang_2022]

Software accessibility is primarily supported by the µDIC toolkit, an open-source Python library for DIC tasks.[^Olufsen_2020] The project's evolution is tracked through specific version forks,[^Olufsen_2020b] comprehensive online documentation, and its primary repository.[^Olufsen_2025] Finally, looking toward performance optimization, the Rust GPU project provides the infrastructure for hardware-accelerated computations that could benefit future DIC processing pipelines.[^Rust_2025]

## References

[^Black_2023]: Black RL, Garbowski T, Bean C, Eberle AL, Nickell S, Texier D, Valle V, Stinville JC. High-throughput high-resolution digital image correlation measurements by multi-beam SEM imaging. Experimental Mechanics. 2023 Jun;63(5):939-53. [link](https://doi.org/10.1007/s11340-023-00961-y)

[^Bourdin_2018]: Bourdin F, Stinville JC, Echlin MP, Callahan PG, Lenthe WC, Torbet CJ, Texier D, Bridier F, Cormier J, Villechaise P, Pollock TM. Measurements of plastic localization by heaviside-digital image correlation. Acta Materialia. 2018 Sep 15;157:307-25. [link](https://doi.org/10.1016/j.actamat.2018.07.013)

[^Brown_2025]: Brown C. Introduction to Digital Image Correlation (DIC) with annotated bibliography. Lawrence Livermore National Laboratory. 2025 Dec. LLNL-TR-2013494. [link](https://www.osti.gov/servlets/purl/3008384)

[^Lenthe_2018]: Lenthe WC, Stinville JC, Echlin MP, Chen Z, Daly S, Pollock TM. Advanced detector signal acquisition and electron beam scanning for high resolution SEM imaging. Ultramicroscopy. 2018 Dec 1;195:93-100. [link](https://doi.org/10.1016/j.ultramic.2018.08.025)

[^Olufsen_2020]: Olufsen SN, Andersen ME, Fagerholt E. μDIC: An open-source toolkit for digital image correlation. SoftwareX. 2020 Jan 1;11:100391. [link](https://www.sciencedirect.com/science/article/pii/S2352711019301967)

[^Olufsen_2020b]: Olufsen SN. Fork: µDIC: A Python toolkit for Digital Image Correlation (DIC), GitHub: https://github.com/ElsevierSoftwareX/SOFTX_2019_193 [link](https://github.com/ElsevierSoftwareX/SOFTX_2019_193) fork of https://github.com/PolymerGuy/muDIC for the 2020 paper.

[^Olufsen_2025]: Olufsen SN. docs for µDIC: A toolkit for digital image correlation, [docs](https://mudic.readthedocs.io/en/latest/) and [repo](https://github.com/PolymerGuy/muDIC)

[^Rust_2025]: Rust GPU https://rust-gpu.github.io/ and https://github.com/rust-gpu/rust-gpu

[^Sutton_2009]: Sutton MA, Orteu JJ, Schreier HW. Image Correlation for Shape, Motion and Deformation Measurements: Basic Concepts, Theory and Applications. Springer; 2009. ISBN 978-0-387-78746-6. [link](https://doi.org/10.1007/978-0-387-78747-3)

[^Turner_2016]: Turner DZ. An overview of the gradient-based local DIC formulation for motion estimation in DICe. 2016 Aug 19. SAND2016-7360R. [link](https://github.com/dicengine/dice/blob/5ebcdfafad1d0ac4ed120ebc1a3fe04138216d5b/doc/reports/LocalGradientAlgorithm.pdf)

[^Turner_2017]: Turner DZ. An overview of the stereo correlation and triangulation formulations used in DICe. 2017 Mar 10. SAND2017-1876R. [link](https://github.com/dicengine/dice/blob/5ebcdfafad1d0ac4ed120ebc1a3fe04138216d5b/doc/reports/Triangulation.pdf)

[^Turner_2018]: Turner DZ. An overview of the virtual strain gauge formulation in DICe. 2018 May 21. SAND2018-5463R. [link](https://github.com/dicengine/dice/blob/5ebcdfafad1d0ac4ed120ebc1a3fe04138216d5b/doc/reports/VirtualStrainGauge.pdf)

[^Yang_2018]: Augmented Lagrangian Digital Image Correlation (2D_ALDIC) MATLAB code. [link](https://www.mathworks.com/matlabcentral/fileexchange/70499-augmented-lagrangian-digital-image-correlation-and-tracking)

[^Yang_2019]: Yang J, Bhattacharya K. Augmented Lagrangian digital image correlation. Experimental Mechanics. 2019 Feb 15;59:187-205. [link](https://link.springer.com/content/pdf/10.1007/s11340-018-00457-0.pdf)

[^Yang_2022]: Yang J, Rubino V, Ma Z, Tao J, Yin Y, McGhee A, Pan W, Franck C. SpatioTemporally adaptive quadtree mesh (STAQ) digital image correlation for resolving large deformations around complex geometries and discontinuities. Experimental Mechanics. 2022 Sep;62(7):1191-215. [link](https://link.springer.com/content/pdf/10.1007/s11340-022-00872-4.pdf)
