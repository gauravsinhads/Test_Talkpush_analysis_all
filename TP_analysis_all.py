import streamlit as st
import pandas as pd
import plotly.express as px
import re
import numpy as np

# Set page config
st.set_page_config(page_title="iQor Talkpush Dashboard", layout="wide" )

# Custom CSS for button styling
st.markdown("""
<style>
    /* Button container styling */
    .sidebar .sidebar-content .block-container {
        display: flex;
        flex-direction: column;
        gap: 0.2rem;
    }
    
    /* Button styling */
    div.stButton > button {
        width: 80%;
        border-radius: 4px 4px 0 0;
        border: 1px solid #e0e0e0;
        background-color: #E53855;
        color: white;
        text-align: left;
        padding: 8px 12px;
        margin: 0;
    }
    
    /* Selected button styling */
    div.stButton > button:focus {
        background-color: #2F76B9;
        border-bottom: 2px solid #F5F5F5;
        font-weight: bold;
    }
    
    /* Hover effect */
    div.stButton > button:hover {
        background-color: #e9ecef;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for page navigation
if 'page' not in st.session_state:
    st.session_state.page = 'Home'

# Set up input widgets
st.logo(image="Images/Iqorlogo.png", 
        icon_image="Images/iQor-corporate.png")    

# Sidebar navigation buttons
st.sidebar.title("Pages")

def set_page(page_name):
    st.session_state.page = page_name

pages = ["Home", "Candidate Info", "Talkscore Analysis", "Failure Reasons", "CEFR Dive","HM actions"]

for page in pages:
    st.sidebar.button(
        page,
        on_click=set_page,
        args=(page,),
        key=page
    )
#PAGE HOME_____________________________________________________________________________________________    
# Page content
if st.session_state.page == "Home":
    st.title("Overview data")

    # bar dropdown
    col = st.columns(3)
    with col[2]: aggregation_option = st.selectbox("Time Period", [ "Last 12 Months","Last 12 Weeks","Last 30 days"])
    today = pd.Timestamp.today() # Get today's date
    # Load data
    @st.cache_data
    def load_data(): return pd.read_csv("TP_raw_data1.csv")
    df = load_data()
    
    df["DATE_DAY"] = pd.to_datetime(df["DATE_DAY"])
    custom_colors = ["#2F76B9",	"#3B9790", "#F5BA2E", "#6A4C93", "#F77F00", "#B4BBBE","#e6657b", "#026df5","#5aede2"]
    # Apply Aggregation based on Selection
    if aggregation_option == "Last 12 Months":
        df["DATE_GROUP"] = df["DATE_DAY"].dt.to_period('M').dt.to_timestamp()  # Format as Feb-2024
    elif  aggregation_option == "Last 12 Weeks":
        df["DATE_GROUP"] = df["DATE_DAY"] + pd.to_timedelta(6 - df["DATE_DAY"].dt.weekday, unit="D")
    else:
        df["DATE_GROUP"] = pd.to_datetime(df["DATE_DAY"], format='%b-%d-%Y')
    # Apply Aggregation based on Selection2
    if aggregation_option == "Last 30 days":
        df = df[df["DATE_DAY"] >= today - pd.Timedelta(days=30)]
    elif  aggregation_option == "Last 12 Weeks":
        df = df[df["DATE_DAY"] >= today - pd.Timedelta(weeks=12)]
    else:
        df["DATE_GROUP2"] = pd.to_datetime(df["DATE_DAY"], format='%b-%d-%Y')

    df_fil = df[df["TALKSCORE_OVERALL"] > 0]

    # Calculate metrics of scorecard
    ts_overall = df_fil["TALKSCORE_OVERALL"].mean()
    count_leads = df["DATE_DAY"].count()
    
    Cols_b = st.columns(2)
    with Cols_b[0]:
        st.metric(label="Total Average Talkscore Overall", value=f"{ts_overall:,.2f}")
    with Cols_b[1]:
        st.metric(label="Total count of  leads", value=f"{count_leads:,.0f}")

    # FIG1 Aggregate Data
    df_avg_overall = df_fil.groupby("DATE_GROUP", as_index=False)["TALKSCORE_OVERALL"].mean()
    df_avg_overall["TEXT_LABEL"] = df_avg_overall["TALKSCORE_OVERALL"].apply(lambda x: f"{x:.2f}")
    # FIG2 count of leads
    df_CountLeads = df.groupby(["DATE_GROUP"], as_index=False)["DATE_DAY"].count()

    # Create metrics columns
    cols = st.columns(2)
    with cols[0]:
        st.subheader("Average Talkscore Overall")
        st.line_chart(df_avg_overall.set_index("DATE_GROUP")["TALKSCORE_OVERALL"], 
                 height=300, use_container_width=True,color= '#3B9790' )
    with cols[1]:
        st.subheader("Trend of Lead Counts")
        st.area_chart(df_CountLeads.set_index("DATE_GROUP")["DATE_DAY"],
                 height=300, use_container_width=True, color= '#3B9790')
        
    # Calculate metrics of scorecard 2  
    ts_vocab = df_fil["TALKSCORE_VOCAB"].mean()
    ts_fluency = df_fil["TALKSCORE_FLUENCY"].mean()
    ts_Grammar = df_fil["TALKSCORE_GRAMMAR"].mean()
    ts_pronun = df_fil["TALKSCORE_PRONUNCIATION"].mean()

    Cols_c = st.columns(4)
    with Cols_c[0]:
        st.metric(label="Total Average Talkscore Vocabulary", value=f"{ts_vocab:,.2f}")
    with Cols_c[1]:
        st.metric(label="Total Average Talkscore Fluency", value=f"{ts_fluency:,.2f}")
    with Cols_c[2]:
        st.metric(label="Total Average Talkscore Grammar", value=f"{ts_Grammar:,.2f}")
    with Cols_c[3]:
        st.metric(label="Total Average Talkscore Pronunciation", value=f"{ts_pronun:,.2f}")

    #FIG2 and FIG2w column stacked avg components
    score_columns = ["TALKSCORE_VOCAB", "TALKSCORE_FLUENCY", "TALKSCORE_GRAMMAR", "TALKSCORE_PRONUNCIATION"]
    df_fil[score_columns] = df_fil[score_columns].apply(pd.to_numeric, errors="coerce")
            # Group by DATE_GROUP and compute averages
    group_avg = df_fil.groupby("DATE_GROUP")[score_columns].mean().reset_index()
            # Melt the DataFrame for Plotly
    df_avg_components = group_avg.melt(id_vars=["DATE_GROUP"],  value_vars=score_columns, var_name="Score Type",  value_name="Average Score")
    df_avg_components["TEXT_LABEL"] = df_avg_components["Average Score"].apply(lambda x: f"{x:.2f}")
        # FIG 2: Stacked Column (Component Breakdown)
    fig2 = px.line(df_avg_components, 
        x="DATE_GROUP",     y="Average Score", 
        color="Score Type",  # Different lines for each component
        markers=True, title="Talkscore Components Month over Month", labels={"DATE_GROUP": "Time", "Average Score": "Score"},
        line_shape="linear",  text="TEXT_LABEL" ) # Show values on points
     # Position text labels on the chart
    fig2.update_traces(textposition="top center") 
    # Display Charts
    st.plotly_chart(fig2)

    #FIG 3 Uncompleted and completed test
        # Create calculated fields
    test_summary = df.groupby(["DATE_GROUP", "CAMP_SITE"], as_index=False)["TEST_COMPLETED"].sum()

    # FIG 3 Create Line Chart
    fig3 =  px.bar(test_summary,
        x="DATE_GROUP", y="TEST_COMPLETED", 
        color="CAMP_SITE",  text="TEST_COMPLETED",
        barmode="group",  title="Test Completion Status",
        labels={"TEST_COMPLETED": "Total Tests Completed", "DATE_GROUP": "time", "CAMP_SITE": "Camp Site"} ,
        color_discrete_sequence=custom_colors    )
        # Format labels (rounded values)
    fig3.update_traces(textposition="inside")
    fig3.update_layout(xaxis_title="time", yaxis_title="Total Test Completed", bargap=0.2)
    
    # Display Charts
    st.plotly_chart(fig3)

    # FIG 4 Create calculated fields - calculate percentages
    total_tests = df.groupby("DATE_GROUP", as_index=False)["TEST_COMPLETED"].count()
    test_summary = test_summary.merge(total_tests, on="DATE_GROUP", suffixes=('', '_TOTAL'))
    test_summary['PERCENTAGE_COMPLETED'] = (test_summary['TEST_COMPLETED'] / test_summary['TEST_COMPLETED_TOTAL']) * 100
    # FIG 4 Create Line Chart
    fig4 = px.line(test_summary,
        x="DATE_GROUP", y="PERCENTAGE_COMPLETED", 
        color="CAMP_SITE", 
        markers=True,  # Add markers to each data point
        title="Test Completion Status (%)",
        labels={"PERCENTAGE_COMPLETED": "Percentage of Tests Completed", "DATE_GROUP": "Time", 
            "CAMP_SITE": "Camp Site"},
            color_discrete_sequence=custom_colors)
    # Format y-axis as percentage
    fig4.update_layout(xaxis_title="Time", yaxis_title="Percentage of Tests Completed", yaxis_ticksuffix="%")
    # Add data labels (percentage values)
    fig4.update_traces(text=test_summary['PERCENTAGE_COMPLETED'].round(1),
        textposition="top center")
    # Display Charts
    st.plotly_chart(fig4)

    # FIG 5
    df5_TSreviewM = df.groupby(["DATE_GROUP"], as_index=False)["FOR_TS_REVIEW"].sum()
    #fig
    fig5 = px.line(df5_TSreviewM,
                x="DATE_GROUP", y="FOR_TS_REVIEW", title="For TS Review Monthly"
                ,markers=True,labels={"DATE_GROUP": "Time", "FOR_TS_REVIEW": "For TS Review"}
                ,line_shape="linear",text="FOR_TS_REVIEW")
    fig5.update_traces(textposition="top center")
    # Display Charts
    st.plotly_chart(fig5)

    #FIG 6
    df6_counts = df.groupby(["DATE_GROUP", "NEW_SOURCE"]).size().reset_index(name="COUNT")
    df6_counts["PERCENTAGE"] = df6_counts.groupby("DATE_GROUP")["COUNT"].transform(lambda x: x / x.sum() * 100)

    fig6 = px.bar(df6_counts, 
        x="DATE_GROUP", y="PERCENTAGE", 
        color="NEW_SOURCE", text=df6_counts["PERCENTAGE"].apply(lambda x: f"{x:.1f}%"),
        title="100% Stacked Column Chart",
        labels={"PERCENTAGE": "Percentage", "DATE_GROUP": "time", "NEW_SOURCE": "Source"} ,
         color_discrete_sequence=custom_colors )
    fig6.update_layout(barmode="stack", yaxis=dict(tickformat=".0%"), height=500)
    # Display Charts
    st.plotly_chart(fig6)

#PAGE 1_______________________________________________________________________________________________
elif st.session_state.page == "Candidate Info":

    st.title("Candidate Info")
    # Load data
    tpci = pd.read_csv("TalkpushCI_data_fetch.csv")
    tpci['INVITATIONDT'] = pd.to_datetime(tpci['INVITATIONDT'])
    
    # Define colors for graphs
    colors = ["#001E44", "#F5F5F5", "#E53855", "#B4BBBE", "#2F76B9", "#3B9790", "#F5BA2E", "#6A4C93", "#F77F00"]
    
    # Sidebar dropdown
    col = st.columns(3)
    with col[2]:
        st.header("Select Time Period")
        time_filter = st.selectbox("Time Period", ["Last 30 days", "Last 12 Weeks", "Last 1 Year", "All Time"])
    
    # Filter data based on selection
    max_date = tpci['INVITATIONDT'].max()
    if time_filter == "Last 30 days":
        filtered_data = tpci[tpci['INVITATIONDT'] >= max_date - pd.DateOffset(days=30)]
        date_freq = 'D'
    elif time_filter == "Last 12 Weeks":
        filtered_data = tpci[tpci['INVITATIONDT'] >= max_date - pd.DateOffset(weeks=12)]
        date_freq = 'W'
    elif time_filter == "Last 1 Year":
        filtered_data = tpci[tpci['INVITATIONDT'] >= max_date - pd.DateOffset(years=1)]
        date_freq = 'M'
    else:
        filtered_data = tpci.copy()
        date_freq = 'M'
    
    # Graph 1: Lead Count Trend
    #lead_trend = filtered_data.resample(date_freq, on='INVITATIONDT').count()
    #fig1 = px.line(lead_trend, x=lead_trend.index, y='RECORDID', title='Lead Count Trend', labels={'RECORDID': 'Counts'}, color_discrete_sequence=[colors[0]])
    #st.plotly_chart(fig1, use_container_width=True)
    
    # Graph 2: Top 10 Campaign Titles
    top_campaigns = filtered_data['CAMPAIGNTITLE'].value_counts().nlargest(10)
    fig2 = px.bar(top_campaigns, x=top_campaigns.index, y=top_campaigns.values, title='Top 10 Campaign Titles', labels={'y': 'Counts'}, color_discrete_sequence=[colors[2]])
    st.plotly_chart(fig2, use_container_width=True)
    
    # Graph 3: Top 10 Source Counts
    top_sources = filtered_data['SOURCE'].value_counts().nlargest(10)
    fig3 = px.bar(top_sources, x=top_sources.index, y=top_sources.values, title='Top 10 Source Counts', labels={'y': 'Counts'}, color_discrete_sequence=[colors[3]])
    st.plotly_chart(fig3, use_container_width=True)
    
    # Graph 4: Top 10 Assigned Manager Counts
    top_managers = filtered_data['ASSIGNEDMANAGER'].value_counts().nlargest(10)
    fig4 = px.bar(top_managers, x=top_managers.index, y=top_managers.values, title='Top 10 Assigned Manager Counts', labels={'y': 'Counts'}, color_discrete_sequence=[colors[4]])
    st.plotly_chart(fig4, use_container_width=True)
    
    # Graph 5: Top 10 Folder Occurrences
    top_folders = filtered_data['FOLDER'].value_counts().nlargest(10)
    fig5 = px.bar(top_folders, x=top_folders.index, y=top_folders.values, title='Top 10 Folder Occurrences', labels={'y': 'Counts'}, color_discrete_sequence=[colors[5]])
    st.plotly_chart(fig5, use_container_width=True)
    
    # Graph 6: Top 5 Completion Methods
    top_completion_methods = filtered_data['COMPLETIONMETHOD'].value_counts().nlargest(5)
    fig6 = px.bar(top_completion_methods, x=top_completion_methods.index, y=top_completion_methods.values, title='Top 5 Completion Methods', labels={'y': 'Counts'}, color_discrete_sequence=[colors[6]])
    st.plotly_chart(fig6, use_container_width=True)
    
    # Graph 7: Repeat Application Counts
    repeat_applications = filtered_data[filtered_data['REPEATAPPLICATION'] == 't'].resample(date_freq, on='INVITATIONDT').count()
    fig7 = px.bar(repeat_applications, x=repeat_applications.index, y='REPEATAPPLICATION', title='Repeat Application Counts', labels={'REPEATAPPLICATION': "Counts-'REPEATAPPLICATION'"}, color_discrete_sequence=[colors[7]])
    st.plotly_chart(fig7, use_container_width=True)
    
    # Graph 8: Top 5 Campaign Type Occurrences
    top_campaign_types = filtered_data['CAMPAIGN_TYPE'].value_counts().nlargest(5)
    fig8 = px.bar(top_campaign_types, x=top_campaign_types.index, y=top_campaign_types.values, title='Top 5 Campaign Type Occurrences', labels={'y': 'Counts'}, color_discrete_sequence=[colors[8]])
    st.plotly_chart(fig8, use_container_width=True)
    
    # Graph 9: Lead Counts by Campaign Site
    top_campaign_sites = filtered_data['CAMPAIGN_SITE'].value_counts().nlargest(5)
    fig9 = px.bar(top_campaign_sites, x=top_campaign_sites.index, y=top_campaign_sites.values, title='Lead Counts by Campaign Site', labels={'y': 'Counts'}, color_discrete_sequence=[colors[0]])
    st.plotly_chart(fig9, use_container_width=True)
#________________________________________________________________________________________________________________________________________    

elif st.session_state.page == "Talkscore Analysis":
    st.title("Talkscore Analysis")
    import streamlit as st
    import pandas as pd
    import plotly.express as px
    import plotly.figure_factory as ff
    
    # Load data
    TPSC1 = pd.read_csv('TalkpushCI_SC1.csv')
    TPSC1['INVITATIONDT_UTC'] = pd.to_datetime(TPSC1['INVITATIONDT_UTC'])
    TPSC1 = TPSC1[TPSC1['TALKSCORE_OVERALL'] > 0]
    
    # Dropdown options
    options = {"Last 30 days": 30, "Last 12 Weeks": 84, "Last 1 Year": 365, "All Time": None}
    selection = st.selectbox("Select Time Period", list(options.keys()))
    
    # Filter data based on selection
    if options[selection]:
        start_date = pd.Timestamp.today() - pd.Timedelta(days=options[selection])
        filtered_df = TPSC1[TPSC1['INVITATIONDT_UTC'] >= start_date]
    else:
        filtered_df = TPSC1
    
    # Define colors
    colors = ["#001E44", "#F5F5F5", "#E53855", "#B4BBBE", "#2F76B9", "#3B9790", "#F5BA2E", "#6A4C93", "#F77F00"]
    
    # Graph 1: Top 5 Rejection Reasons
    st.subheader("Top 5 Rejection Reasons")
    if 'REJECTED_REASON' in filtered_df.columns:
        rejection_counts = filtered_df['REJECTED_REASON'].value_counts().nlargest(5)
        fig1 = px.bar(x=rejection_counts.index, y=rejection_counts.values, 
                      labels={'x': 'Rejection Reason', 'y': 'Count'}, color=rejection_counts.index,
                      color_discrete_sequence=colors[:5])
        st.plotly_chart(fig1)
    else:
        st.write("No rejection reasons available in the dataset.")
    
    # Graph 2: Correlation Heatmap of Talkscore Variables
    st.subheader("Correlation Heatmap of Talkscore Variables")
    talkscore_vars = ['TALKSCORE_VOCAB', 'TALKSCORE_FLUENCY', 'TALKSCORE_GRAMMAR',
                      'TALKSCORE_COMPREHENSION', 'TALKSCORE_PRONUNCIATION', 'TALKSCORE_OVERALL']
    if all(var in filtered_df.columns for var in talkscore_vars):
        corr_matrix = filtered_df[talkscore_vars].corr().round(2)
        fig2 = ff.create_annotated_heatmap(z=corr_matrix.values, x=talkscore_vars, y=talkscore_vars,
                                           annotation_text=corr_matrix.round(2).astype(str).values,
                                           colorscale='Blues', showscale=True)
        st.plotly_chart(fig2)
    else:
        st.write("Talkscore variables not available in the dataset.")
        
#____________________________________________________________________________________________________________________________________

elif st.session_state.page == "Failure Reasons":
    st.title("Failure Reasons")

    col = st.columns(3)
    with col[2]: aggregation_option = st.selectbox("Time Period", [ "Last 12 Months","Last 12 Weeks","Last 30 days"])
    today = pd.Timestamp.today() # Get today's date
    # Load data
    @st.cache_data
    def load_data(): return pd.read_csv("Failure_Reasons.csv")
    df = load_data()
    
    df["DATE_DAY"] = pd.to_datetime(df["DATE_DAY"])
    
    # Apply Aggregation based on Selection
    if aggregation_option == "Last 12 Months":
        df["DATE_GROUP"] = df["DATE_DAY"].dt.to_period('M').dt.to_timestamp()  # Format as Feb-2024
    elif  aggregation_option == "Last 12 Weeks":
        df["DATE_GROUP"] = df["DATE_DAY"] + pd.to_timedelta(6 - df["DATE_DAY"].dt.weekday, unit="D")
    else:
        df["DATE_GROUP"] = pd.to_datetime(df["DATE_DAY"], format='%b-%d-%Y')
    # Apply Aggregation based on Selection2
    if aggregation_option == "Last 30 days":
        df = df[df["DATE_DAY"] >= today - pd.Timedelta(days=30)]
    elif  aggregation_option == "Last 12 Weeks":
        df = df[df["DATE_DAY"] >= today - pd.Timedelta(weeks=12)]
    else:
        df["DATE_GROUP2"] = pd.to_datetime(df["DATE_DAY"], format='%b-%d-%Y')

    # 📌 Table 1 : Count of FAILED_REASON by TALKSCORE_CEFR
    pivot_count = df.pivot_table(index="FAILED_REASON", columns=["DATE_GROUP", "CEFR"], aggfunc="size", fill_value=0)
    pivot_count = pivot_count.reindex(sorted(pivot_count.columns, key=lambda x: pd.to_datetime(x[0], format="%b-%y")), axis=1)
    pivot_count.reset_index(inplace=True)
       
    #Show the table
    st.subheader("Count of FAILED_REASON by TALKSCORE_CEFR")
    st.dataframe(pivot_count, use_container_width=True)

    # 📌 Table 2 : Average TALKSORES by FAILED_REASON
    pivot_avg2  = df.groupby(["DATE_GROUP", "FAILED_REASON"])[["VOC", "FLU", "GRAM", "PRON", "OVERALL"]].mean().reset_index()
    pivot_avg2["VOC"]  = pivot_avg2["VOC"].apply(lambda x: f"{x:.2f}")
    pivot_avg2["FLU"]  = pivot_avg2["FLU"].apply(lambda x: f"{x:.2f}")
    pivot_avg2["GRAM"] = pivot_avg2["GRAM"].apply(lambda x: f"{x:.2f}")
    pivot_avg2["PRON"] = pivot_avg2["PRON"].apply(lambda x: f"{x:.2f}")
    pivot_avg2["_OVERALL"] = pivot_avg2["OVERALL"].apply(lambda x: f"{x:.2f}")
    ## Pivot Monthly Table
    pvt_avg2 = pivot_avg2.pivot(index="FAILED_REASON", columns="DATE_GROUP", values=["VOC", "FLU", "GRAM", "PRON", "OVERALL"])
    pvt_avg2 = pvt_avg2.sort_index(axis=1, level=1)
    # Ensure DATE_GROUP is formatted correctly in column names
    pvt_avg2.columns = pd.MultiIndex.from_tuples([(col[0], col[1].strftime('%b-%d-%Y')) for col in pvt_avg2.columns])
    # Reset index and swap levels for better readability
    pvt_avg2.reset_index(inplace=True)
    pvt_avg2 = pvt_avg2.swaplevel(axis=1)
    # Show the table
    st.subheader("Average TALKSORES by FAILED_REASON")
    st.dataframe(pvt_avg2, use_container_width=True)

    
#____________________________________________________________________________________________________________________________________
elif st.session_state.page == "CEFR Dive":
    st.title("CEFR Dive")
    
    col = st.columns(3)
    with col[2]: aggregation_option = st.selectbox("Time Period", [ "Last 12 Months","Last 12 Weeks","Last 30 days"])
    today = pd.Timestamp.today() # Get today's date
    # Load data
    @st.cache_data
    def load_data(): return pd.read_csv("TP_raw_data1.csv")
    df = load_data()
    
    df["DATE_DAY"] = pd.to_datetime(df["DATE_DAY"])
    
    # Apply Aggregation based on Selection
    if aggregation_option == "Last 12 Months":
        df["DATE_GROUP"] = df["DATE_DAY"].dt.to_period('M').dt.to_timestamp()  # Format as Feb-2024
    elif  aggregation_option == "Last 12 Weeks":
        df["DATE_GROUP"] = df["DATE_DAY"] + pd.to_timedelta(6 - df["DATE_DAY"].dt.weekday, unit="D")
    else:
        df["DATE_GROUP"] = pd.to_datetime(df["DATE_DAY"], format='%b-%d-%Y')
    # Apply Aggregation based on Selection2
    if aggregation_option == "Last 30 days":
        df = df[df["DATE_DAY"] >= today - pd.Timedelta(days=30)]
    elif  aggregation_option == "Last 12 Weeks":
        df = df[df["DATE_DAY"] >= today - pd.Timedelta(weeks=12)]
    else:
        df["DATE_GROUP2"] = pd.to_datetime(df["DATE_DAY"], format='%b-%d-%Y')

    df_fil = df[df["TALKSCORE_OVERALL"] > 0]

    # Calculate metrics of scorecard

    #FIG calculate dataframe for CEFR
    df_cefr_count = df_fil.groupby(["DATE_GROUP", "TALKSCORE_CEFR"]).size().reset_index(name="Count")
        #FIG 1 TALKSCORE_CEFR over the time
    custom_colors = ["#2F76B9",	"#3B9790", "#F5BA2E", "#6A4C93", "#F77F00", "#B4BBBE","#e6657b", "#026df5","#5aede2"]

    CEFR_Monthly = px.bar(df_cefr_count, 
        x="DATE_GROUP", y="Count", 
        color="TALKSCORE_CEFR",  # Different colors for each CEFR level
        barmode="stack", title="Distribution of TALKSCORE_CEFR Levels",
        labels={"DATE_GROUP": "time", "Count": "Number of Candidates"},
        text_auto=True,color_discrete_sequence=custom_colors ) # Show counts on bars
    # display chart
    st.plotly_chart(CEFR_Monthly, use_container_width=True)

    # FIG 2 Group by TALKSCORE_CEFR and calculate min, max, and count
    cefr_summary = df_fil.groupby(["DATE_GROUP", "TALKSCORE_CEFR"]).agg(
        Min_=("TALKSCORE_OVERALL", "min"),
        Max_=("TALKSCORE_OVERALL", "max"),
        Count=("TALKSCORE_CEFR", "count")).reset_index()
    # FIG 2 Pivot the table so that MONTHLY_ is the top-level column
        #  MONTHLY_ is the top-level column and stats are below
    cefr_summary_pivot = cefr_summary.pivot(index="TALKSCORE_CEFR", columns="DATE_GROUP", values=["Min_", "Max_", "Count"])
    cefr_summary_pivot = cefr_summary_pivot.sort_index(axis=1, level=1)
        # Rename columns: Convert dates back to string format (e.g., "Feb-25") and keep hierarchical structure
    cefr_summary_pivot.columns = pd.MultiIndex.from_tuples([(col[0], col[1].strftime('%b-%d-%Y')) for col in cefr_summary_pivot.columns])
    cefr_summary_pivot.reset_index(inplace=True)
    cefr_summary_pivot = cefr_summary_pivot.swaplevel(axis=1)
    
    st.subheader("Talkscore Overall Summary by CEFR (Min–Max)")
    st.dataframe(cefr_summary_pivot)

#____________________________________________________________________________________________________________________________________
elif st.session_state.page == "HM actions":
    st.title("HM actions")

    col = st.columns(3)
    with col[2]: aggregation_option = st.selectbox("Time Period", [ "Last 12 Months","Last 12 Weeks","Last 30 days"])
    today = pd.Timestamp.today() # Get today's date
    # Load data
    @st.cache_data
    def load_data(): return pd.read_csv("Folder_Logs.csv")
    df = load_data()
    
    df["DATE_DAY"] = pd.to_datetime(df["DATE_DAY"])
    
    # Apply Aggregation based on Selection
    if aggregation_option == "Last 12 Months":
        df["DATE_GROUP"] = df["DATE_DAY"].dt.to_period('M').dt.to_timestamp()  # Format as Feb-2024
    elif  aggregation_option == "Last 12 Weeks":
        df["DATE_GROUP"] = df["DATE_DAY"] + pd.to_timedelta(6 - df["DATE_DAY"].dt.weekday, unit="D")
    else:
        df["DATE_GROUP"] = pd.to_datetime(df["DATE_DAY"], format='%b-%d-%Y')
    # Apply Aggregation based on Selection2
    if aggregation_option == "Last 30 days":
        df = df[df["DATE_DAY"] >= today - pd.Timedelta(days=30)]
    elif  aggregation_option == "Last 12 Weeks":
        df = df[df["DATE_DAY"] >= today - pd.Timedelta(weeks=12)]
    else:
        df["DATE_GROUP2"] = pd.to_datetime(df["DATE_DAY"], format='%b-%d-%Y')

    df_f = df[df["MOVED_BY"] == "Manager" ]    

    # Group by month,and weeky
    df_rej = df.groupby(["DATE_GROUP"], as_index=False)[['REJECTED_BY_MANAGER', 'MOVED_BY_MANAGER']].sum()
    # Calculate rejection percentage
    df_rej['REJECT_PERCENT'] = (df_rej['REJECTED_BY_MANAGER'] / df_rej['MOVED_BY_MANAGER']) * 100
    #Create column with text type
    df_rej["TEXT_LABEL"] = df_rej["REJECT_PERCENT"].apply(lambda x: f"{x:.2f}%")
    # creation of the plot
    fig1 = px.line(df_rej, 
               x="DATE_GROUP", 
               y="REJECT_PERCENT",
               markers=True,  # Add points (vertices)
               title="Reject % Over the time",
               labels={"DATE_GROUP": "Time", "REJECT_PERCENT": "Rejection %"},
               line_shape="linear", 
               text="TEXT_LABEL")  # Use formatted text
        # Update the trace to display the text on the chart
    fig1.update_traces( textposition="top center", fill='tozeroy' , fillcolor="rgba(0, 0, 255, 0.2)")

    st.plotly_chart(fig1, use_container_width=True)

    #FIG 3 
    
    #FIG 3# Normalize the counts per month to percentages
    df3_actions = df_f.groupby(["DATE_GROUP", "FOLDER_TO_TITLE"]).size().reset_index(name="COUNT")
            # Normalize to get percentage per month
    df3_actions["PERCENTAGE"] = df3_actions.groupby("DATE_GROUP")["COUNT"].transform(lambda x: x / x.sum() * 100)
    df3_actions["TEXT_LABEL"] = df3_actions["PERCENTAGE"].apply(lambda x: f"{x:.2f}%")



    fig3 = px.bar(df3_actions, 
    x="DATE_GROUP", y="PERCENTAGE", 
    color="FOLDER_TO_TITLE", text="TEXT_LABEL",
    title="Percentage of actions BY Manager",
    labels={"DATE_GROUP": "Time", "PERCENTAGE": "Percentage", "FOLDER_TO_TITLE": "Actions"} 
    )
    fig3.update_layout(barmode="stack", yaxis=dict(tickformat=".0%"), height=500)

    st.plotly_chart(fig3, use_container_width=True)

    #TABLE
    # Step 1: Clean the MOVER_EMAIL column
    def clean_email(email):
        if pd.isna(email) or not isinstance(email, str):
            return email  # Return as-is if it's NaN or not a string
        return re.sub(r'\+.*?@', '@', email)  # Remove everything between + and @

    # Convert MOVER_EMAIL to string type first (NaN will become 'nan')
    df['CLEANED_MOVER_EMAIL'] = df['MOVER_EMAIL'].astype(str).apply(clean_email)

    # Replace 'nan' with actual NaN if needed
    df['CLEANED_MOVER_EMAIL'] = df['CLEANED_MOVER_EMAIL'].replace('nan', np.nan)

    # Step 2: Group by cleaned MOVER_EMAIL (filter out NaN values if needed)
    df_mover = df.groupby('CLEANED_MOVER_EMAIL')[['REJECTED_BY_MANAGER', 'MOVED_BY_MANAGER']].sum()

    # Step 3: Calculate rejection percentage
    df_mover['REJECT_PERCENT'] = (df_mover['REJECTED_BY_MANAGER'] / df_mover['MOVED_BY_MANAGER']) * 100
    df_mover["REJECT %"] = df_mover["REJECT_PERCENT"].apply(lambda x: f"{x:.2f}%")
    df_mover = df_mover.sort_values(by='REJECTED_BY_MANAGER', ascending=False)
    df_mover = df_mover.reset_index()
    df_mover = df_mover.drop(columns=['REJECT_PERCENT'])

    # Show the table
    st.subheader("Rejection % By Manager")
    st.dataframe(df_mover, use_container_width=True)
# streamlit run TP_analysis_all.py
