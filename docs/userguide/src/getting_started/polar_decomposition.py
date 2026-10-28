#!/usr/bin/env python
import os
import numpy as np

# import matplotlib as mpl
from matplotlib import rc, rcParams
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from abc import ABC


rc("font", **{"family": "serif", "serif": ["Computer Modern Roman"]})
rc("text", usetex=True)
# matplotlib.rcParams['text.latex.preamble']=[r"\usepackage{amsmath}"]
rcParams["text.latex.preamble"] = r"\usepackage{amsmath}"

# Illustration of Model-View-Controller (MVC) and (eventually) RTTI attribution.


# =====
# Model
# =====
class Model(ABC):
    def __init__(self):
        # origin
        self._X0, self._Y0 = 0, 0

    def origin(self):
        return [self._X0, self._Y0]

    @property
    def points(self):
        return [self._X0, self._Y0]

    @points.setter
    def points(self, value):
        self._X0 = value[0]
        self._Y0 = value[1]


class AxisModel(Model):
    def __init__(self, direction=1):
        super().__init__()
        # direction=1 is the x-axis
        # direction=2 is the y-axis
        if direction == 1:
            self._X = np.array([0, 1])
            self._Y = np.array([0, 0])
        else:  # direction is y-axis
            self._X = np.array([0, 0])
            self._Y = np.array([0, 1])

    @property
    def points(self):  # override
        return [self._X, self._Y]

    @points.setter  # override
    def points(self, value):
        self._X0 = value[0][0]  # update the origin x
        self._Y0 = value[1][0]  # update the origin y
        self._X = value[0]
        self._Y = value[1]


class BodyModel(Model):
    def __init__(self, radius=1):
        super().__init__()
        self._NPOINTS = 25
        theta = np.linspace(0.0, 2 * np.pi, self._NPOINTS)  # radians
        self._X = np.array(radius * np.cos(theta))
        self._Y = np.array(radius * np.sin(theta))

    def number_of_points(self):
        return self._NPOINTS

    def perimeter(self):
        return self._X, self._Y

    @property
    def points(self):  # override
        where = 0
        X = np.insert(self._X, where, self._X0, axis=0)
        Y = np.insert(self._Y, where, self._Y0, axis=0)
        return [X, Y]

    @points.setter  # override
    def points(self, value):
        self._X0 = value[0][0]  # update the origin x
        self._Y0 = value[1][0]  # update the origin y
        self._X = value[0][1:]
        self._Y = value[1][1:]


# ====
# View
# ====
class View(ABC):
    def __init__(self):
        self._color = "red"

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value):
        self._color = value


class AxisView(View):
    def __init__(self, model, axis, color="blue"):
        super().__init__()
        self._color = color
        self._color_origin = "black"
        x, y = model.points
        axis.plot(
            x, y, "-", marker="o", color=self._color, markevery=[-1]
        )  # plot the x-axis or y-axis, depending on model

        x0, y0 = model.origin()
        axis.plot(x0, y0, "o", color=self._color_origin)


class BodyView(View):
    def __init__(self, model, axis, color="magenta"):
        super().__init__()
        self._color = color
        self._fs = "none"  # fillstyle
        self._linealpha = 0.5
        x0, y0 = model.origin()
        x, y = model.perimeter()

        axis.plot(x, y, "-", color=self._color)  # boundary
        axis.plot(
            x, y, "o", color=self._color, fillstyle=self._fs, alpha=self._linealpha
        )  # boundary
        axis.plot(
            [x0, x[0]],
            [y0, y[0]],
            "o-",
            color="red",
            fillstyle=self._fs,
            markevery=[-1],
        )  # tracking line on original x-axis
        y_axis_index = int((model.number_of_points() - 1) / 4)
        axis.plot(
            [x0, x[y_axis_index]],
            [y0, y[y_axis_index]],
            "o-",
            color="green",
            fillstyle=self._fs,
            markevery=[-1],
        )  # tracking line on original y-axis
        axis.plot(x0, y0, "o", color="black", fillstyle=self._fs)  # body origin


