import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from io import BytesIO

# Page setup
st.set_page_config(page_title="Data Visualizer")

# Title
st.title("Data Visualizer")

# Store uploaded datasets in session
if "datasets" not in st.session_state:
    st.session_state.datasets = {}

# Sidebar: Upload dataset
st.sidebar.header("Upload Your Dataset")
uploaded_file = st.sidebar.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx"], key="file_upload")

if uploaded_file:
    file_name = uploaded_file.name
    try:
        if file_name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, encoding='latin1')
        else:
            df = pd.read_excel(uploaded_file)
        st.session_state.datasets[file_name] = df
        st.sidebar.success(f"Loaded: {file_name}")
    except Exception as e:
        st.sidebar.error(f"Failed to load file: {e}")

# Continue only if dataset is available
if st.session_state.datasets:
    dataset_names = list(st.session_state.datasets.keys())
    selected_dataset_name = st.sidebar.selectbox("Select Dataset", dataset_names)
    dataset = st.session_state.datasets[selected_dataset_name]

    # Preview
    if st.checkbox("Show Data Preview"):
        st.subheader(f"Dataset Preview: {selected_dataset_name}")
        st.dataframe(dataset)

    # Column Types
    numeric_cols = dataset.select_dtypes(include='number').columns.tolist()
    categorical_cols = dataset.select_dtypes(include='object').columns.tolist()
    columns = dataset.columns.tolist()

    # Sidebar Filters
    st.sidebar.header("Filter and Grouping Options")

    # Date filtering
    if 'Invoice Date' in dataset.columns:
        dataset['Invoice Date'] = pd.to_datetime(dataset['Invoice Date'], errors='coerce')
        dataset = dataset.dropna(subset=['Invoice Date'])
        min_date = dataset['Invoice Date'].min().date()
        max_date = dataset['Invoice Date'].max().date()
        date_range = st.sidebar.slider(
            "Select Date Range",
            min_value=min_date,
            max_value=max_date,
            value=(min_date, max_date)
        )
        dataset = dataset[
            (dataset['Invoice Date'].dt.date >= date_range[0]) &
            (dataset['Invoice Date'].dt.date <= date_range[1])
        ]

    # Grouping
    group_col = st.sidebar.selectbox("Group By", options=["None"] + columns)
    if group_col != "None":
        dataset = dataset.groupby(group_col).sum(numeric_only=True).reset_index()

    # Sorting
    sort_col = st.sidebar.selectbox("Sort By", options=["None"] + dataset.columns.tolist())
    if sort_col != "None":
        dataset = dataset.sort_values(by=sort_col)

    # Sidebar: Chart selection
    st.sidebar.header("Chart Settings")
    chart_type = st.sidebar.radio(
        "Select a Chart Type",
        ["Bar Chart", "Line Plot", "Pie Chart", "Histogram", "Box Plot", "Heatmap"]
    )

    st.subheader(f"{chart_type}")
    fig, ax = plt.subplots(figsize=(10, 6))

    # LINE PLOT
    if chart_type == "Line Plot":
        selected_line_cols = st.multiselect("Select numeric columns for Line Chart", numeric_cols)
        if selected_line_cols:
            st.line_chart(dataset[selected_line_cols])
        else:
            st.warning("Select at least one numeric column.")

    # BAR CHART
    elif chart_type == "Bar Chart":
        selected_bar_col = st.selectbox("Select a column for Bar Chart", columns)
        if selected_bar_col:
            bar_data = dataset[selected_bar_col].value_counts().head(10).reset_index()
            bar_data.columns = [selected_bar_col, "Count"]

            # Clean category labels to avoid errors like " 0"
            bar_data[selected_bar_col] = bar_data[selected_bar_col].astype(str).str.strip()

            # Use only numeric values for plotting
            st.bar_chart(bar_data.set_index(selected_bar_col)["Count"])

    # HISTOGRAM
    elif chart_type == "Histogram":
        col = st.selectbox("Select column for Histogram", numeric_cols)
        sns.histplot(dataset[col], kde=True, ax=ax)
        st.pyplot(fig)

    # BOX PLOT
    elif chart_type == "Box Plot":
        col = st.selectbox("Select column for Box Plot", numeric_cols)
        sns.boxplot(x=dataset[col], ax=ax)
        st.pyplot(fig)

    # HEATMAP
    elif chart_type == "Heatmap":
        corr = dataset[numeric_cols].corr()
        sns.heatmap(corr, annot=True, cmap='coolwarm', ax=ax)
        st.pyplot(fig)

    # PIE CHART
    elif chart_type == "Pie Chart":
        if categorical_cols and numeric_cols:
            selected_cat_col = st.selectbox("Select a categorical column for Pie Chart", categorical_cols)
            selected_num_col = st.selectbox("Select numeric column", numeric_cols)
            if selected_cat_col in dataset.columns and selected_num_col in dataset.columns:
                pie_data = dataset.groupby(selected_cat_col)[selected_num_col].sum()
                fig4, ax4 = plt.subplots()
                ax4.pie(
                    pie_data,
                    labels=pie_data.index,
                    autopct='%1.1f%%',
                    startangle=90
                )
                ax4.axis('equal')
                st.pyplot(fig4)
        else:
            st.warning("Need both categorical and numeric columns.")

    # DOWNLOAD
    st.subheader("Download Processed Data")

    def convert_df_to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()

    excel_data = convert_df_to_excel(dataset)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "Download as Excel",
            data=excel_data,
            file_name="Processed_Data.xlsx",
            mime="application/vnd.ms-excel"
        )
    with col2:
        csv_data = dataset.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Download as CSV",
            data=csv_data,
            file_name="Processed_Data.csv",
            mime='text/csv'
        )

else:
    st.warning("Please upload a dataset to begin.")
