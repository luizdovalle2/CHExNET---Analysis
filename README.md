# CHExNET---Analysis

Code used for paper *CHExNet: A 400-years Multilayer Network of Early Modern Collaboration at the Jagiellonian University*.

WORK IN PROGRESS, NOTEBOOK ON SOCIAL CONTAGION FORTHCOMING

## Data download (required)

1. Download the dataset from Zenodo:

   **CHExNet: A network of collaborators in early modern Jagiellonian University**  
   https://zenodo.org/records/18693917

2. Place the downloaded files into the `data/` folder in the root of this repository.

Expected layout:

```text
.
├── CHExNet_properties_exploarion.ipynb
├── net_properties_funcs.py
└── data/
    ├── (files downloaded from Zenodo go here)
    └── ...
```

3. Install libraries from `requirements.txt`


## Code in this repo
- `CHExNet_creation.ipynb`  
  Creates the CHExNet dataset from the matched source tables by (1) generating a half‑year time index (`time_id_final.pkl`), (2) constructing sparse adjacency matrices per time slice via group co-membership for **layer 1** (CAC events / institutional co-presence) and **layer 2** (bibliographic co-mentions / ALMA-derived data), and (3) exporting the combined multilayer structure to `CHExNet.pkl`.

- `CHExNet_properties_exploarion.ipynb`  
  Loads the CHExNet data, constructs the graphs, and computes aggregated + temporal network metrics (e.g., LCC size, density / mean degree, clustering, assortativity).

- `net_properties_funcs.py`  
  Utility functions used by the notebook: build rolling-window temporal graphs, extract the giant component, compute summary metrics, and run metric series in parallel (with `tqdm` progress bars).

