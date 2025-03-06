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

from NHM_helpers.NHM_helpers import (
    hrus_by_poi,
    hrus_by_seg,
    subset_stream_network,
    create_poi_group,
)
from NHM_helpers.map_template import *
from NHM_helpers.NHM_Assist_utilities import make_plots_par_vals

from NHM_helpers.NHM_output_visualization import (
    retrieve_hru_output_info,
    create_sum_var_dataarrays,
    create_mean_var_dataarrays,
    create_sum_var_annual_gdf,
    create_sum_var_annual_df,
    create_sum_var_monthly_df,
    create_var_daily_df,
    create_var_ts_for_poi_basin_df,
)
from NHM_helpers.output_plots import * #create_poi_group

import hydroeval as he
import calendar
import statistics
from sklearn.metrics import r2_score

import webbrowser

# HRU color list
import random

plot_colors = [
    "aliceblue",
    "aqua",
    "aquamarine",
    "azure",
    "beige",
    "bisque",
    "black",
    "blue",
    "blueviolet",
    "brown",
    "burlywood",
    "cadetblue",
    "chartreuse",
    "chocolate",
    "coral",
    "cornflowerblue",
    "crimson",
    "cyan",
    "darkblue",
    "darkcyan",
    "darkgoldenrod",
    "darkgray",
    "darkgrey",
    "darkgreen",
    "darkkhaki",
    "darkmagenta",
    "darkolivegreen",
    "darkorange",
    "darkorchid",
    "darkred",
    "darksalmon",
    "darkseagreen",
    "darkslateblue",
    "darkslategray",
    "darkslategrey",
    "darkturquoise",
    "darkviolet",
    "deeppink",
    "deepskyblue",
    "dodgerblue",
    "firebrick",
    "forestgreen",
    "fuchsia",
    "gainsboro",
    "goldenrod",
    "green",
    "greenyellow",
    "honeydew",
    "hotpink",
    "indianred",
    "indigo",
    "lavender",
    "lawngreen",
    "lime",
    "limegreen",
    "magenta",
    "maroon",
    "mediumaquamarine",
    "mediumblue",
    "mediumorchid",
    "mediumpurple",
    "mediumseagreen",
    "mediumslateblue",
    "mediumspringgreen",
    "mediumturquoise",
    "mediumvioletred",
    "midnightblue",
    "mintcream",
    "moccasin",
    "navy",
    "olive",
    "olivedrab",
    "orange",
    "orangered",
    "orchid",
    "palegreen",
    "paleturquoise",
    "palevioletred",
    "papayawhip",
    "peachpuff",
    "peru",
    "pink",
    "plum",
    "powderblue",
    "purple",
    "red",
    "rosybrown",
    "royalblue",
    "rebeccapurple",
    "saddlebrown",
    "salmon",
    "sandybrown",
    "seagreen",
    "sienna",
    "silver",
    "skyblue",
    "slateblue",
    "slategray",
    "slategrey",
    "springgreen",
    "steelblue",
    "tan",
    "teal",
    "thistle",
    "tomato",
    "turquoise",
    "violet",
    "wheat",
    "yellowgreen",
]
# random.shuffle(plot_colors)
random.Random(4).shuffle(plot_colors)
# plot_colors

# Dictionaries for plots
var_colors_dict = {
    "hru_actet": "red",
    "recharge": "brown",
    "net_rain": "blue",
    "net_snow": "lightblue",
    "net_ppt": "darkblue",
    "sroff": "lightgreen",
    "sroff_vol": "lightgreen",
    "ssres_flow": "green",
    "ssres_flow_vol": "green",
    "gwres_flow": "chocolate",
    "gwres_flow_vol": "chocolate",
    "gwres_sink": "black",
    "snowmelt": "mediumpurple",
    "gwres_stor": "darkgreen",
    "gwres_stor_change": "darkgreen",
    "ssres_stor": "green",
    "unused_potet": "orange",
}

# 'legendonly'
leg_only_dict = {
    "hru_actet": "legendonly",
    "recharge": "legendonly",
    "net_rain": "legendonly",
    "net_snow": "legendonly",
    "net_ppt": True,
    "sroff": True,
    "sroff_vol": True,
    "ssres_flow": "legendonly",
    "ssres_flow_vol": "legendonly",
    "gwres_flow": True,
    "gwres_flow_vol": True,
    "gwres_sink": "legendonly",
    "snowmelt": "legendonly",
    "gwres_stor": "legendonly",
    "gwres_stor_change": "legendonly",
    "ssres_stor": "legendonly",
    "unused_potet": "legendonly",
}

