import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

st.set_page_config(layout="wide", page_title="Dashboard Analisis Credit Score")

# Judul aplikasi
st.title("Dashboard Analisis Credit Score dan Status Pembayaran")

# Fungsi untuk mengidentifikasi tipe data kolom
def identify_column_types(df):
    column_types = {}
    
    for column in df.columns:
        # Mengambil nilai non-null dari kolom
        non_null_values = df[column].dropna().astype(str)
        
        if non_null_values.empty:
            column_types[column] = 'unknown'
            continue
        
        # Cek apakah berisi angka
        if pd.to_numeric(non_null_values, errors='coerce').notna().all():
            column_types[column] = 'numeric'
            continue
        
        # Cek untuk format array
        if non_null_values.str.startswith('[').any() and non_null_values.str.endswith(']').any():
            column_types[column] = 'array'
            continue
            
        # Cek jumlah nilai unik
        unique_values = non_null_values.nunique()
        if unique_values <= 20:
            column_types[column] = 'categorical'
        else:
            column_types[column] = 'text'
    
    return column_types

# Fungsi untuk mendapatkan statistik kolom kategorikal
def get_categorical_stats(df, column):
    value_counts = df[column].value_counts(dropna=False)
    value_counts.index = value_counts.index.map(lambda x: 'Missing/Null' if pd.isna(x) else str(x))
    
    stats = []
    for value, count in value_counts.items():
        stats.append({
            'value': value,
            'count': count,
            'percentage': round((count / len(df)) * 100, 2)
        })
    
    return stats

# Fungsi untuk mendapatkan statistik kolom numerik
def get_numeric_stats(df, column):
    values = pd.to_numeric(df[column], errors='coerce')
    stats = {
        'count': int(values.count()),
        'min': float(values.min()),
        'max': float(values.max()),
        'mean': float(values.mean()),
        'median': float(values.median()),
        'missing': int(len(df) - values.count())
    }
    
    # Membuat bins untuk distribusi
    bins = 5
    bin_values, bin_edges = np.histogram(values.dropna(), bins=bins)
    
    stats['bins'] = [{
        'min': float(bin_edges[i]),
        'max': float(bin_edges[i+1]),
        'count': int(bin_values[i])
    } for i in range(bins)]
    
    return stats

# Fungsi untuk mendapatkan perbandingan dengan status pembayaran
def get_comparison_with_repayment(df, column, column_type, repayment_column='farmer_repayment_status'):
    # Mendapatkan nilai unik repayment status
    repayment_values = df[repayment_column].dropna().unique().tolist()
    
    if column_type == 'categorical':
        # Membuat tabel crosstab
        cross_tab = pd.crosstab(df[column], df[repayment_column], margins=False)
        cross_tab_percent = pd.crosstab(df[column], df[repayment_column], normalize='index') * 100
        
        return {
            'absolute': cross_tab,
            'percentage': cross_tab_percent
        }
    
    elif column_type == 'numeric':
        # Membuat statistik per status pembayaran
        stats = {}
        
        for status in repayment_values:
            values = pd.to_numeric(df[df[repayment_column] == status][column], errors='coerce')
            
            if values.count() == 0:
                continue
                
            stats[status] = {
                'count': int(values.count()),
                'min': float(values.min()),
                'max': float(values.max()),
                'mean': float(values.mean()),
                'median': float(values.median())
            }
        
        return stats
    
    return None

# Upload file CSV
uploaded_file = st.sidebar.file_uploader("Upload file CSV", type=["csv"])

# Load data
@st.cache_data
def load_data(file):
    df = pd.read_csv(file)
    return df

# Sidebar untuk konfigurasi
st.sidebar.title("Konfigurasi")

# Memuat data
if uploaded_file is not None:
    df = load_data(uploaded_file)
else:
    try:
        # Default file
        df = pd.read_csv("credit_score_evaluation.csv")
        st.sidebar.success("Menggunakan file default: credit_score_evaluation.csv")
    except:
        st.sidebar.error("File default tidak ditemukan. Silakan upload file CSV.")
        st.stop()

# Identifikasi tipe data kolom
column_types = identify_column_types(df)

