# Finite Element Method

A finite element mesh is a collection of **nodes** (points) connected into
**elements** — small regions used to interpolate a quantity of interest
(e.g. displacement) across the whole domain. The point grid built in
[Multi-Point Motion](./multi_point_motion.md#point-grid) is exactly the
kind of nodal point collection a mesh needs, and [Tracking the
Grid](./multi_point_motion.md#tracking-the-grid) already found every one
of its 12 points' current positions — exactly the per-node displacement
data a mesh needs to represent how an object deformed.

[Tracking the Grid](./multi_point_motion.md#tracking-the-grid) already
covers the kernel-size-versus-point-spacing tradeoff involved in getting
that per-node data reliably — the same considerations apply whether the
points come from a toy grid or a real mesh.

Once every node's current position is known, an actual finite element
mesh still needs one more thing this page doesn't provide: **element
connectivity** — which nodes join together into which elements. Building
that connectivity is future work, not implemented here; the element
formulation connectivity would plug into — shape functions, strain, and
deformation gradient, for the four-node quadrilateral element — is what
this page covers below.

## Four-Noded Quadrilateral Finite Element (Q4)

The four-node quadrilateral element is one of the most commonly used elements in 2D FEA. It has four corner nodes, with each node having two degrees of freedom (DOFs): displacements in the $x$ and $y$ directions.

<figure class="figure-box">
    <img src="quad_isoparametric.png" alt="quad_isoparametric" width=100% />
    <figcaption>
        Figure:  Illustration of isoparameteric mapping between (left) an arbitrary quadrilateral element in global (physical) coordinates to (right) the local (natural) coordinates.  The local domain is sometimes called the parent quadrilateral element.  
    </figcaption>
</figure>

Image credit: James *et al.*[^James_2012]

### Shape Functions

For the element in local coordinates $(\xi, \eta) \in [−1, 1] \times [−1,1]$, the bilinear shape functions are defined:

$$
\begin{align}
N_1(\xi, \eta) &:= \frac{1}{4}(1-\xi)(1-\eta) \\
N_2(\xi, \eta) &:= \frac{1}{4}(1+\xi)(1-\eta) \\
N_3(\xi, \eta) &:= \frac{1}{4}(1+\xi)(1+\eta) \\
N_4(\xi, \eta) &:= \frac{1}{4}(1-\xi)(1+\eta)
\end{align}
$$

The shape functions satisfy the following properties:

* Kronecker delta property: $N_a(\xi_b,\eta_b) = \delta_{ab}$ (equals 1 at node $a$, 0 at other nodes)
* Partition of unity: $\sum_{a=1}^4 N_a (\xi , \eta) = 1$ for all $(\xi, \eta)$

### Local Coordinates

The key concept in finite element analysis is the **isoparametric mapping** between the local coordinate system and the global coordinate system.

This mapping allows:
- Integration to be performed on the local domain (parent element)
- Handling of arbitrarily shaped quadrilaterals
- Use of the same shape functions for geometry and displacement (isoparametric concept)

The isoparametric coordinates $(\xi, \eta)$ range from $-1$ to $+1$ in both the $x$ and $y$ directions. 

The mapping between global coordinates $(x, y)$ and local coordinates is introduced as a linear combination of local shape functions $N_{\rm node}(\boldsymbol{x})$:

$$
\boldsymbol{x}(\boldsymbol{\xi}) = 
\begin{Bmatrix}
x(\xi, \eta) \\
y(\xi, \eta)
\end{Bmatrix}
= \sum_{a=1}^{4} N_a(\boldsymbol{\xi}) \boldsymbol{x}_a
= \sum_{a=1}^{4} N_a(\xi, \eta)
\begin{Bmatrix}
x_a \\
y_a
\end{Bmatrix}
$$

where $(x_a, y_a)$ is the position of node $a$, and $a = 1 \ldots 4$.

### Shape Function Derivatives in Local Coordinates

The derivatives with respect to the local coordinate system are

$$
\frac{\partial N_a(\xi, \eta)}{\partial \xi} = \frac{1}{4}
\begin{bmatrix}
-(1-\eta) \\
(1-\eta) \\
(1+\eta) \\
-(1+\eta)
\end{bmatrix}, \quad
\frac{\partial N_a(\xi, \eta)}{\partial \eta} = \frac{1}{4}
\begin{bmatrix}
-(1-\xi) \\
-(1+\xi) \\
(1+\xi) \\
(1-\xi)
\end{bmatrix}
$$

These are assembled into a $2 \times 4$ matrix:

$$
\frac{\partial \boldsymbol{N(\boldsymbol{\xi})}}{\partial \boldsymbol{\xi}} =
\begin{bmatrix}
\frac{\partial N_1}{\partial \xi} & \frac{\partial N_2}{\partial \xi} & \frac{\partial N_3}{\partial \xi} & \frac{\partial N_4}{\partial \xi} \\[1em]
\frac{\partial N_1}{\partial \eta} & \frac{\partial N_2}{\partial \eta} & \frac{\partial N_3}{\partial \eta} & \frac{\partial N_4}{\partial \eta}
\end{bmatrix}_{2 \times 4}
$$

### Jacobian Matrix

The Jacobian matrix relates derivatives in local coordinates to derivatives in global coordinates.  For nodal coordinates organized as:

$$
\boldsymbol{x} = 
\begin{bmatrix}
x_1 & y_1 \\
x_2 & y_2 \\
x_3 & y_3 \\
x_4 & y_4
\end{bmatrix}_{4 \times 2}
$$

the Jacobian is computed as:

$$
\boldsymbol{J}(\boldsymbol{\xi}) := \frac{\partial \boldsymbol{x}(\boldsymbol{\xi})}{\partial \boldsymbol{\xi}} 
= \begin{bmatrix}
\frac{\partial x}{\partial \xi} & \frac{\partial y}{\partial \xi} \\[1em]
\frac{\partial x}{\partial \eta} & \frac{\partial y}{\partial \eta}
\end{bmatrix}_{2 \times 2}
= \frac{\partial \boldsymbol{N}(\boldsymbol \xi)}{\partial \boldsymbol{\xi}} \cdot \boldsymbol{x} 
$$ 

The individual components are:

$$
\begin{align}
J_{11} &= \frac{\partial x}{\partial \xi} = \sum_{a=1}^{4} \frac{\partial N_a}{\partial \xi} x_a \\[1em]
J_{12} &= \frac{\partial y}{\partial \xi} = \sum_{a=1}^{4} \frac{\partial N_a}{\partial \xi} y_a \\[1em]
J_{21} &= \frac{\partial x}{\partial \eta} = \sum_{a=1}^{4} \frac{\partial N_a}{\partial \eta} x_a \\[1em]
J_{22} &= \frac{\partial y}{\partial \eta} = \sum_{a=1}^{4} \frac{\partial N_a}{\partial \eta} y_a
\end{align}
$$

### Shape Function Derivatives in Global Coordinates

The transformation from local to global coordinate derivatives requires the inverse Jacobian through the chain rule.
Since

$$
\frac{\partial N_a}{\partial x} = 
\frac{\partial N_a}{\partial \xi} \frac{\partial \xi}{\partial x}
+
\frac{\partial N_a}{\partial \eta} \frac{\partial \eta}{\partial x}
$$

$$
\frac{\partial N_a}{\partial y} = 
\frac{\partial N_a}{\partial \xi} \frac{\partial \xi}{\partial y}
+
\frac{\partial N_a}{\partial \eta} \frac{\partial \eta}{\partial y}
$$

then

$$
\begin{bmatrix}
\frac{\partial N_a}{\partial x} \\[1em]
\frac{\partial N_a}{\partial y}
\end{bmatrix}
=
\begin{bmatrix}
\frac{\partial \xi}{\partial x} & \frac{\partial \eta}{\partial x} \\[1em]
\frac{\partial \xi}{\partial y} & \frac{\partial \eta}{\partial y}
\end{bmatrix}_{2 \times 2}
\begin{bmatrix}
\frac{\partial N_a}{\partial \xi} \\[1em]
\frac{\partial N_a}{\partial \eta}
\end{bmatrix}
= \boldsymbol{J}^{-1}(\boldsymbol{x})
\begin{bmatrix}
\frac{\partial N_a}{\partial \xi} \\[1em]
\frac{\partial N_a}{\partial \eta}
\end{bmatrix}
$$

In matrix form for all shape functions:

$$
\frac{\partial \boldsymbol{N}}{\partial \boldsymbol{x}} = \boldsymbol{J}^{-1} \cdot \frac{\partial \boldsymbol{N}}{\partial \boldsymbol{\xi}}
$$

where:

$$
\frac{\partial \boldsymbol{N}}{\partial \boldsymbol{x}} = 
\begin{bmatrix}
\frac{\partial N_1}{\partial x} & \frac{\partial N_2}{\partial x} & \frac{\partial N_3}{\partial x} & \frac{\partial N_4}{\partial x} \\[0.5em]
\frac{\partial N_1}{\partial y} & \frac{\partial N_2}{\partial y} & \frac{\partial N_3}{\partial y} & \frac{\partial N_4}{\partial y}
\end{bmatrix}_{2 \times 4}
$$

### Displacement Field

The displacement $\boldsymbol{u}(\boldsymbol{x})$ is defined as the difference between the current configuration $\boldsymbol{\varphi}(\boldsymbol{x})$ and the reference configuration $\boldsymbol{x}$,

$$
\boldsymbol{u}(\boldsymbol{x}) :=
\boldsymbol{\varphi}(\boldsymbol{x}) - \boldsymbol{x}
$$

The displacement field within the element is interpolated using shape functions:

$$
\boldsymbol{u}(\xi, \eta) = 
\begin{Bmatrix}
u(\xi, \eta) \\
v(\xi, \eta)
\end{Bmatrix}
= \sum_{a=1}^{4} N_a(\boldsymbol{\xi}) \boldsymbol{u}_a
= \sum_{a=1}^{4} N_a(\xi, \eta)
\begin{Bmatrix}
u_a \\
v_a
\end{Bmatrix}
$$

where $(u_a, v_a)$ is the respective $(x, y)$ displacement of node $a$, and $a = 1 \ldots 4$.

### Displacement Gradient

$$\nabla\boldsymbol{u}(\boldsymbol{x}) =
\begin{bmatrix}
\frac{\partial u}{\partial x} & \frac{\partial u}{\partial y} \\[1em]
\frac{\partial v}{\partial x} & \frac{\partial v}{\partial y}
\end{bmatrix}_{2 \times 2}
$$

Each component is computed using the chain rule:

$$
\begin{align}
\frac{\partial u}{\partial x} &= \sum_{a=1}^{4} \frac{\partial N_a}{\partial x} u_a \\[1em]
\frac{\partial u}{\partial y} &= \sum_{a=1}^{4} \frac{\partial N_a}{\partial y} u_a \\[1em]
\frac{\partial v}{\partial x} &= \sum_{a=1}^{4} \frac{\partial N_a}{\partial x} v_a \\[1em]
\frac{\partial v}{\partial y} &= \sum_{a=1}^{4} \frac{\partial N_a}{\partial y} v_a
\end{align}
$$

In compact matrix notation:

$$\nabla \boldsymbol{u} = \left( \frac{\partial \boldsymbol{N}}{\partial \boldsymbol{x}} \cdot \boldsymbol{u} \right)^T
$$

where $\boldsymbol{u}$ is the nodal displacement matrix:

$$
\boldsymbol{u} = 
\begin{bmatrix}
u_1 & v_1 \\
u_2 & v_2 \\
u_3 & v_3 \\
u_4 & v_4
\end{bmatrix}_{4 \times 2}
$$

### Deformation Gradient

The deformation gradient tensor $\boldsymbol{F}(\boldsymbol{x})$ maps material points in the reference configuration $\boldsymbol{x}$ to their positions in the current (deformed) configuration $\boldsymbol{\varphi}$:

$$
\boldsymbol{F}(\boldsymbol{x}) := \frac{\partial \boldsymbol{\varphi}(\boldsymbol{x})}{\partial \boldsymbol{x}}
$$

Because $\boldsymbol{u}(\boldsymbol{x})= \boldsymbol{\varphi}(\boldsymbol{x}) - \boldsymbol{x}$, 

$$
\nabla \boldsymbol{u} = \boldsymbol{F} - \boldsymbol{I} \quad \implies \quad 
\boldsymbol{F} =
\nabla \boldsymbol{u} + \boldsymbol{I}
$$

Explicitly:

$$
\boldsymbol{F}
= 
\begin{bmatrix}
F_{11} & F_{12} \\[0.5em]
F_{21} & F_{22}
\end{bmatrix}
=
\begin{bmatrix}
\frac{\partial u}{\partial x} + 1 & \frac{\partial u}{\partial y} \\[0.5em]
\frac{\partial v}{\partial x} & \frac{\partial v}{\partial y} + 1
\end{bmatrix}
$$

The determinant $J_0=\det(\boldsymbol{F})$
represents the local volume ratio and must be positive for physically admissible deformations.

### Gauss Points

To evaluate strain, we use **Gaussian Quadrature**.  We don't typically calculate strain
at the nodes.  Rather, we evaluate strain at specific *integration points* (also known as **Gauss points**) where mathematical precision is the highest.

For a 2D quadrilateral element, we typically use a $2 \times 2$ Gauss rule.  The integration points are located in the local coordinate system $(\xi, \eta)$ at

$$
\xi, \eta \in \left\{\pm \frac{1}{\sqrt{3}} \right\} \approx \pm 0.57735
$$

## References

[^James_2012]: James KA, Lee E, Martins JR. Stress-based topology optimization using an isoparametric level set method. Finite Elements in Analysis and Design. 2012 Oct 1;58:20-30. [link](https://doi.org/10.1016/j.finel.2012.03.012)
