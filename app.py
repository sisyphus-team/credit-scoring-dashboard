import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Konfigurasi halaman
st.set_page_config(
    page_title="Dashboard Credit Score Dataset",
    page_icon="📊",
    layout="wide"
)

# Custom color palette
COLOR_GREEN = '#2E8B57'  # Sea Green
COLOR_ORANGE = '#FFA500'  # Orange
COLOR_LIGHT_GREEN = '#8FBC8F'  # Dark Sea Green
COLOR_LIGHT_ORANGE = '#FFD700'  # Gold
COLOR_PALETTE = [COLOR_GREEN, COLOR_ORANGE, COLOR_LIGHT_GREEN, COLOR_LIGHT_ORANGE]

# Custom CSS untuk styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E8B57;
        text-align: center;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #1E5631;
    }
    .metric-card {
        background-color: #f4f4f4;
        border-radius: 5px;
        padding: 10px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2E8B57;
    }
    .sidebar .sidebar-content {
        background-color: #f9f9f9;
    }
</style>
""", unsafe_allow_html=True)

# Judul Aplikasi
st.markdown('<H1 class="main-header">Eratani Credit Score Dashboard</H1>', unsafe_allow_html=True)

# Fungsi untuk membaca data
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('credit_score_dataset_new.csv')
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# Load data
df = load_data()

if df is not None:
    # Pisahkan kolom numerik dan kategorikal
    numeric_cols = ['farmer_age', 'farmer_dependents', 'farmer_field_tiles', 
                   'farmer_field_owned_area', 'farmer_field_proposed_area', 
                   'proposed_field_size_ratio', 'farmer_field_ph', 
                   'farmer_credit_score', 'farmer_retention', 'farmer_financial_monthly_income', 
                   'farmer_last_year_harvest', 'farmer_last_year_expenses', 'farmer_total_loan']
    
    categorical_cols = [col for col in df.columns if col not in numeric_cols]
    
    # Tampilkan KPI utama di bagian atas
    st.markdown('<p class="sub-header">Metrik Utama</p>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total Data", f"{len(df):,}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        avg_credit_score = int(df['farmer_credit_score'].mean())
        st.metric("Rata-rata Credit Score", f"{avg_credit_score:,}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        if 'farmer_repayment_status' in df.columns:
            good_repayment = df['farmer_repayment_status'].value_counts().get('Lunas', 0)
            good_percent = round((good_repayment / len(df)) * 100, 2)
            st.metric("Repayment Status Lunas", f"{good_percent}%")
        else:
            st.metric("Repayment Status Baik", "N/A")
        st.markdown('</div>', unsafe_allow_html=True)

    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        if 'farmer_repayment_status' in df.columns:
            good_repayment = df['farmer_repayment_status'].value_counts().get('Outstanding', 0)
            good_percent = round((good_repayment / len(df)) * 100, 2)
            st.metric("Repayment Status Outstanding", f"{good_percent}%")
        else:
            st.metric("Repayment Status Baik", "N/A")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # with col4:
    #     st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    #     median_age = int(df['farmer_age'].median())
    #     st.metric("Median Umur Petani", f"{median_age} tahun")
    #     st.markdown('</div>', unsafe_allow_html=True)
    
    # Sidebar untuk memilih jenis data dan kolom
    st.sidebar.title("Filter dan Pilihan")
    
    data_type = st.sidebar.radio("Pilih Jenis Data", ["Numerik", "Kategorikal"])
    
    if data_type == "Numerik":
        selected_column = st.sidebar.selectbox("Pilih Kolom Numerik", numeric_cols)
    else:
        selected_column = st.sidebar.selectbox("Pilih Kolom Kategorikal", categorical_cols)
    
    # Filter data berdasarkan range (untuk numerik) atau nilai (untuk kategorikal)
    if data_type == "Numerik":
        min_val = float(df[selected_column].min())
        max_val = float(df[selected_column].max())
        
        # Gunakan input box untuk filter rentang numerik
        st.sidebar.subheader(f"Filter rentang {selected_column}")
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            input_min = st.number_input(f"Min {selected_column}", 
                                       min_value=min_val, 
                                       max_value=max_val,
                                       value=min_val,
                                       step=(max_val-min_val)/100)
        with col2:
            input_max = st.number_input(f"Max {selected_column}", 
                                       min_value=min_val, 
                                       max_value=max_val,
                                       value=max_val,
                                       step=(max_val-min_val)/100)
            
        # Pastikan nilai min tidak lebih besar dari nilai max
        if input_min > input_max:
            st.sidebar.error("Nilai minimum tidak boleh lebih besar dari nilai maksimum!")
            input_min = input_max
            
        filtered_df = df[(df[selected_column] >= input_min) & 
                         (df[selected_column] <= input_max)]
    else:
        unique_values = df[selected_column].dropna().unique()
        selected_values = st.sidebar.multiselect(f"Filter nilai {selected_column}", 
                                              unique_values, default=unique_values)
        if selected_values:
            filtered_df = df[df[selected_column].isin(selected_values)]
        else:
            filtered_df = df
    
    # Tampilkan jumlah data setelah filter
    st.sidebar.info(f"Jumlah data setelah filter: {len(filtered_df):,} dari {len(df):,}")
    
    # Membuat dua tabs
    tab1, tab2, tab3 = st.tabs(["Distribusi Kolom", "Perbandingan dengan Repayment Status", "Data Mentah"])
    
    # Tab 1: Distribusi Kolom
    with tab1:
        st.markdown(f'<p class="sub-header">Distribusi {selected_column}</p>', unsafe_allow_html=True)
        
        if data_type == "Numerik":
            # Menampilkan statistik untuk kolom numerik
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Statistik Deskriptif")
                stats = filtered_df[selected_column].describe().reset_index()
                stats.columns = ['Statistik', 'Nilai']
                st.dataframe(stats, use_container_width=True)
                
                # Distribusi sebagai box plot
                fig_box = px.box(filtered_df, y=selected_column, 
                                color_discrete_sequence=[COLOR_GREEN])
                st.plotly_chart(fig_box, use_container_width=True)
            
            with col2:
                st.subheader("Histogram")
                fig_hist = px.histogram(filtered_df, x=selected_column, 
                                     color_discrete_sequence=[COLOR_GREEN],
                                     nbins=30,
                                     marginal="rug")
                fig_hist.update_layout(bargap=0.1)
                st.plotly_chart(fig_hist, use_container_width=True)
                
                # Tambahkan KDE plot
                fig_kde = px.density_contour(filtered_df, x=selected_column,
                                          color_discrete_sequence=[COLOR_ORANGE])
                fig_kde.update_traces(contours_coloring="fill", contours_showlabels=True)
                st.plotly_chart(fig_kde, use_container_width=True)
        
        else:
            # Menampilkan distribusi untuk kolom kategorikal
            st.subheader("Distribusi Nilai")
            
            # Menghitung nilai absolut dan persentase
            value_counts = filtered_df[selected_column].value_counts().reset_index()
            value_counts.columns = ['Nilai', 'Jumlah']
            
            # Tambahkan persentase
            total = value_counts['Jumlah'].sum()
            value_counts['Persentase'] = (value_counts['Jumlah'] / total * 100).round(2)
            value_counts['Persentase Label'] = value_counts['Persentase'].apply(lambda x: f"{x}%")
            
            # Tampilkan tabel
            st.dataframe(value_counts[['Nilai', 'Jumlah', 'Persentase Label']], 
                       use_container_width=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Buat bar chart dengan warna hijau-oranye
                fig_bar = px.bar(value_counts, x='Nilai', y='Jumlah', 
                              text='Persentase Label',
                              color='Jumlah', 
                              color_continuous_scale=[COLOR_LIGHT_GREEN, COLOR_GREEN])
                fig_bar.update_traces(texttemplate='%{text}', textposition='outside')
                fig_bar.update_layout(title="Distribusi Nilai (Absolute)")
                st.plotly_chart(fig_bar, use_container_width=True)
            
            with col2:
                # Tampilkan pie chart
                fig_pie = px.pie(value_counts, names='Nilai', values='Jumlah', 
                              hole=0.4,
                              color_discrete_sequence=COLOR_PALETTE)
                fig_pie.update_traces(textinfo='percent+label')
                fig_pie.update_layout(title="Distribusi Nilai (Persentase)")
                st.plotly_chart(fig_pie, use_container_width=True)
    
    # Tab 2: Perbandingan dengan Repayment Status
    with tab2:
        st.markdown(f'<p class="sub-header">{selected_column} vs Repayment Status</p>', unsafe_allow_html=True)
        
        # Pastikan kolom repayment status ada dalam dataset
        if 'farmer_repayment_status' in filtered_df.columns:
            # Dapatkan nilai unik repayment status
            repayment_values = filtered_df['farmer_repayment_status'].dropna().unique()
            
            if data_type == "Numerik":
                col1, col2 = st.columns(2)
                
                with col1:
                    # Boxplot untuk numerik berdasarkan repayment status
                    fig_box = px.box(filtered_df, x='farmer_repayment_status', y=selected_column, 
                                 color='farmer_repayment_status', 
                                 color_discrete_sequence=[COLOR_GREEN, COLOR_ORANGE])
                    fig_box.update_layout(title="Box Plot berdasarkan Repayment Status")
                    st.plotly_chart(fig_box, use_container_width=True)
                
                with col2:
                    # Violin plot
                    fig_violin = px.violin(filtered_df, x='farmer_repayment_status', y=selected_column, 
                                      color='farmer_repayment_status', box=True, 
                                      color_discrete_sequence=[COLOR_GREEN, COLOR_ORANGE])
                    fig_violin.update_layout(title="Violin Plot berdasarkan Repayment Status")
                    st.plotly_chart(fig_violin, use_container_width=True)
                
                # Histogram dengan overlay untuk setiap repayment status
                fig_hist = px.histogram(filtered_df, x=selected_column, 
                                     color='farmer_repayment_status',
                                     nbins=30,
                                     opacity=0.7,
                                     color_discrete_sequence=[COLOR_GREEN, COLOR_ORANGE])
                fig_hist.update_layout(title="Histogram berdasarkan Repayment Status")
                st.plotly_chart(fig_hist, use_container_width=True)
                
                # Statistik deskriptif per repayment status
                st.subheader("Statistik berdasarkan Repayment Status")
                desc_stats = filtered_df.groupby('farmer_repayment_status')[selected_column].describe().reset_index()
                st.dataframe(desc_stats, use_container_width=True)
                
            else:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Hitung distribusi kolom kategorikal untuk setiap nilai repayment status
                    cross_tab_pct = pd.crosstab(filtered_df[selected_column], filtered_df['farmer_repayment_status'], 
                                             normalize='index') * 100
                    cross_tab_pct = cross_tab_pct.reset_index()
                    
                    # Tampilkan sebagai tabel
                    st.subheader("Distribusi (%) berdasarkan Repayment Status")
                    st.dataframe(cross_tab_pct.round(2), use_container_width=True)
                    
                    # Tampilkan sebagai stacked bar chart
                    fig_stacked = go.Figure()
                    
                    for i, status in enumerate(repayment_values):
                        color = COLOR_GREEN if i == 0 else COLOR_ORANGE
                        fig_stacked.add_trace(go.Bar(
                            x=cross_tab_pct[selected_column],
                            y=cross_tab_pct[status],
                            name=status,
                            marker_color=color
                        ))
                    
                    fig_stacked.update_layout(
                        barmode='stack',
                        xaxis={'categoryorder':'total descending'},
                        yaxis_title='Persentase (%)',
                        legend_title='Repayment Status',
                        title="Distribusi (%) berdasarkan Repayment Status"
                    )
                    
                    st.plotly_chart(fig_stacked, use_container_width=True)
                
                with col2:
                    # Hitung jumlah absolut
                    cross_tab_abs = pd.crosstab(filtered_df[selected_column], filtered_df['farmer_repayment_status'])
                    cross_tab_abs = cross_tab_abs.reset_index()
                    
                    # Tampilkan sebagai tabel
                    st.subheader("Jumlah Absolut berdasarkan Repayment Status")
                    st.dataframe(cross_tab_abs, use_container_width=True)
                    
                    # Tampilkan sebagai grouped bar chart
                    fig_grouped = go.Figure()
                    
                    for i, status in enumerate(repayment_values):
                        color = COLOR_GREEN if i == 0 else COLOR_ORANGE
                        fig_grouped.add_trace(go.Bar(
                            x=cross_tab_abs[selected_column],
                            y=cross_tab_abs[status],
                            name=status,
                            marker_color=color
                        ))
                    
                    fig_grouped.update_layout(
                        barmode='group',
                        xaxis={'categoryorder':'total descending'},
                        yaxis_title='Jumlah',
                        legend_title='Repayment Status',
                        title="Jumlah Absolut berdasarkan Repayment Status"
                    )
                    
                    st.plotly_chart(fig_grouped, use_container_width=True)
                
                # Heatmap untuk melihat korelasi
                # Modifikasi data untuk heatmap
                heat_data = pd.crosstab(filtered_df[selected_column], filtered_df['farmer_repayment_status'], normalize='all') * 100
                
                # Buat heatmap
                fig_heat = px.imshow(heat_data,
                                  labels=dict(x="Repayment Status", y=selected_column, color="Persentase (%)"),
                                  x=heat_data.columns,
                                  y=heat_data.index,
                                  color_continuous_scale=['white', COLOR_LIGHT_GREEN, COLOR_GREEN])
                
                fig_heat.update_layout(
                    title="Heatmap Distribusi (%)",
                    xaxis_title="Repayment Status",
                    yaxis_title=selected_column
                )
                
                # Tambahkan nilai sebagai anotasi
                fig_heat.update_traces(text=heat_data.values.round(1), texttemplate="%{text}%")
                
                st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.error("Kolom 'farmer_repayment_status' tidak ditemukan dalam dataset")
    
    # Tab 3: Data Mentah
    with tab3:
        st.markdown('<p class="sub-header">Data Mentah</p>', unsafe_allow_html=True)
        
        # Tampilkan filter kolom
        cols_to_show = st.multiselect(
            "Pilih kolom yang akan ditampilkan",
            options=filtered_df.columns.tolist(),
            default=[selected_column, 'farmer_repayment_status', 'farmer_credit_score']
        )
        
        if not cols_to_show:
            cols_to_show = filtered_df.columns.tolist()
        
        # Tampilkan data mentah dengan filter
        st.dataframe(filtered_df[cols_to_show], use_container_width=True)
        
        # Opsi download data
        csv = filtered_df[cols_to_show].to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download data sebagai CSV",
            data=csv,
            file_name=f"credit_score_data_{selected_column}.csv",
            mime="text/csv",
        )

    # Footer dengan informasi tambahan
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Tentang Dataset")
        st.markdown(f"""
        - Total data: {len(df):,} petani
        - Kolom numerik: {len(numeric_cols)}
        - Kolom kategorikal: {len(categorical_cols)}
        """)
    
    with col2:
        st.markdown("### Panduan Penggunaan")
        st.markdown("""
        1. Gunakan sidebar kiri untuk memilih jenis data dan kolom
        2. Tab 'Distribusi Kolom' menampilkan statistik dan visualisasi dari satu kolom
        3. Tab 'Perbandingan dengan Repayment Status' menampilkan hubungan antara kolom dengan status pembayaran
        4. Tab 'Data Mentah' memungkinkan Anda melihat dan mengunduh data mentah
        """)
    

else:
    st.error("Gagal memuat data. Silakan periksa file CSV Anda.")