def make_plot_var_for_hrus_in_poi_basin(
    out_dir,
    param_filename,
    water_years,
    hru_gdf,
    poi_df,
    output_var_sel,
    var_units,
    poi_id_sel,
    plot_start_date,
    plot_end_date,
    plot_colors,
    subbasin,
    html_plots_dir,
):
    #plot_file = f"{html_plots_dir}/{output_var_sel}_for_{poi_id_sel}_plot.html"
    plot_file_path = pl.Path(html_plots_dir / f"{output_var_sel}_for_{poi_id_sel}_plot.html").resolve()
    
    if plot_file_path.exists():
        webbrowser.open(f"{plot_file_path}", new=2)
    else:
        var_daily, sum_var_monthly, sum_var_annual, var_units, var_desc = (
            create_sum_var_dataarrays(
                out_dir,
                output_var_sel,
                plot_start_date,
                plot_end_date,
                water_years,
            )
        )
        
        hru_gdf, hru_poi_dict = create_poi_group(hru_gdf, poi_df, param_filename)
        
        if poi_id_sel:
            hru_list = hru_poi_dict[
                poi_id_sel
            ]  # returns a list of all upstream contributing hrus
    
            fig = plotly.subplots.make_subplots(
                rows=3,
                cols=1,
                shared_xaxes="columns",
                # shared_yaxes = 'columns',
                start_cell="top-left",
                vertical_spacing=0.1,
                y_title=f"{output_var_sel}, {var_units}",
                subplot_titles=[
                    "Annual",
                    "Monthly",
                    "Daily",
                ],
                specs=[
                    [{"type": "scatter"}],
                    [{"type": "scatter"}],
                    [{"type": "scatter"}],
                ],
            )
            fig.update_layout(
                title_text=f'The NHM {subbasin} domain {output_var_sel} for poi basin<br> {poi_id_sel}, {poi_df.loc[poi_df.poi_id == poi_id_sel, "poi_name"].values[0]}',  #
                width=900,
                height=700,
                legend=dict(orientation="v", yanchor="top", y=1, xanchor="right", x=10.0),
                # legend_tracegroupgap = 5,
                font=dict(family="Arial", size=14, color="#7f7f7f"),  # font color
                paper_bgcolor="linen",
                plot_bgcolor="white",
            )
    
            fig.update_layout(
                title_automargin=True,
                title_font_color="black",
                title_font_size=20,
                title_x=0.5,
                title_y=0.945,
                title_xref="container",
                title_xanchor="center",
            )
    
            # fig.update_xaxes(range = [daily_plot_df.index[0], daily_plot_df.index[-1]])
    
            fig.update_layout(font_color="black")
            fig.update_layout(legend={"title": "Extent"})
    
            fig.update_xaxes(ticks="inside", tickwidth=2, tickcolor="black", ticklen=10)
            fig.update_yaxes(ticks="inside", tickwidth=2, tickcolor="black", ticklen=10)
    
            fig.update_xaxes(
                showline=True, linewidth=2, linecolor="black", gridcolor="lightgrey"
            )
            fig.update_yaxes(
                showline=True, linewidth=2, linecolor="black", gridcolor="lightgrey"
            )
    
            fig.update_traces(hovertemplate=None)
            fig.update_layout(hovermode="x unified")
            fig.update_layout(
                hoverlabel=dict(
                    bgcolor="linen",
                    font_size=13,
                    font_family="Rockwell",
                )
            )
    
            ######################################################
    
            annual_fig = go.Figure()
    
            # subset to selcted gage one gage
            sum_var_annual_df = create_sum_var_annual_df(
                hru_gdf,
                poi_df,
                param_filename,
                plot_start_date,
                plot_end_date,
                sum_var_annual,
                output_var_sel,
            )
            
            df_basin = sum_var_annual_df.loc[
                sum_var_annual_df["nhm_id"].isin(hru_poi_dict[poi_id_sel])
            ]
            df_basin.set_index(
                ["time", "nhm_id"], inplace=True, drop=True
            )  # resets the index to that new value and type
    
            # Calculate basin volume average output_var value from basin HRUs
            df_basin_plot1 = df_basin.groupby(level="time").sum()
            df_basin_plot1["output_var"] = (
                df_basin_plot1["vol_inch_acres"] / df_basin_plot1["hru_area"]
            )
    
            annual_fig.add_trace(
                go.Scatter(
                    x=df_basin_plot1.index,
                    y=(df_basin_plot1.output_var).ravel().tolist(),
                    mode="lines",
                    name=f"poi basin",
                    showlegend=True,
                    legendgroup="poi_basin",
                    # marker=dict(color='lightblue'),
                    line=dict(
                        color="lightblue",
                        width=5,
                        # dash='dot'
                    ),
                )
            )
    
            for (
                value
            ) in (
                hru_list
            ):  # I fixed this below to read right from the xarray, need to fix the hru_list as well.
                hru_id_sel = value
                color_sel = hru_list.index(hru_id_sel)
                ds_sub = (
                    sum_var_annual.where((sum_var_annual.nhm_id == hru_id_sel), drop=True)
                ).sel(
                    time=slice(plot_start_date, plot_end_date)
                )  # have to fix to subset to new date range
                annual_fig.add_trace(
                    go.Scatter(
                        x=ds_sub.time,
                        y=(ds_sub.values).ravel().tolist(),
                        mode="lines",
                        name=f"HRU {hru_id_sel}",
                        showlegend=True,
                        visible="legendonly",
                        legendgroup=hru_id_sel,
                        # marker=dict(color=plot_colors[color_sel]),
                        line=dict(
                            color=plot_colors[color_sel],
                            width=2,
                            # dash='dot'
                        ),
                    )
                )
    
            monthly_fig = go.Figure()
    
            # subset to selcted gage one gage
    
            sum_var_monthly_df = create_sum_var_monthly_df(
               hru_gdf,
               poi_df,
               param_filename,
               output_var_sel,
               plot_start_date,
               plot_end_date,
               sum_var_monthly,
           )
    
            
            df_basin = sum_var_monthly_df.loc[
                sum_var_monthly_df["nhm_id"].isin(hru_poi_dict[poi_id_sel])
            ]
            df_basin.set_index(
                ["time", "nhm_id"], inplace=True, drop=True
            )  # resets the index to that new value and type
    
            # Calculate basin recharge from individual HRU contributions for plotting
            df_basin_plot1 = df_basin.groupby(level="time").sum()
            df_basin_plot1["output_var"] = (
                df_basin_plot1["vol_inch_acres"] / df_basin_plot1["hru_area"]
            )
    
            monthly_fig.add_trace(
                go.Scatter(
                    x=df_basin_plot1.index,
                    y=(df_basin_plot1.output_var).ravel().tolist(),
                    mode="lines",
                    name=poi_id_sel,
                    showlegend=False,
                    legendgroup="poi_basin",
                    # marker=dict(color='lightblue'),
                    line=dict(
                        color="lightblue",
                        width=5,
                        # dash='dot'
                    ),
                )
            )
    
            for (
                value
            ) in (
                hru_list
            ):  # I fixed this below to read right from the xarray, need to fix the hru_list as well.
                hru_id_sel = value
                color_sel = hru_list.index(hru_id_sel)
                ds_sub = (
                    sum_var_monthly.where((sum_var_monthly.nhm_id == hru_id_sel), drop=True)
                ).sel(time=slice(plot_start_date, plot_end_date))
                monthly_fig.add_trace(
                    go.Scatter(
                        x=ds_sub.time,
                        y=(ds_sub.values).ravel().tolist(),
                        mode="lines",
                        name=hru_id_sel,
                        showlegend=False,
                        visible="legendonly",
                        legendgroup=hru_id_sel,
                        # marker=dict(color=plot_colors[color_sel]),
                        line=dict(
                            color=plot_colors[color_sel],
                            width=2,
                            # dash='dot'
                        ),
                    )
                )
            daily_fig = go.Figure()
    
            # subset to selcted gage one gage
    
            var_daily_df = create_var_daily_df(
                hru_gdf,
                poi_df,
                param_filename,
                output_var_sel,
                plot_start_date,
                plot_end_date,
                var_daily,
            )
    
            df_basin = var_daily_df.loc[
                var_daily_df["nhm_id"].isin(hru_poi_dict[poi_id_sel])
            ]
            df_basin.set_index(
                ["time", "nhm_id"], inplace=True, drop=True
            )  # resets the index to that new value and type
    
            # Calculate basin recharge from individual HRU contributions for plotting
            df_basin_plot1 = df_basin.groupby(level="time").sum()
            df_basin_plot1["output_var"] = (
                df_basin_plot1["vol_inch_acres"] / df_basin_plot1["hru_area"]
            )
    
            daily_fig.add_trace(
                go.Scatter(
                    x=df_basin_plot1.index,
                    y=(df_basin_plot1.output_var).ravel().tolist(),
                    mode="lines",
                    name=poi_id_sel,
                    showlegend=False,
                    legendgroup="poi_basin",
                    # marker=dict(color='lightblue'),
                    line=dict(
                        color="lightblue",
                        width=5,
                        # dash='dot'
                    ),
                )
            )
    
            for (
                value
            ) in (
                hru_list
            ):  # I fixed this below to read right from the xarray, need to fix the hru_list as well.
                hru_id_sel = value
                color_sel = hru_list.index(hru_id_sel)
                ds_sub = (var_daily.where((var_daily.nhm_id == hru_id_sel), drop=True)).sel(
                    time=slice(plot_start_date, plot_end_date)
                )
                daily_fig.add_trace(
                    go.Scatter(
                        x=ds_sub.time,
                        y=(ds_sub.values).ravel().tolist(),
                        mode="lines",
                        name=hru_id_sel,
                        showlegend=False,
                        visible="legendonly",
                        legendgroup=hru_id_sel,
                        # marker=dict(color=plot_colors[color_sel]),
                        line=dict(
                            color=plot_colors[color_sel],
                            width=2,
                            # dash='dot'
                        ),
                    )
                )
    
            for t in annual_fig.data:
                fig.append_trace(t, row=1, col=1)
    
            for t in monthly_fig.data:
                fig.append_trace(t, row=2, col=1)
    
            for t in daily_fig.data:
                fig.append_trace(t, row=3, col=1)
    
            plotly.offline.plot(fig, filename=f"{plot_file_path}")

        return plot_file_path

