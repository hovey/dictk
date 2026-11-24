# Kernel Size Selection

## Data and Methods Provenance

We copied two speckle images from the `doc-msem` branch of `hdic`, at
`hdic/test_data/test_file.tif` and `hdic/test_data/msem_test_file.tif`.
The table gives each image's name before and after the copy:

<details>
<summary><code>kernel_size_selection_previews.py</code></summary>

```python
<!-- cmdrun cat kernel_size_selection_previews.py -->
```

</details>

```text
<!-- cmdrun python3 kernel_size_selection_previews.py -->
```

| before | after | Preview |
|---|---|---|
| `test_file.tif` | [`sem_steel_silver_speckle.tif`](sem_steel_silver_speckle.tif) | <a href="sem_steel_silver_speckle_preview.png" target="_blank" rel="noopener"><img src="sem_steel_silver_speckle_preview.png" alt="sem_steel_silver_speckle.tif, a 200 by 200 pixel speckle image" /></a> |
| `msem_test_file.tif` | [`msem_titanium_silver_speckle.tif`](msem_titanium_silver_speckle.tif) | <a href="msem_titanium_silver_speckle_preview.png" target="_blank" rel="noopener"><img src="msem_titanium_silver_speckle_preview.png" alt="msem_titanium_silver_speckle.tif, a 200 by 200 pixel speckle image" /></a> |

Click a preview to open it in its own tab.

The methods come from the same branch, at
`hdic/src/hdic/xcorr_quickplot.py` and `hdic/src/hdic/xcorr_pytorch.py`:

<details>
<summary><code>xcorr_quickplot.py</code></summary>

```python
<!-- cmdrun cat xcorr_quickplot.py -->
```

</details>

<details>
<summary><code>xcorr_pytorch.py</code></summary>

```python
<!-- cmdrun cat xcorr_pytorch.py -->
```

</details>

Continue to [Subpixel Accuracy](./subpixel_accuracy.md).