# ===========
# Controllers
# ===========
def offset(points, offsets=[0, 0]):
    """Given a list of reference points [X, Y], offset them in
    the x-axis and the y-axis.
    """
    # x = X + offset_x
    # y = Y + offset_y
    # return x, y
    x = points[0] + offsets[0]
    y = points[1] + offsets[1]
    return [x, y]


def simple_shear(points, shear_12=0):
    """Given a list of reference points [X, Y], simple shear them in
    the x-axis by distance shear_x (Length) to the current points [x, y].
    """
    # x = X + shear_12 * Y
    # y = Y
    # return x, y
    x = points[0] + shear_12 * points[1]
    y = points[1]
    return [x, y]


def rotate(points, angle=0):
    """Given list of reference points [X, Y], rotate them about the
    z-axis by angle R (radians) to the current points [x, y].
    """
    # x = np.cos(R) * X - np.sin(R) * Y
    # y = np.sin(R) * X + np.cos(R) * Y
    X = points[0]
    Y = points[1]
    x = np.cos(angle) * X - np.sin(angle) * Y
    y = np.sin(angle) * X + np.cos(angle) * Y
    return [x, y]


def stretch(points, stretches=[1, 1]):
    """Given a list of reference points [X, Y], simple stretch j
    by factor stretches[0] in the x-direction and
    by factor stretches[1] in the y-direction
    to the current points [x, y].
    """
    x = stretches[0] * points[0]
    y = stretches[1] * points[1]
    return [x, y]


# ======
# client
# ======
fig = plt.figure(figsize=(6, 6))  # inches, (wide, tall)
ax = fig.add_subplot(1, 1, 1)

RADTODEG = 180.0 / np.pi
DEGTORAD = 1.0 / RADTODEG


def text(x, y, text):
    ax.text(
        x,
        y,
        text,
        backgroundcolor="white",
        ha="center",
        va="center_baseline",
        weight="bold",
        color="black",
    )


# xaxis = AxisModel(direction=1)  # create
# p = xaxis.points  # read
# o = [-7, -7]  # offset
# xaxis.points = offset(p, o)  # update
# gb = AxisView(xaxis, ax, 'red')  # view
# text(o[0] - 0.5, o[1] - 0.5, '$o$')
# text(o[0] + 2.25, o[1], '$X_1, x_1$')
#
# yaxis = AxisModel(direction=2)  # create
# p = yaxis.points  # read
# yaxis.points = offset(p, o)  # update
# gb = AxisView(yaxis, ax, 'green')  # view
# text(o[0], o[1] + 1.75, '$X_2, x_2$')

# horizontal and vertical dividing lines
edge = 8
ax.plot([-edge, edge], [0, 0], "--", linewidth=1, color="dimgray")
ax.plot([0, 0], [-edge, edge], "--", linewidth=1, color="dimgray")

b1 = BodyModel(radius=2)  # create
c = 4  # notational origin (center) for each of the four plots
m = c + 3  # motional origin plus margin
inner = 1.5  # inner margin position
o = [-c, c]  # offset
b1.points = offset(b1.points, o)  # read then update
gb = BodyView(b1, ax, "black")  # view

# stretch U
b2 = BodyModel(radius=2)  # create
s = [1.5, 0.5]  # stretches
b2.points = stretch(b2.points, s)  # read then update
o = [c, c]  # offset
b2.points = offset(b2.points, o)  # read then update
gb = BodyView(b2, ax, "black")  # view
# ap = dict(arrowstyle='->, head_width=0.4, head_length=0.8', shrinkA=0, shrinkB=0) # arrow properites
ap = dict(arrowstyle="->")  # arrow properites
ax.annotate("", xy=(b2.origin()[0], m), xytext=(b1.origin()[0], m), arrowprops=ap)
text(0, m, "stretch \sffamily \\bfseries U")
# https://tex.stackexchange.com/questions/7669/bfseries-is-to-textbf-as-what-is-to-textsf/7670