def oopla(
    out_dir,
    param_filename,
    water_years,
    hru_gdf,
    poi_df,
    output_var_list,
    output_var_sel,
    var_units,
    poi_id_sel,
    plot_start_date,
    plot_end_date,
    plot_colors,
    var_colors_dict,
    leg_only_dict,
    subbasin,
    html_plots_dir,
):
    """
    Make figure of three plots...

    First figure setup.

    """
    plot_file_path = pl.Path(html_plots_dir / f"water_budget_fluxes_for_{poi_id_sel}_plot.html").resolve()
    
    if plot_file_path.exists():
        webbrowser.open(f"{plot_file_path}", new=2)
    else:

        hru_gdf, hru_poi_dict = create_poi_group(hru_gdf, poi_df, param_filename)
    
        fig = plotly.subplots.make_subplots(
            rows=3,
            cols=1,
            shared_xaxes="columns",
            # shared_yaxes = 'columns',
            start_cell="top-left",
            vertical_spacing=0.1,
            y_title="Water flux, cubic-feet per second",
            subplot_titles=[
                "Annual mean",
                "Monthly mean",
                "Daily",
            ],
            specs=[
                [{"type": "scatter"}],
                [{"type": "scatter"}],
                [{"type": "scatter"}],
            ],
        )
        fig.update_layout(
            title_text=f'The NHM {subbasin} domain water budget flux rates for <br> {poi_id_sel}, {poi_df.loc[poi_df.poi_id == poi_id_sel, "poi_name"].values[0]}',  #
            width=900,
            height=700,
            legend=dict(orientation="v", yanchor="top", y=1, xanchor="right", x=10.0),
            # legend_tracegroupgap = 5,
            font=dict(family="Arial", size=14, color="#7f7f7f"),  # font color
            paper_bgcolor="linen",
            plot_bgcolor="white",
        )
    
        fig.update_layout(
            title_automargin=True,
            title_font_color="black",
            title_font_size=20,
            title_x=0.5,
            title_y=0.945,
            title_xref="container",
            title_xanchor="center",
        )
    
        # fig.update_xaxes(range = [daily_plot_df.index[0], daily_plot_df.index[-1]])
    
        fig.update_layout(font_color="black")
        fig.update_layout(
            legend={"title": "NHM output variable"}
        )  # <--- add only this line
    
        fig.update_xaxes(ticks="inside", tickwidth=2, tickcolor="black", ticklen=10)
        fig.update_yaxes(ticks="inside", tickwidth=2, tickcolor="black", ticklen=10)
    
        fig.update_xaxes(
            showline=True, linewidth=2, linecolor="black", gridcolor="lightgrey"
        )
        fig.update_yaxes(
            showline=True, linewidth=2, linecolor="black", gridcolor="lightgrey"
        )
    
        fig.update_traces(hovertemplate=None)
    
        fig.update_layout(hovermode="x unified")
        fig.update_layout(
            hoverlabel=dict(
                bgcolor="linen",
                font_size=13,
                font_family="Rockwell",
            )
        )
    
        daily_fig = go.Figure()
        annual_fig = go.Figure()
        monthly_fig = go.Figure()
    
        """
        Nww to plot the data
    
        """
        for var in output_var_list:
            color_sel = var_colors_dict[var]
            leg_only = leg_only_dict[var]
    
            var_daily, mean_var_monthly, mean_var_annual, var_units, var_desc = (
                create_mean_var_dataarrays(
                    out_dir,
                    var,
                    plot_start_date,
                    plot_end_date,
                    water_years,
                )
            )
    
            df_basin_plot1_annual = create_var_ts_for_poi_basin_df(
                mean_var_annual,
                var,
                hru_gdf,
                hru_poi_dict,
                poi_id_sel,
            )
    
            df_basin_plot1_monthly = create_var_ts_for_poi_basin_df(
                mean_var_monthly,
                var,
                hru_gdf,
                hru_poi_dict,
                poi_id_sel,
            )
    
            df_basin_plot1_daily = create_var_ts_for_poi_basin_df(
                var_daily,
                var,
                hru_gdf,
                hru_poi_dict,
                poi_id_sel,
            )
    
            annual_fig.add_trace(
                go.Scatter(
                    x=df_basin_plot1_annual.index,
                    y=(df_basin_plot1_annual.vol_cfs).ravel().tolist(),
                    # x=year_list,
                    # y= (gdf.loc[gdf.nhm_id == hru_id_sel, year_list].values).ravel().tolist(),
                    mode="lines",
                    name=var,
                    visible=leg_only,
                    showlegend=True,
                    legendgroup=var,
                    # marker=dict(color='lightblue'),
                    line_shape="vh",
                    line=dict(
                        color=color_sel,
                        width=2,
                        # dash='dot'
                    ),
                )
            )
    
            monthly_fig.add_trace(
                go.Scatter(
                    x=df_basin_plot1_monthly.index,
                    y=(df_basin_plot1_monthly.vol_cfs).ravel().tolist(),
                    # x=year_list,
                    # y= (gdf.loc[gdf.nhm_id == hru_id_sel, year_list].values).ravel().tolist(),
                    mode="lines",
                    name=var,
                    visible=leg_only,
                    showlegend=False,
                    legendgroup=var,
                    # marker=dict(color='lightblue'),
                    line_shape="vh",
                    line=dict(
                        color=color_sel,
                        width=2,
                        # dash='dot'
                    ),
                )
            )
    
            daily_fig.add_trace(
                go.Scatter(
                    x=df_basin_plot1_daily.index,
                    y=(df_basin_plot1_daily.vol_cfs).ravel().tolist(),
                    # x=year_list,
                    # y= (gdf.loc[gdf.nhm_id == hru_id_sel, year_list].values).ravel().tolist(),
                    mode="lines",
                    name=var,
                    visible=leg_only,
                    showlegend=False,
                    legendgroup=var,
                    # marker=dict(color='lightblue'),
                    line_shape="vh",
                    line=dict(
                        color=color_sel,
                        width=2,
                        # dash='dot'
                    ),
                )
            )
    
        for t in annual_fig.data:
            fig.append_trace(t, row=1, col=1)
    
        for t in monthly_fig.data:
            fig.append_trace(t, row=2, col=1)
    
        for t in daily_fig.data:
            fig.append_trace(t, row=3, col=1)
    
        plotly.offline.plot(fig, filename=f"{plot_file_path}")
    
    return plot_file_path