# Informasi dataset
with st.expander("Informasi Dataset", expanded=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Jumlah Baris", len(df))
    with col2:
        st.metric("Jumlah Kolom", len(df.columns))
    with col3:
        if 'farmer_repayment_status' in df.columns:
            repayment_counts = df['farmer_repayment_status'].value_counts()
            repayment_info = ", ".join([f"{status}: {count}" for status, count in repayment_counts.items()])
            st.metric("Status Pembayaran", repayment_info)
    
    # Tampilkan detail kolom
    st.subheader("Detail Kolom")
    column_info = {
        'Kolom': list(column_types.keys()),
        'Tipe': list(column_types.values()),
        'Missing Values': [df[col].isna().sum() for col in column_types.keys()],
        'Missing Percentage': [round(df[col].isna().sum() / len(df) * 100, 2) for col in column_types.keys()]
    }
    st.dataframe(pd.DataFrame(column_info))

# Sidebar untuk pemilihan kolom dan tipe
column_type_filter = st.sidebar.radio("Tampilkan tipe kolom:", ["Semua", "Kategorikal", "Numerik"])

# Filter kolom berdasarkan tipe yang dipilih
filtered_columns = []
if column_type_filter == "Kategorikal":
    filtered_columns = [col for col, type_ in column_types.items() if type_ == 'categorical' or type_ == 'array']
elif column_type_filter == "Numerik":
    filtered_columns = [col for col, type_ in column_types.items() if type_ == 'numeric']
else:
    filtered_columns = list(df.columns)

# Pencarian kolom
search_term = st.sidebar.text_input("Cari kolom:")
if search_term:
    filtered_columns = [col for col in filtered_columns if search_term.lower() in col.lower()]

# Pilih kolom untuk analisis
selected_column = st.sidebar.selectbox("Pilih kolom untuk analisis:", filtered_columns)

# Tampilkan distribusi kolom yang dipilih
if selected_column:
    st.header(f"Analisis Kolom: {selected_column}")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.subheader("Informasi Kolom")
        st.write(f"Tipe: {column_types.get(selected_column, 'unknown')}")
        
        missing_count = df[selected_column].isna().sum()
        st.write(f"Missing values: {missing_count} ({round(missing_count/len(df)*100, 2)}%)")
        
        if column_types.get(selected_column) == 'categorical' or column_types.get(selected_column) == 'array':
            st.write(f"Nilai unik: {df[selected_column].dropna().nunique()}")
        elif column_types.get(selected_column) == 'numeric':
            numeric_values = pd.to_numeric(df[selected_column], errors='coerce')
            st.write(f"Minimum: {numeric_values.min():.2f}")
            st.write(f"Maximum: {numeric_values.max():.2f}")
            st.write(f"Mean: {numeric_values.mean():.2f}")
            st.write(f"Median: {numeric_values.median():.2f}")
    
    with col1:
        if column_types.get(selected_column) == 'categorical' or column_types.get(selected_column) == 'array':
            # Visualisasi untuk kolom kategorikal
            categorical_stats = get_categorical_stats(df, selected_column)
            
            # Ambil top 10 untuk grafik
            chart_data = [stat for stat in categorical_stats if stat['value'] != 'Missing/Null'][:10]
            
            fig = px.bar(
                chart_data, 
                x='value', 
                y='count',
                labels={'value': selected_column, 'count': 'Jumlah'},
                title=f"Distribusi {selected_column}"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        elif column_types.get(selected_column) == 'numeric':
            # Visualisasi untuk kolom numerik
            numeric_stats = get_numeric_stats(df, selected_column)
            
            # Histogram
            fig = px.histogram(
                df, 
                x=selected_column,
                nbins=20,
                title=f"Distribusi {selected_column}"
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Perbandingan dengan status pembayaran (jika kolom repayment_status ada)
    if 'farmer_repayment_status' in df.columns and selected_column != 'farmer_repayment_status':
        st.header(f"Perbandingan {selected_column} dengan Status Pembayaran")
        
        column_type = column_types.get(selected_column)
        
        if column_type == 'categorical' or column_type == 'array':
            comparison = get_comparison_with_repayment(df, selected_column, 'categorical')
            
            if comparison:
                # Tab untuk memilih tampilan absolut atau persentase
                tab1, tab2 = st.tabs(["Persentase", "Nilai Absolut"])
                
                with tab1:
                    # Stacked bar chart untuk persentase
                    fig = px.bar(
                        comparison['percentage'].reset_index(), 
                        x=selected_column,
                        y=comparison['percentage'].columns,
                        title=f"Persentase Status Pembayaran per {selected_column}",
                        barmode='stack',
                        color_discrete_map={
                            'Outstanding': '#FF8042',
                            'Lunas': '#00C49F',
                            'Drop': '#8884d8'
                        }
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Tampilkan data tabel
                    st.dataframe(comparison['percentage'].round(2))
                
                with tab2:
                    # Grouped bar chart untuk nilai absolut
                    fig = px.bar(
                        comparison['absolute'].reset_index(), 
                        x=selected_column,
                        y=comparison['absolute'].columns,
                        title=f"Jumlah Status Pembayaran per {selected_column}",
                        barmode='group',
                        color_discrete_map={
                            'Outstanding': '#FF8042',
                            'Lunas': '#00C49F',
                            'Drop': '#8884d8'
                        }
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Tampilkan data tabel
                    st.dataframe(comparison['absolute'])
                
        elif column_type == 'numeric':
            comparison = get_comparison_with_repayment(df, selected_column, 'numeric')
            
            if comparison:
                # Membuat dataframe dari statistik
                comparison_df = pd.DataFrame({
                    status: {
                        'count': stats['count'],
                        'min': stats['min'],
                        'max': stats['max'],
                        'mean': stats['mean'],
                        'median': stats['median']
                    }
                    for status, stats in comparison.items()
                }).T
                
                # Tampilkan dataframe
                st.dataframe(comparison_df)
                
                # Visualisasi mean dan median per status
                fig = go.Figure()
                
                for status in comparison.keys():
                    color = '#FF8042' if status == 'Outstanding' else '#00C49F' if status == 'Lunas' else '#8884d8'
                    
                    fig.add_trace(go.Bar(
                        x=['Mean', 'Median'],
                        y=[comparison[status]['mean'], comparison[status]['median']],
                        name=status,
                        marker_color=color
                    ))
                
                fig.update_layout(
                    title=f"Mean dan Median {selected_column} per Status Pembayaran",
                    xaxis_title="Metrik",
                    yaxis_title="Nilai",
                    barmode='group'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Box plot per status pembayaran
                fig = px.box(
                    df, 
                    x='farmer_repayment_status', 
                    y=selected_column,
                    title=f"Box Plot {selected_column} per Status Pembayaran",
                    color='farmer_repayment_status',
                    color_discrete_map={
                        'Outstanding': '#FF8042',
                        'Lunas': '#00C49F',
                        'Drop': '#8884d8'
                    }
                )
                
                st.plotly_chart(fig, use_container_width=True)

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("Dashboard Analisis Credit Score © 2025")