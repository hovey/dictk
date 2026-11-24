"""Write a PNG copy of each of the two speckle images, so any browser
can show them. Prints each saved file name.
"""

from dictk.image import read, write

NAMES = ["sem_steel_silver_speckle", "msem_titanium_silver_speckle"]

for name in NAMES:
    write(arr=read(path=f"{name}.tif"), path=f"{name}_preview.png")
print("Saved: " + ", ".join(f"{name}_preview.png" for name in NAMES))