def stats_table(stats_df):
    """
    stats_df must have columns ['discharge', 'seg_outflow']
    """

    evaluations = stats_df.discharge
    std_evaluations = statistics.stdev(evaluations)

    simulations = stats_df.seg_outflow

    rmse = np.round(he.evaluator(he.rmse, simulations, evaluations), 2)
    nse = np.round(he.evaluator(he.nse, simulations, evaluations), 2)
    pbias = np.round(he.evaluator(he.pbias, simulations, evaluations), 2)
    kge, r, alpha, beta = np.round(he.evaluator(he.kge, simulations, evaluations), 2)

    rsr = np.round(rmse / std_evaluations, 2)
    r_sq = np.round(np.array([r2_score(simulations, evaluations)]), 2)

    stat_dict = {
        "KGE": kge[0],
        "NSE": nse[0],
        "Pbias": pbias[0],
        "RMSE": rmse[0],
        "R^2": r_sq[0],
        "R": r[0],
        "Alpha": alpha[0],
        "Beta": beta[0],
        "RSR": rsr[0],
    }

    df = pd.DataFrame(stat_dict, index=[0])

    return df

def calculate_monthly_kge_in_poi_df(
    obs,
    var_daily,
    poi_df,
):

    for i in poi_df.poi_id:
        # print(obs.sel(poi_id=poi_tag))
        df_sf_data_sel_temp = obs.sel(poi_id=i)
        df_sf_data_sel = df_sf_data_sel_temp.to_dataframe()
        # Determine por
        por_start = df_sf_data_sel["discharge"].notna().idxmax()  # First Day
        por_end = df_sf_data_sel["discharge"].notna()[::-1].idxmax()  # Last Day

        # Slice to por
        df_sf_data_sel = (
            obs.sel(poi_id=i, time=slice(por_start, por_end))
        ).to_dataframe()
        df_sf_data_sel.drop(columns=["poi_id"], inplace=True)  # drop unwanted columns

        sim_flow = (
            var_daily.sel(npoi_gages=i, time=slice(por_start, por_end))
        ).to_dataframe()
        sim_flow.drop(columns=["npoi_gages"], inplace=True)  # drop unwanted columns

        # drop the Nan's from the obs for memory/stats (may want to check back on this later)
        daily_stat_df = (
            df_sf_data_sel.merge(
                sim_flow, right_index=True, left_index=True, how="inner"
            )
        ).dropna()
        month_stat_df = daily_stat_df.resample("m").mean().dropna()

        kge_func = np.round(
            he.evaluator(
                he.kge,
                month_stat_df["seg_outflow"],  # simulation data set
                month_stat_df["discharge"],  # observation data set
            ),
            2,  # decimal places for the round() function
        )[
            0
        ]  # this grabs only the kge var, in position"0" from the list of ke.kge() output vars

        poi_df.loc[poi_df.poi_id == i, "kge"] = np.array(
            kge_func[0]
        )  # pandas wrangling of the array output from he.evaluator() as an array

    return poi_df

