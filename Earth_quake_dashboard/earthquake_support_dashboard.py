import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime,timedelta
import warnings

warnings.filterwarnings('ignore')

st.set_page_config(
    page_title='Earthquake Decision Support System',
    layout='wide',
    initial_sidebar_state='expanded'

)

st.title('Earthquake Decision Support Dashboard')
st.markdown(
    '**Real time monitoring, clustering, and decision support for geologists**'
)


uploaded_file=st.file_uploader('Upload earthquake CSV',type=['csv'])


def load_data(uploaded_file):
    df=pd.read_csv(uploaded_file)
    df['time']=pd.to_datetime(df['time'], format='%Y-%m-%d %H:%M:%S.%f',errors='coerce')
    df=df.dropna(subset=['time'])

    df['date']=df['time'].dt.date
    df['year']=df['time'].dt.year
    df['month']=df['time'].dt.month
    df['hour']=df['time'].dt.hour
    df['day_of_the_week']=df['time'].dt.day_name()
    
    df['risk_level']=pd.cut(
        df['magnitude'],
        bins=[0,4.0,5.5,6.5,np.inf],
        labels=['Low','Medium','High','Critical']
    )

    df['tectonic_type']=np.where(
        df['depth'] < 70,'Crustal',
        np.where(
            df['depth'] < 300 ,'Intermediate', 'Deep'
        )
    )

    

    

    def haversine(lat1, lon1, lat2, lon2):
        R = 6371  # Earth radius in km
        # Convert degrees to radians
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    
        dlat = lat2 - lat1
        dlon = lon2 - lon1
    
        a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
        c = 2 * np.arcsin(np.sqrt(a))
    
        return R * c
    
    df=df.sort_values('time').reset_index(drop=True)
    
    df['dist_km'] = haversine(
    df['latitude'], df['longitude'],
    df['latitude'].shift(), df['longitude'].shift() )

    df['dist_km'] = df['dist_km'].fillna(0)

    df['hours_since_prev']=df['time'].diff().dt.total_seconds()/3600
    df['hours_since_prev']=df['hours_since_prev'].fillna(0)

    df['cluster_flag']=(df['hours_since_prev'] <= 24 ) & (df['dist_km'] <= 100 )
    df.loc[0, 'cluster_flag'] = False 
    df['cluster_id'] = (~df['cluster_flag']).cumsum()
    df.loc[df['cluster_flag'] == False, 'cluster_id'] = np.nan

    

    return df

