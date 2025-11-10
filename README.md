# Earthquake Decision Support System

A Streamlit-based interactive dashboard for real-time earthquake monitoring, analysis, and decision support for geologists and emergency management experts.

## Overview

### The Earthquake Decision Support System is an interactive web dashboard that allows experts to:
Monitor recent and historical earthquake events.  
Identify high-risk regions and active aftershock clusters.  
Analyze earthquake trends over time.  
Examine relationships between depth, magnitude, and risk levels.  
Make informed decisions based on key metrics and visualizations.  
The dashboard is built with Python, Streamlit, Pandas, and Plotly, and provides an intuitive interface for exploration and decision-making.  

## Features

### Executive Summary Metrics: Total events, critical events (M≥6.5), events in the last 24h, average and maximum magnitudes
### Top Affected Regions: Displays the top 3 regions by number of earthquakes
### Current Alerts: Highlights high-risk events in the last 24 hours

## Risk Trends:

Pie chart for risk level distribution  
Hourly and daily event trends  
Magnitude over time visualization  

## Depth Analysis:

Scatter plot of Depth vs Magnitude  
Line chart showing average magnitude by depth range  
### Geospatial Visualization:
Interactive map showing earthquake locations, magnitude, and risk levels  
Aftershock cluster detection (events within 24h of a previous quake)  

## Decision Support:

Recommended actions based on recent events and clusters  
Priority metrics for risk monitoring  
Data Export: Download filtered earthquake dataset as CSV  
