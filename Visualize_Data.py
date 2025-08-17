import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from io import BytesIO

# Set page configuration
st.set_page_config(layout="wide")

# Title
st.title("Data Visualizer")

# Sidebar Theme Selection
st.sidebar.title("Options")

# Upload CSV/Excel
uploaded_file = st.sidebar.file_uploader("Upload your file", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    # Check file type and read accordingly
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.title("Interactive Data Visualization App")

    # Sidebar Filters
    st.sidebar.header("Filter and Grouping Options")

    # Date filtering
    date_columns = df.select_dtypes(include=['datetime64[ns]', 'datetime64[ns, UTC]']).columns

    if not date_columns.empty:
        # Pick the first datetime column
        date_col = date_columns[0]

        # Convert to datetime (if not already)
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])

        if not df.empty:
            min_date = df[date_col].min().date()
            max_date = df[date_col].max().date()

            date_range = st.sidebar.slider(
                f"Select Date Range ({date_col})",
                min_value=min_date,
                max_value=max_date,
                value=(min_date, max_date)
            )

            df = df[
                (df[date_col].dt.date >= date_range[0]) &
                (df[date_col].dt.date <= date_range[1])
            ]

    # Grouping
    columns = df.columns.tolist()
    group_col = st.sidebar.selectbox("Group By", options=["None"] + columns)
    if group_col != "None":
        df = df.groupby(group_col).sum(numeric_only=True).reset_index()

    # Sorting
    sort_col = st.sidebar.selectbox("Sort By", options=["None"] + df.columns.tolist())
    if sort_col != "None":
        df = df.sort_values(by=sort_col)

    # Checkbox for dataset preview
    show_data = st.checkbox("Show Dataset Preview")
    if show_data:
        st.write("### Dataset Preview")
        st.dataframe(df)

    chart_type = st.sidebar.selectbox(
        "Select Chart Type",
        ["Bar Chart", "Pie Chart", "Scatter Plot", "Box Plot", "Histogram", "Heatmap", "Pair Plot"]
    )

    if chart_type == "Bar Chart":
        st.subheader("Bar Chart")
        column = st.sidebar.selectbox("Select Column", df.columns)
        if column:
            bar_data = df[column].value_counts()
            st.bar_chart(bar_data)

    elif chart_type == "Pie Chart":
        st.subheader("Pie Chart")
        column = st.sidebar.selectbox("Select Column for Pie", df.select_dtypes(include='object').columns)
        if column:
            pie_data = df[column].value_counts()
            plt.figure(figsize=(6, 6))
            plt.pie(pie_data, labels=pie_data.index, autopct='%1.1f%%', startangle=140)
            st.pyplot(plt)

    elif chart_type == "Scatter Plot":
        st.subheader("Scatter Plot")
        x_axis = st.sidebar.selectbox("X Axis", df.select_dtypes(include='number').columns)
        y_axis = st.sidebar.selectbox("Y Axis", df.select_dtypes(include='number').columns)
        if x_axis and y_axis:
            fig, ax = plt.subplots()
            ax.scatter(df[x_axis], df[y_axis], alpha=0.6)
            ax.set_xlabel(x_axis)
            ax.set_ylabel(y_axis)
            ax.set_title(f"{x_axis} vs {y_axis}")
            st.pyplot(fig)

    elif chart_type == "Box Plot":
        st.subheader("Box Plot")
        column = st.sidebar.selectbox("Select Numeric Column", df.select_dtypes(include='number').columns)
        category = st.sidebar.selectbox("Group By (Optional)", df.select_dtypes(include='object').columns)
        if column:
            plt.figure(figsize=(8, 4))
            if category:
                sns.boxplot(x=df[category], y=df[column])
            else:
                sns.boxplot(y=df[column])
            st.pyplot(plt)

    elif chart_type == "Histogram":
        st.subheader("Histogram")
        column = st.sidebar.selectbox("Select Numeric Column", df.select_dtypes(include='number').columns)
        if column:
            plt.figure(figsize=(8, 4))
            plt.hist(df[column].dropna(), bins=20, color='skyblue', edgecolor='black')
            plt.title(f"Histogram of {column}")
            st.pyplot(plt)

    elif chart_type == "Heatmap":
        st.subheader("Heatmap - Correlation")
        corr = df.select_dtypes(include='number').corr()
        plt.figure(figsize=(8, 6))
        sns.heatmap(corr, annot=True, cmap='coolwarm')
        st.pyplot(plt)

    elif chart_type == "Pair Plot":
        st.subheader("Pair Plot")
        numeric_columns = df.select_dtypes(include='number').columns
        if len(numeric_columns) > 1:
            sns.pairplot(df[numeric_columns])
            st.pyplot(plt)

    # DOWNLOAD
    st.subheader("Download Processed Data")

    def convert_df_to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()

    excel_data = convert_df_to_excel(df)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "Download as Excel",
            data=excel_data,
            file_name="Processed_Data.xlsx",
            mime="application/vnd.ms-excel"
        )
    with col2:
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Download as CSV",
            data=csv_data,
            file_name="Processed_Data.csv",
            mime='text/csv'
        )

else:
    st.info("Upload a CSV or Excel file to start exploring!")