# rotate R
r = 30 * DEGTORAD  # radians
b3 = BodyModel(radius=2)  # create
b3.points = rotate(b3.points, r)  # read then update
o = [-c, -c]  # offset
b3.points = offset(b3.points, o)  # read then update
gb = BodyView(b3, ax, "black")  # view
# ax.annotate('', xy=(-m, b3.origin()[1]), xytext=(-m, b1.origin()[1]), arrowprops=ap)
ax.annotate(
    "", xy=(b1.origin()[0], -inner), xytext=(b1.origin()[0], inner), arrowprops=ap
)
rscale = 0.9
# text(-rscale*m, 0, 'rotation \sffamily \\bfseries R')
text(b1.origin()[0], 0, "rotation \sffamily \\bfseries R")

# F = RU
b4 = BodyModel(radius=2)  # create
s = [1.5, 0.5]  # stretches
b4.points = stretch(b4.points, s)  # read then update
b4.points = rotate(b4.points, r)  # read then update
o = [c, -c]  # offset
b4.points = offset(b4.points, o)  # read then update
gb = BodyView(b4, ax, "black")  # view

ax.annotate("", xy=(b4.origin()[0], -m), xytext=(b3.origin()[0], -m), arrowprops=ap)
text(0, -m, "stretch \sffamily \\bfseries v")

# ax.annotate('', xy=(m, b4.origin()[1]), xytext=(m, b2.origin()[1]), arrowprops=ap)
# text(rscale*m, 0, 'rotation \sffamily \\bfseries R')
ax.annotate(
    "", xy=(b2.origin()[0], -inner), xytext=(b2.origin()[0], inner), arrowprops=ap
)
# text(-rscale*m, 0, 'rotation \sffamily \\bfseries R')
text(b2.origin()[0], 0, "rotation \sffamily \\bfseries R")

ax.annotate("", xy=(inner, -inner), xytext=(-inner, inner), arrowprops=ap)
text(0, 0, "\sffamily \\bfseries F")

ax.axis("equal")

# major axes
ax.xaxis.set_major_locator(MultipleLocator(1.0))
ax.yaxis.set_major_locator(MultipleLocator(1.0))
# ax.grid(b=True, which='major', linestyle=':')
ax.grid(
    visible=True, which="major", linestyle="solid", linewidth=0.5, color="lightgray"
)

# minor axes
# no operations

ax.set_xlabel(r"$X_1, x_1$")
ax.set_ylabel(r"$X_2, x_2$")
ax.set_xlim(-edge, edge)
ax.set_ylim(-edge, edge)
# ax.legend(loc='lower right', framealpha=1.0)

ax.set_xticklabels(["", "", -3, -2, -1, 0, 1, 2, 3, "", -3, -2, -1, 0, 1, 2, 3])
ax.set_yticklabels(["", "", -3, -2, -1, 0, 1, 2, 3, "", -3, -2, -1, 0, 1, 2, 3])

text(-edge + 1, edge - 1, "(a)")
text(edge - 1, edge - 1, "(b)")
text(-edge + 1, -edge + 1, "(c)")
text(edge - 1, -edge + 1, "(d)")

ax.text(
    b1.origin()[0] - 0.55, b1.origin()[1] - 0.55, "$\\boldsymbol{X}$"
)  # no white background
ax.text(b4.origin()[0] - 0.5, b4.origin()[1] - 0.5, "$\\boldsymbol{x}$")


# fig.tight_layout()
script_name = os.path.basename(__file__)
figure_name = os.path.splitext(script_name)[0]
print(f"Saving figure as {figure_name}.png")
fig.savefig(figure_name + ".png", bbox_inches="tight", dpi=200)