if uploaded_file is not None:
    st.markdown('Uploaded file successfully.')

    with st.spinner('Loading data...'):
        df=load_data(uploaded_file)

    st.sidebar.header('Filters')

    time_window=st.sidebar.selectbox(
        "Time Window",
        ['All time','Last 7 days','Last 30 days','Last 90 days','Custom']
    )

    if time_window=='Custom':
        start_date=st.sidebar.date_input('start',df['date'].min())
        end_date=st.sidebar.date_input('end',df['date'].max())
        filter_df=df[(df['date']>=start_date) & (df['date']<=end_date)]
    else:
        days={'All time':9999 ,'Last 7 days': 7 ,'Last 30 days': 30 , 'Last 90 days':90}
        cutoff=df['time'].max()-timedelta(days=days[time_window])
        filter_df=df[df['time']>=cutoff]


    mag_range=st.sidebar.slider("Magnitude",
        float(df['magnitude'].min()), float(df['magnitude'].max()),
        (float(df['magnitude'].min()),float(df['magnitude'].max())))
    

    depth_range=st.sidebar.slider("Depth(km)",
        float(df['depth'].min()),float(df['depth'].max()),
        (float(df['depth'].min()),float(df['depth'].max()))                          
    )

    risk_levels=st.sidebar.multiselect("Risk Level",
                ['Low','Medium','High','Critical'],
                default=['Medium','High','Critical'])
    
    tectonic_types=st.sidebar.multiselect('Tectonic Type',
                 ['Crustal','Intermediate','Deep'],
                 default=['Crustal','Intermediate','Deep'])
    
    
    filter_df=filter_df[
        (filter_df['magnitude'].between(mag_range[0],mag_range[1]))&
        (filter_df['depth'].between(depth_range[0],depth_range[1]))&
        (filter_df['risk_level'].isin(risk_levels))&
        (filter_df['tectonic_type'].isin(tectonic_types))
    ]
    
    filter_df['region'] = filter_df['place'].str.split(',').str[-1].str.strip()
    region_counts = filter_df.groupby('region').size().reset_index(name='earthquake_count')
    top_regions = region_counts.sort_values(by='earthquake_count', ascending=False).reset_index(drop=True)



    st.markdown("---")
    st.header('Executive Summary')
    col1,col2,col3,col4,col5=st.columns(5)

    total_events=len(filter_df)
    critical_events=len(filter_df[filter_df['risk_level']=='Critical'])
    recent_24h=len(filter_df[filter_df['time'] >= (filter_df['time'].max()-timedelta(hours=24))])
    avg_mag=filter_df['magnitude'].mean()
    max_mag=filter_df['magnitude'].max()


    with col1:

        st.metric('Total Events ',total_events)
    with col2:
        st.metric('Critical (M>=6.5)',critical_events)
    with col3:
        st.metric('Last 24h',recent_24h)
    with col4:
        st.metric('Average Magnitude',f"{avg_mag:.2f}")
    with col5:
        st.metric('Max Magnitude',f"{max_mag:.2f}")


    st.markdown("---")
    st.header("Most Affected Region")
    col1,col2,col3=st.columns(3)
    top_n = min(3, len(top_regions))
    cols = [col1, col2, col3]

    for i in range(top_n):
        with cols[i]:
            st.metric(top_regions['region'].iloc[i], value=int(top_regions['earthquake_count'].iloc[i]))
        


    st.markdown("---")
    st.header("Current Alerts")

    now=datetime.now()

    recent_events=filter_df[filter_df['time']>= (now-timedelta(hours=24))]
    alert_df=recent_events[recent_events['magnitude']>=4.5].copy()
    alert_df['time_ago']=(now-alert_df['time']).dt.total_seconds()/3600

    if len(alert_df) > 0:
        st.error(f"High risk events in last 24h: {len(alert_df)}")
        for _,row in alert_df.head(6).iterrows():
            st.warning(f"**M{row['magnitude']:.1f}** - {row['place'][:50]} | {row['time_ago']:.1f}h ago")
    else:
        st.success("No high-risk events in last 24h")


    


    st.markdown("---")
    st.header('Risk Trends')

    col1,col2=st.columns(2)

    with col1:
        fig_pie=px.pie(
            filter_df['risk_level'].value_counts().reset_index(),
            values='count',
            names='risk_level',
            title='Risk Distribution'
        )

        st.plotly_chart(
            fig_pie,use_container_width='True'
        )

        hourly=filter_df.groupby('hour').size().reset_index(name='count')
        fig_hour=px.bar(
             hourly,x='hour',y='count',title='Events by Hour'
        )

        st.plotly_chart(
            fig_hour,use_container_width='True'
        )



     
        
    with col2:
        daily=filter_df.groupby('date').size().reset_index(name='count')
        fig_daily=px.line(
            daily, x='date',y='count', title='Daily Rate',markers=True
        )
        fig_daily.add_hline(y=daily['count'].mean(),line_dash='dash',annotation_text='Avg')
        st.plotly_chart(fig_daily,use_container_width=True)

        fig_mag=px.scatter(filter_df,x='time',y='magnitude',color='risk_level',
                           color_discrete_map={'Low': '#90EE90', 'Moderate': '#FFD700', 'High': '#FFA500',
                                                 'Critical': '#FF4500'},
                            title="Magnitude Over Time")
        st.plotly_chart(fig_mag, use_container_width=True)




    st.markdown("---")
    st.header("Relation With Depth")

    col1,col2=st.columns(2)
    with col1:
        fig = px.scatter(filter_df, x='depth', y='magnitude',
                 title='Depth vs Magnitude',
                 labels={'depth': 'Depth (km)', 'magnitude': 'Magnitude'},
                 color='magnitude', hover_data=['place'])
        st.plotly_chart(fig,use_container_width=True)


    with col2:
        
        filter_df['depth_bin'] = pd.cut(filter_df['depth'], bins=10)
        avg_mag = filter_df.groupby('depth_bin')['magnitude'].mean().reset_index()
        avg_mag['depth_bin'] = avg_mag['depth_bin'].astype(str)

        fig1 = px.line(
            avg_mag,
            x='depth_bin',
            y='magnitude',
            title='Average Magnitude by Depth Range',
            labels={'depth_bin': 'Depth Range (km)', 'magnitude': 'Avg Magnitude'}
        )

        st.plotly_chart(fig1,use_container_width=True)

       

    st.markdown("---")
    st.header("Risk Map")
    fig_map = px.scatter_mapbox(
        filter_df, lat="latitude", lon="longitude",
        size="magnitude", color="magnitude",
        color_continuous_scale="Reds", size_max=20, opacity=0.8,
        hover_name="place", hover_data=["risk_level", "depth", "time", "tectonic_type"],
        mapbox_style="open-street-map", zoom=3
    )
    fig_map.update_layout(height=600, margin=dict(r=0, t=40, l=0, b=0))
    st.plotly_chart(fig_map, use_container_width=True)

    
     
    st.markdown("---")
    st.header('Aftershock Clusters')
    clusters = filter_df[filter_df['cluster_flag'] == True].copy()
    
    if len(clusters) > 0:
        st.warning(f"{len(clusters)} events in active clusters (within 24h of previous event and 100 km of radius)")

        # Group clusters 
        # clusters['cluster_id'] = ((clusters['hours_since_prev'] > 24) & (clusters['dist_km'] > 100)).cumsum()
        

        #  visible markers
        fig_cluster = px.scatter_mapbox(
            clusters,
            lat="latitude",
            lon="longitude",
            size="magnitude",
            color="magnitude",
            color_continuous_scale="Oranges",
            size_max=25,
            opacity=0.9,
            hover_name="place",
            hover_data={
                "time": "|%Y-%m-%d %H:%M",
                "magnitude": ":.2f",
                "depth": ":.0f",
                "cluster_id": True
            },
            title="Detected Aftershock Clusters",
            mapbox_style="open-street-map"
        )
        fig_cluster.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig_cluster, use_container_width=True)

        # Cluster summary
        cluster_summary = clusters.groupby('cluster_id').agg(
            count=('magnitude', 'size'),
            max_mag=('magnitude', 'max'),
            center_lat=('latitude', 'mean'),
            center_lon=('longitude', 'mean'),
            start_time=('time', 'min')
        ).round(2)
        st.subheader("Cluster Summary")
        st.dataframe(cluster_summary.sort_values('max_mag', ascending=False))

    else:
        st.info("No active aftershock clusters detected (events >24h apart)")

    
    st.markdown("---")
    st.header("Decision Support")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Recommended Actions")
        actions = []
        if recent_24h > 10: actions.append("Increase monitoring frequency")
        if critical_events > 0: actions.append("Issue public safety alerts")
        if len(clusters) > 5: actions.append("Deploy field assessment teams")
        if len(filter_df[filter_df['magnitude'] >= 5.5]) > 3:
            actions.append("Prepare tsunami early warning")

        if actions:
            for a in actions: st.error(a)
        else:
            st.success("No immediate actions required")

    with col2:
        st.subheader("Priority Metrics")
        days_span = max(1, (filter_df['date'].max() - filter_df['date'].min()).days)
        st.metric("Event Rate (/day)", f"{len(filter_df) / days_span:.1f}")
        st.metric("M≥5.0 Events", len(filter_df[filter_df['magnitude'] >= 5.0]))
        st.metric("Deep Events (>300km)", len(filter_df[filter_df['depth'] > 300]))
        st.metric("Active Clusters", len(clusters['cluster_id'].unique()) if len(clusters) > 0 else 0)

    # Download data
    with st.expander("Full Dataset & Export"):
        display_cols = ['time', 'place', 'magnitude', 'depth', 'risk_level', 'tectonic_type', 'cluster_flag']
        st.dataframe(filter_df[display_cols].sort_values('time', ascending=False))
        csv = filter_df[display_cols].to_csv(index=False)
        st.download_button("Download Filtered Data", csv, "filtered_earthquakes.csv", "text/csv")




        


    