def create_streamflow_plot(
    obs_annual,
    obs,
    obs_efc,
    poi_id_sel,
    water_years,
    var_daily,
    var_units,
    poi_name_df,
    html_plots_dir,
    Folium_maps_dir,
):
    """ """
    plot_file_path = pl.Path(
        html_plots_dir / f"streamflow_eval_for_{poi_id_sel}_plot.html"
    ).resolve()

    if plot_file_path.exists():
        webbrowser.open(f"{plot_file_path}", new=2)

    else:
        # Single request
        if len((obs_annual.sel(poi_id=poi_id_sel)).to_dataframe().dropna()) < 2:
            con.print(
                f"The gage {poi_id_sel} has no observation data in the streamflow obs file."
            )
            pass
        else:
            df_sf_data_sel = (obs.sel(poi_id=poi_id_sel)).to_dataframe()

            # Determine por
            por_start = df_sf_data_sel["discharge"].notna().idxmax()  # First Day
            por_end = df_sf_data_sel["discharge"].notna()[::-1].idxmax()  # Last Day

            # Slice to por
            df_sf_data_sel = (
                obs.sel(poi_id=poi_id_sel, time=slice(por_start, por_end))
            ).to_dataframe()
            df_sf_data_sel.drop(
                columns=["poi_id"], inplace=True
            )  # drop unwanted columns

            obs_efc_sel = (
                obs_efc.sel(poi_id=poi_id_sel, time=slice(por_start, por_end))
            ).to_dataframe()
            obs_efc_sel.drop(columns=["poi_id"], inplace=True)  # drop unwanted columns
            obs_with_efc_sel = df_sf_data_sel.merge(
                obs_efc_sel, right_index=True, left_index=True, how="inner"
            )  # .dropna() #how='left' will slice ts with obs range

            sim_flow = (
                var_daily.sel(npoi_gages=poi_id_sel, time=slice(por_start, por_end))
            ).to_dataframe()
            sim_flow.drop(columns=["npoi_gages"], inplace=True)  # drop unwanted columns

            # Create a dataframe for the NaN's that occur between the beginning and end of por
            daily_efc_df = (
                obs_with_efc_sel.merge(
                    sim_flow, right_index=True, left_index=True, how="inner"
                )
            ).dropna()
            daily_efc_plot_df = obs_with_efc_sel.merge(
                sim_flow, right_index=True, left_index=True, how="inner"
            )
            daily = df_sf_data_sel.merge(
                sim_flow, right_index=True, left_index=True, how="inner"
            )
            # daily_na = daily[daily["discharge"].isnull()]
            # daily_na["discharge"] = 5.0

            # drop the Nan's from the obs for memory/stats (may want to check back on this later)
            daily_stat_df = (
                df_sf_data_sel.merge(
                    sim_flow, right_index=True, left_index=True, how="inner"
                )
            ).dropna()
            daily_plot_df = df_sf_data_sel.merge(
                sim_flow, right_index=True, left_index=True, how="inner"
            )  # .dropna()

            # daily_stat_df_na = daily_stat_df[daily_stat_df['discharge'].isnull()]
            # daily_stat_df = daily_stat_df.dropna()

            # .dropna() #how='left' will slice ts with obs range
            # daily_stat_df =streamflows_df.copy()#.dropna()
            month_stat_df = daily_stat_df.resample("m").mean().dropna()
            month_plot_df = daily_plot_df.resample("m").mean()  # .dropna()

            if water_years:
                water_year_stat_df = daily_stat_df.resample("A-SEP").mean().dropna()
                water_year_plot_df = daily_plot_df.resample("A-SEP").mean()  # .dropna()
            else:
                water_year_stat_df = daily_stat_df.resample("y").mean().dropna()
                water_year_plot_df = daily_plot_df.resample("y").mean()  # .dropna()

            if len(daily_efc_df) <= 10000:
                n = len(daily_efc_df)
            else:
                n = 10000  # Number of sampled days in records

            ######################################################
            # Make timeseries subplot figure
            fig = plotly.subplots.make_subplots(
                rows=3,
                cols=2,
                column_widths=[0.5, 0.5],  # row_heights=[0., 0.3, 0.3, 0.4],
                shared_xaxes="columns",
                # shared_yaxes = 'columns',
                start_cell="top-left",
                vertical_spacing=0.1,
                horizontal_spacing=0.06,
                # y_title=f"Average daily streamflow, {getattr(model_output, output_var_sel).units}",
                y_title=f"Average daily streamflow, {var_units}",
                subplot_titles=[
                    "Annual mean",
                    f"Flow Exceedence Curve, n = {n}",
                    "Monthly mean",
                    "Daily",
                    "Statistics",
                ],
                specs=[
                    [{"type": "scatter"}, {"type": "scatter", "rowspan": 2}],
                    [{"type": "scatter"}, None],
                    [{"type": "scatter"}, {"type": "table"}],
                ],
            )

            poi_name = poi_name_df.loc[
                poi_name_df.index == poi_id_sel, "poi_name"
            ].values[0]
            date_range = f"{daily_stat_df.index.month[0]}-{daily_stat_df.index.day[0]}-{daily_stat_df.index.year[0]} to {daily_plot_df.index.month[-1]}-{daily_plot_df.index.day[-1]}-{daily_plot_df.index.year[-1]} "

            fig.update_layout(
                title_text=f"NHM simulated streamflow at {poi_id_sel},<br>{poi_name}, {date_range}",  #
                width=900,
                height=700,
                legend=dict(
                    orientation="h", yanchor="bottom", y=-0.15, xanchor="right", x=0.7
                ),
                font=dict(family="Arial", size=14, color="#7f7f7f"),  # font color
                paper_bgcolor="linen",
                plot_bgcolor="white",
            )

            fig.update_layout(
                title_automargin=True,
                title_font_color="black",
                title_font_size=20,
                title_x=0.5,
                title_y=0.945,
                title_xref="container",
                title_xanchor="center",
            )

            fig.update_xaxes(range=[daily_plot_df.index[0], daily_plot_df.index[-1]])
            # fig.update_xaxes(range = [(obs["time"][0].dt.datetime.strftime("%Y-%m-%d").values.tolist()), (obs["time"][-1].dt.datetime.strftime("%Y-%m-%d").values.tolist())])

            # fig.update_layout(legend_grouptitlefont_color='black')
            fig.update_layout(font_color="black")

            # fig.update_yaxes(title_text=f'{output_var_sel}, {getattr(model_output, output_var_sel).units}', title_font_color = 'black')
            # fig.update_xaxes(title_text="Water years, from October 1 to September 31", title_font_color = 'black')

            fig.update_xaxes(ticks="inside", tickwidth=2, tickcolor="black", ticklen=10)
            fig.update_yaxes(ticks="inside", tickwidth=2, tickcolor="black", ticklen=10)

            fig.update_xaxes(
                showline=True, linewidth=2, linecolor="black", gridcolor="lightgrey"
            )
            fig.update_yaxes(
                showline=True, linewidth=2, linecolor="black", gridcolor="lightgrey"
            )

            fig.update_traces(hovertemplate=None)
            fig.update_layout(hovermode="x unified")  # "x unified"
            fig.update_layout(
                hoverlabel=dict(
                    bgcolor="linen",
                    font_size=13,
                    font_family="Rockwell",
                )
            )
            # Useful xarray calls
            # f'{(obs["time"][0].dt.datetime.strftime("%Y-%m-%d").values.tolist())} to {(obs["time"][-1].dt.datetime.strftime("%Y-%m-%d").values.tolist())} '
            # x_values_annual = (output_var_annual["time"].dt.datetime.strftime("%Y-%m-%d").values.tolist())
            # sim_values_annual = (output_var_annual.sel(npoi_gages = poi_id_sel).values.tolist())
            # obs_values = (obs_annual.sel(poi_id = poi_id_sel).values.tolist())

            ######################################################
            # Create annual subplot
            annual_plots = [
                go.Scatter(
                    x=water_year_plot_df.index,
                    y=water_year_plot_df.discharge,
                    mode="lines",
                    name="Observed flow, annual",
                    showlegend=False,
                    # marker=dict(color='brown'),
                    # xaxis =
                    line=dict(
                        color="deepskyblue",
                        width=4,
                        # dash='dot'
                    ),
                ),
                go.Scatter(
                    x=water_year_plot_df.index,
                    y=water_year_plot_df.seg_outflow,
                    mode="lines",
                    name="Simulated flow, annual",
                    showlegend=False,
                    # marker=dict(color='brown'),
                    line=dict(
                        color="black",
                        width=1,
                        # dash='dot'
                    ),
                ),
            ]
            annual_fig = go.Figure(data=annual_plots)

            ######################################################
            # Create monthly subplot
            monthly_plots = [
                go.Scatter(
                    x=month_plot_df.index,
                    y=month_plot_df.discharge,
                    mode="lines",
                    name="Observed flow, monthly",
                    showlegend=False,
                    # marker=dict(color='brown'),
                    # xaxis =
                    line=dict(
                        color="deepskyblue",
                        width=4,
                        # dash='dot'
                    ),
                ),
                go.Scatter(
                    x=month_plot_df.index,
                    y=month_plot_df.seg_outflow,
                    mode="lines",
                    name="Simulated flow, monthly",
                    showlegend=False,
                    # marker=dict(color='brown'),
                    line=dict(
                        color="black",
                        width=1,
                        # dash='dot'
                    ),
                ),
            ]
            monthly_fig = go.Figure(data=monthly_plots)

            ######################################################
            # Create daily subplot
            # Make a line set for na values to show no data in the plot.

            # daily_efc_exlow_df = daily_efc_df.loc[daily_efc_df['efc'].isin([5])]
            daily_efc_low_plot_df = daily_efc_plot_df.copy()
            daily_efc_low_plot_df.loc[
                daily_efc_low_plot_df["efc"] <= 3, "discharge"
            ] = np.nan

            daily_efc_high_plot_df = daily_efc_plot_df.copy()
            daily_efc_high_plot_df.loc[
                daily_efc_high_plot_df["efc"] >= 4, "discharge"
            ] = np.nan

            daily_plots = [
                go.Scatter(
                    x=daily_efc_high_plot_df.index,  # (output_var["time"].dt.datetime.strftime("%Y-%m-%d").values.tolist()),
                    y=daily_efc_high_plot_df.discharge,  # (obs.sel(poi_id = poi_id_sel).values.tolist()),
                    mode="lines",
                    name="Observed flow",
                    showlegend=True,
                    connectgaps=False,
                    # marker=dict(color='deepskyblue', size = 5),
                    # xaxis =
                    line=dict(
                        color="deepskyblue",
                        width=4,
                        # dash='dot'
                    ),
                ),
                go.Scatter(
                    x=daily_efc_low_plot_df.index,  # (output_var["time"].dt.datetime.strftime("%Y-%m-%d").values.tolist()),
                    y=daily_efc_low_plot_df.discharge,  # (obs.sel(poi_id = poi_id_sel).values.tolist()),
                    mode="lines",
                    name="Observed flow, (Low)",
                    showlegend=True,
                    connectgaps=False,
                    # marker=dict(color='deepskyblue', size = 5),
                    # xaxis =
                    line=dict(
                        color="red",
                        width=4,
                        # dash='dot'
                    ),
                ),
                go.Scatter(
                    x=daily_plot_df.index,  # (output_var["time"].dt.datetime.strftime("%Y-%m-%d").values.tolist()),
                    y=daily_plot_df.seg_outflow,  # (output_var.sel(npoi_gages = poi_id_sel).values.tolist()),
                    mode="lines",
                    name="Simulated flow, daily",
                    showlegend=False,
                    # marker=dict(color='black', size = 3),
                    line=dict(
                        color="black",
                        width=1,
                        # dash='dot'
                    ),
                ),
            ]
            #######################################################
            # EFC classifications
            # 1 = Large floods
            # 2 = Small floods
            # 3 = High flow pulses
            # 4 = Low flows
            # 5 = Extreme low flows

            daily_df = stats_table(daily_stat_df)
            daily_df["time"] = "daily"
            monthly_df = stats_table(month_stat_df)
            monthly_df["time"] = "monthly"
            annual_df = stats_table(water_year_stat_df)
            annual_df["time"] = "annual"

            # daily_efc_exlow_df = daily_efc_df.loc[daily_efc_df['efc'].isin([5])]
            daily_efc_low_df = daily_efc_df.loc[daily_efc_df["efc"].isin([4, 5])]
            daily_efc_high_df = daily_efc_df.loc[daily_efc_df["efc"].isin([1, 2, 3])]

            # daily_exlow_tab_df = stats_table(daily_efc_exlow_df)
            # daily_exlow_tab_df['time'] = 'exlow'
            # daily_exlow_tab_df[['NSE','KGE']] = np.nan

            daily_low_tab_df = stats_table(daily_efc_low_df)
            daily_low_tab_df["time"] = "low"
            daily_low_tab_df[["NSE", "KGE"]] = np.nan

            daily_high_tab_df = stats_table(daily_efc_high_df)
            daily_high_tab_df["time"] = "high"
            daily_high_tab_df[["NSE", "KGE"]] = np.nan

            all_df = pd.concat(
                [
                    daily_df,
                    daily_low_tab_df,
                    daily_high_tab_df,
                    monthly_df,
                    annual_df,
                ]
            )
            all_df.set_index("time", inplace=True)
            stats_table_df = all_df.T
            # stats_table_df

            stats_table_obj = go.Figure(
                data=[
                    go.Table(
                        header=dict(
                            values=[
                                "Statistic",
                                "Daily",
                                "Low",
                                "High",
                                "Monthly",
                                "Annual",
                            ]
                        ),
                        cells=dict(
                            values=[
                                stats_table_df.index,
                                stats_table_df.daily,
                                stats_table_df.low,
                                stats_table_df.high,
                                stats_table_df.monthly,
                                stats_table_df.annual,
                            ]
                        ),
                    )
                ]
            )

            #######################################################

            obs_data = daily_efc_df.discharge.sample(
                n=n, replace=False, random_state=3  # frac=0.25,
            )
            sim_data = daily_efc_df.seg_outflow.sample(
                n=n, replace=False, random_state=3  # frac=0.25,
            )

            obs_sort = np.sort(obs_data)[::-1]
            sim_sort = np.sort(sim_data)[::-1]
            obs_color_sort = daily_efc_df.sort_values("discharge")[
                ::-1
            ]  # Makes the color value sort in same order for use in plot.

            obs_exceedence = np.arange(1.0, len(obs_sort) + 1) / len(obs_sort)
            sim_exceedence = np.arange(1.0, len(sim_sort) + 1) / len(sim_sort)

            efc_colors = {
                1: "rgba(0, 191, 255, 0.5)",  # Large Floods
                0: "white",
                2: "rgba(0, 191, 255, 0.5)",  # Small Floods
                3: "rgba(0, 191, 255, 0.5)",  # High Flow Pulse
                4: "rgba(255, 0, 0, 0.5)",  # Low
                5: "rgba(255, 0, 0, 0.5)",  # Extreemly Low
                np.nan: "yellow",
            }  # missing
            # or ...color_discrete_sequence = plotly.colors.sequential.Viridis

            custom_marker_color = obs_color_sort["efc"].map(efc_colors)

            exceed_plot = [
                go.Scatter(
                    x=obs_exceedence,
                    y=obs_sort,
                    mode="markers",
                    name="Observed flow",
                    marker=dict(color=custom_marker_color, size=3),
                    showlegend=False,
                    # line = dict(color='deepskyblue',
                    #    width=3,
                    # dash='dot'
                    # )
                ),
                go.Scatter(
                    x=sim_exceedence,
                    y=sim_sort,
                    mode="lines",
                    name="NHM simulated flow",
                    showlegend=False,
                    # marker=dict(#color='brown',
                    #            size=1),
                    line=dict(
                        color="black",
                        width=1,
                        # dash='dot'
                    ),
                ),
            ]

            exceed_fig = go.Figure(data=exceed_plot)

            # fig.update_yaxes(title_text=f'Streamflow, {getattr(model_output, "seg_outflow").units}', title_font_color = 'black', row=1, col=3)
            # fig.update_xaxes(title_text="Exceedence, probability", title_font_color = 'black', row=1, col=3)

            fig.update_yaxes(type="log", col=2)

            tickvals = [
                0,
                1,
                2,
                5,
                10,
                20,
                50,
                100,
                200,
                500,
                1000,
                2000,
                5000,
                10000,
                20000,
                50000,
                100000,
                200000,
                500000,
                1000000,
            ]

            tickvals_exceed = [0, 0.25, 0.5, 0.75, 1]

            fig.update_xaxes(
                tickvals=tickvals_exceed,
                ticks="inside",
                tickwidth=2,
                tickcolor="black",
                showticklabels=True,
                ticklen=10,
                col=2,
            )
            fig.update_yaxes(
                tickvals=tickvals,
                ticks="inside",
                tickwidth=2,
                tickcolor="black",
                ticklen=10,
                col=2,
            )

            fig.update_xaxes(
                showline=True,
                linewidth=2,
                linecolor="black",
                gridcolor="lightgrey",
                range=[-0.1, 1.1],
                col=2,
            )
            fig.update_yaxes(
                showline=True,
                linewidth=2,
                linecolor="black",
                gridcolor="lightgrey",
                col=2,
            )

            #######################################################
            # Add plots and stats tables to figure
            daily_fig = go.Figure(data=daily_plots)

            for t in annual_fig.data:
                fig.append_trace(t, row=1, col=1)
            for t in monthly_fig.data:
                fig.append_trace(t, row=2, col=1)
            for t in daily_fig.data:
                fig.append_trace(t, row=3, col=1)
            for t in exceed_fig.data:
                fig.append_trace(t, row=1, col=2)
            for t in stats_table_obj.data:
                fig.append_trace(t, row=3, col=2)

            # # Creating the html code for the plotly plot
            # text_div = plotly.offline.plot(fig, include_plotlyjs=False, output_type="div")

            # # Saving the plot as txt file with the html code
            # # idx = 1
            # with open(Folium_maps_dir / f"streamflow_{poi_id_sel}.txt", "w") as f:
            #     f.write(text_div)

            fig.write_html(Folium_maps_dir / f"streamflow_{poi_id_sel}.html")

            plotly.offline.plot(fig, filename=f"{plot_file_path}")

    return plot_file_path