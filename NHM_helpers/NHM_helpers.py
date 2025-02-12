# Import Notebook Packages
import warnings
from urllib import request
from urllib.request import urlopen
from urllib.error import HTTPError

import re
from io import StringIO
import os

# os.environ["USE_PYGEOS"] = "0"

import geopandas as gpd
import xarray as xr
import pandas as pd
import pathlib as pl
import numpy as np
import pyogrio

import netCDF4

import ipyleaflet

import branca
import branca.colormap as cm

import folium
from folium import Circle, Marker
from folium import plugins
from folium.features import DivIcon
from folium.plugins import MarkerCluster
from ipywidgets import widgets

from ipyleaflet import Map, GeoJSON

# PyPRMS needs
from pyPRMS import Dimensions
from pyPRMS.metadata.metadata import MetaData
from pyPRMS import ControlFile
from pyPRMS import Parameters
from pyPRMS import ParameterFile
from pyPRMS.prms_helpers import get_file_iter, cond_check
from pyPRMS.constants import (
    DIMENSIONS_HDR,
    PARAMETERS_HDR,
    VAR_DELIM,
    PTYPE_TO_PRMS_TYPE,
    PTYPE_TO_DTYPE,
)
from pyPRMS.Exceptions_custom import ParameterExistsError, ParameterNotValidError
import networkx as nx
from collections.abc import KeysView

import pywatershed as pws

from rich.console import Console
from rich.progress import track
from rich.progress import Progress
from rich import pretty

pretty.install()
con = Console()

warnings.filterwarnings("ignore")

#### Adds:
import matplotlib as mplib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import ipyleaflet
from ipyleaflet import Map, GeoJSON

from folium import Choropleth
from folium.plugins import BeautifyIcon

import branca
import branca.colormap as cm

import plotly.graph_objects as go
import plotly
import plotly.subplots
import plotly.express as px

import dataretrieval.nwis as nwis

### Helper Functions

def subset_stream_network(dag_ds, uscutoff_seg, dsmost_seg):  # (from Bandit)
    """Extract subset of stream network

    :param dag_ds: Directed, acyclic graph of downstream stream network
    :param uscutoff_seg: List of upstream cutoff segments
    :param dsmost_seg: List of outlet segments to start extraction from

    :returns: Stream network of extracted segments
    """

    # taken from Bandit bandit_helpers.py

    # Create the upstream graph
    dag_us = dag_ds.reverse()

    # Trim the u/s graph to remove segments above the u/s cutoff segments
    try:
        for xx in uscutoff_seg:
            try:
                dag_us.remove_nodes_from(nx.dfs_predecessors(dag_us, xx))

                # Also remove the cutoff segment itself
                dag_us.remove_node(xx)
            except KeyError:
                print(f"WARNING: nhm_segment {xx} does not exist in stream network")
    except TypeError:
        print(
            "\nSelected cutoffs should at least be an empty list instead of NoneType."
        )

    # =======================================
    # Given a d/s segment (dsmost_seg) create a subset of u/s segments

    # Get all unique segments u/s of the starting segment
    uniq_seg_us: Set[int] = set()
    if dsmost_seg:
        for xx in dsmost_seg:
            try:
                pred = nx.dfs_predecessors(dag_us, xx)
                uniq_seg_us = uniq_seg_us.union(
                    set(pred.keys()).union(set(pred.values()))
                )
            except KeyError:
                print(f"KeyError: Segment {xx} does not exist in stream network")

        # Get a subgraph in the dag_ds graph and return the edges
        dag_ds_subset = dag_ds.subgraph(uniq_seg_us).copy()

        node_outlets = [ee[0] for ee in dag_ds_subset.edges()]
        true_outlets = set(dsmost_seg).difference(set(node_outlets))

        # Add the downstream segments that exit the subgraph
        for xx in true_outlets:
            nhm_outlet = list(dag_ds.neighbors(xx))[0]
            dag_ds_subset.add_node(
                nhm_outlet, style="filled", fontcolor="white", fillcolor="grey"
            )
            dag_ds_subset.add_edge(xx, nhm_outlet)
            dag_ds_subset.nodes[xx]["style"] = "filled"
            dag_ds_subset.nodes[xx]["fontcolor"] = "white"
            dag_ds_subset.nodes[xx]["fillcolor"] = "blue"
    else:
        # No outlets specified so pull the full model
        dag_ds_subset = dag_ds

    return dag_ds_subset


def hrus_by_seg(pdb, segs):  # (custom code)
    # segs: global segment IDs

    if isinstance(segs, int):
        segs = [segs]
    elif isinstance(segs, KeysView):
        segs = list(segs)

    seg_hrus = {}
    seg_to_hru = pdb.seg_to_hru

    # Generate stream network for the model
    dag_streamnet = pdb.stream_network()

    for cseg in segs:
        # Lookup segment for the current POI
        dsmost_seg = [cseg]

        # Get subset of stream network for given POI
        dag_ds_subset = subset_stream_network(dag_streamnet, set(), dsmost_seg)

        # Create list of segments in the subset
        toseg_idx = list(set(xx[0] for xx in dag_ds_subset.edges))

        # Build list of HRUs that contribute to the POI
        final_hru_list = []

        for xx in toseg_idx:
            try:
                for yy in seg_to_hru[xx]:
                    final_hru_list.append(yy)
            except KeyError:
                # print(f'Segment {xx} has no HRUs connected to it') # comment this out and add pass to not print the KeyError
                pass
        final_hru_list.sort()

        seg_hrus[cseg] = final_hru_list

    return seg_hrus


def hrus_by_poi(pdb, poi):  # (custom code)
    if isinstance(poi, str):
        poi = [poi]
    elif isinstance(poi, KeysView):
        poi = list(poi)

    poi_hrus = {}
    nhm_seg = pdb.get("nhm_seg").data
    pois_dict = pdb.poi_to_seg
    seg_to_hru = pdb.seg_to_hru

    # Generate stream network for the model
    dag_streamnet = pdb.stream_network()

    for cpoi in poi:
        # Lookup global segment id for the current POI
        dsmost_seg = [nhm_seg[pois_dict[cpoi] - 1]]

        # Get subset of stream network for given POI
        dag_ds_subset = subset_stream_network(dag_streamnet, set(), dsmost_seg)

        # Create list of segments in the subset
        toseg_idx = list(set(xx[0] for xx in dag_ds_subset.edges))

        # Build list of HRUs that contribute to the POI
        final_hru_list = []

        for xx in toseg_idx:
            try:
                for yy in seg_to_hru[xx]:
                    final_hru_list.append(yy)
            except KeyError:
                # Not all segments have HRUs connected to them
                # print(f'{cpoi}: Segment {xx} has no HRUs connected to it')
                pass
        final_hru_list.sort()
        poi_hrus[cpoi] = final_hru_list

    return poi_hrus