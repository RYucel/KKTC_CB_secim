import streamlit as st
import pandas as pd
import plotly.express as px

# --- Sayfa Konfigürasyonu ---
st.set_page_config(
    page_title="KKTC Seçim Sonuçları Paneli",
    page_icon="🗳️",
    layout="wide"
)

# --- Veri Yükleme ve Önbelleğe Alma ---
@st.cache_data
def load_data(file_path):
    """CSV dosyasından seçim verilerini yükler, temizler ve standartlaştırır."""
    try:
        df = pd.read_csv(file_path, on_bad_lines='warn')
        df.rename(columns=lambda c: c.strip('\ufeff'), inplace=True)
        rename_map = {'Sandık No': 'Sandik_No', 'Sandik No': 'Sandik_No', 'Seçim Çevresi': 'Secim_Cevresi'}
        df.rename(columns=rename_map, inplace=True)
        df.columns = [col.strip().replace(' ', '_') for col in df.columns]

        for col in ['Region', 'Secim_Cevresi']:
            if col in df.columns:
                df[col] = df[col].astype(str)

        df.dropna(subset=['Region', 'Secim_Cevresi'], inplace=True)
        
        numeric_cols = df.columns.drop(['Region', 'Secim_Cevresi', 'Sandik_No'], errors='ignore')
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df.fillna(0, inplace=True)
        return df
    except FileNotFoundError:
        st.error(f"Hata: {file_path} dosyası bulunamadı.")
        return None
    except Exception as e:
        st.error(f"{file_path} yüklenirken bir hata oluştu: {e}")
        return None

# Verileri Yükle
df_2020 = load_data('TumSandiklar2020.csv')
df_2025 = load_data('TumSandiklar2025.csv')

def process_election_data(df, year):
    if df is None or df.empty: return None, []
    try:
        if year == 2020: start_col, end_col = 'Ersin_Tatar', 'Serdar_Denktaş'
        else: start_col, end_col = 'Osman_Zorba_(KSP)', 'Ersin_Tatar_(BAĞ_6)'
        
        if start_col not in df.columns or end_col not in df.columns:
            st.error(f"{year} yılı verilerinde aday sütunları bulunamadı. Lütfen CSV sütun isimlerini kontrol edin.")
            return None, []
            
        start_idx, end_idx = df.columns.get_loc(start_col), df.columns.get_loc(end_col)
        candidate_columns = df.columns[start_idx : end_idx + 1]
        candidate_votes = df[candidate_columns].sum().sort_values(ascending=False)
        return candidate_votes, candidate_columns
    except KeyError as e:
        st.error(f"{year} yılı verilerinde sütun hatası: {e} sütunu bulunamadı.")
        return None, []

# --- Kenar Çubuğu Filtreleri ---
st.sidebar.header("Filtreler")
selected_year = st.sidebar.radio("Yıl Seçimi", ('2020', '2025', 'Karşılaştırma'))

if df_2020 is not None and df_2025 is not None:
    if selected_year == 'Karşılaştırma':
        regions = sorted(list(set(df_2020['Region'].unique()) | set(df_2025['Region'].unique())))
    else:
        active_df = df_2020 if selected_year == '2020' else df_2025
        regions = sorted(active_df['Region'].unique().tolist())
    
    selected_region = st.sidebar.selectbox("Bölge Seçimi", ["Tümü"] + regions)

    temp_df_2020 = df_2020[df_2020['Region'] == selected_region] if selected_region != "Tümü" else df_2020
    temp_df_2025 = df_2025[df_2025['Region'] == selected_region] if selected_region != "Tümü" else df_2025

    if selected_year == 'Karşılaştırma':
        districts = sorted(list(set(temp_df_2020['Secim_Cevresi'].unique()) | set(temp_df_2025['Secim_Cevresi'].unique())))
    else:
        active_temp_df = temp_df_2020 if selected_year == '2020' else temp_df_2025
        districts = sorted(active_temp_df['Secim_Cevresi'].unique().tolist())
    selected_district = st.sidebar.selectbox("Seçim Çevresi (İlçe)", ["Tümü"] + districts)

    if selected_district != "Tümü":
        temp_df_2020 = temp_df_2020[temp_df_2020['Secim_Cevresi'] == selected_district]
        temp_df_2025 = temp_df_2025[temp_df_2025['Secim_Cevresi'] == selected_district]

    if selected_year == 'Karşılaştırma':
        ballot_boxes = sorted([int(x) for x in set(temp_df_2020['Sandik_No'].unique()) | set(temp_df_2025['Sandik_No'].unique())])
    else:
        active_temp_df = temp_df_2020 if selected_year == '2020' else temp_df_2025
        ballot_boxes = sorted([int(x) for x in active_temp_df['Sandik_No'].unique()])
    selected_ballot_box = st.sidebar.selectbox("Sandık No", ["Tümü"] + ballot_boxes)

    def filter_data(df, region, district, ballot_box):
        if df is None: return pd.DataFrame()
        filtered_df = df.copy()
        if region != "Tümü": filtered_df = filtered_df[filtered_df['Region'] == region]
        if district != "Tümü": filtered_df = filtered_df[filtered_df['Secim_Cevresi'] == district]
        if ballot_box != "Tümü": filtered_df = filtered_df[filtered_df['Sandik_No'] == ballot_box]
        return filtered_df

    filtered_df_2020 = filter_data(df_2020, selected_region, selected_district, selected_ballot_box)
    filtered_df_2025 = filter_data(df_2025, selected_region, selected_district, selected_ballot_box)

    candidate_votes_2020_filtered, _ = process_election_data(filtered_df_2020, 2020)
    candidate_votes_2025_filtered, _ = process_election_data(filtered_df_2025, 2025)

# --- Ana Panel ---
st.title("🇹🇷 KKTC Cumhurbaşkanlığı Seçim Sonuçları Paneli")

def get_title(year_str, region, district, ballot_box):
    title_parts = [year_str]
    if region != "Tümü": title_parts.append(region)
    if district != "Tümü": title_parts.append(district)
    if ballot_box != "Tümü": title_parts.append(f"Sandık No: {ballot_box}")
    return " - ".join(title_parts)

def display_year_results(df, candidate_votes, year_str, header_title):
    st.header(header_title)
    
    if df.empty or candidate_votes is None or candidate_votes.empty:
        st.warning(f"{year_str} yılı için seçilen kriterlerde veri bulunamadı.")
        return

    total_voters = df['Kayıtlı_Seçmen_Sayısı'].sum()
    total_votes_cast = df['Oy_Kullanan_Seçmen_Sayısı'].sum()
    total_valid_votes = candidate_votes.sum()
    turnout = (total_votes_cast / total_voters) * 100 if total_voters > 0 else 0

    col1, col2 = st.columns(2)
    col1.metric("Kullanılan Toplam Oy", f"{int(total_votes_cast):,}")
    col2.metric("Seçime Katılım Oranı", f"{turnout:.2f}%")
    st.markdown("---")

    st.subheader("İlk Üç Aday")
    cols = st.columns(3)
    
    # --- DÜZELTME: Her adayın bilgisi kendi sütununa yerleştirildi ---
    for i in range(3):
        if len(candidate_votes) > i:
            label = ["Birinci 🥇", "İkinci 🥈", "Üçüncü 🥉"][i]
            candidate_name = candidate_votes.index[i].replace('_', ' ')
            vote_count = candidate_votes.iloc[i]
            vote_percentage = (vote_count / total_valid_votes) * 100 if total_valid_votes > 0 else 0
            
            # 'with' bloğu kullanarak tüm metrikleri doğru sütuna yerleştir
            with cols[i]:
                st.metric(
                    label=label,
                    value=candidate_name,
                )
                st.metric(
                    label="Oy Sayısı",
                    value=f"{int(vote_count):,}",
                )
                st.metric(
                    label="Oy Oranı",
                    value=f"{vote_percentage:.2f}%",
                )

    st.markdown("---")

    # Görselleştirmeler
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Adayların Oy Sayıları")
        bar_df = candidate_votes.reset_index(); bar_df.columns = ['Aday', 'Oy Sayısı']
        fig_bar = px.bar(bar_df, x='Aday', y='Oy Sayısı', labels={'Aday': 'Adaylar', 'Oy Sayısı': 'Toplam Oy'})
        st.plotly_chart(fig_bar, use_container_width=True)
    with col2:
        st.subheader("Oy Dağılımı")
        if total_valid_votes > 0:
            pie_df = candidate_votes.reset_index(); pie_df.columns = ['Aday', 'Oy_Sayısı']
            fig_pie = px.pie(
                pie_df, values='Oy_Sayısı', names='Aday',
                title=f"Toplam Geçerli Oy: {int(total_valid_votes):,}", hole=0.3
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label', pull=[0.1 if i==0 else 0 for i in range(len(pie_df))])
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.warning("Bu seçimde geçerli oy bulunmamaktadır.")

# --- Ana uygulama mantığı ---
if 'selected_region' in locals():
    if selected_year == '2020':
        title = get_title("2020 Sonuçları", selected_region, selected_district, selected_ballot_box)
        display_year_results(filtered_df_2020, candidate_votes_2020_filtered, "2020", title)
    elif selected_year == '2025':
        title = get_title("2025 Sonuçları", selected_region, selected_district, selected_ballot_box)
        display_year_results(filtered_df_2025, candidate_votes_2025_filtered, "2025", title)
    elif selected_year == 'Karşılaştırma':
        title = get_title("Karşılaştırmalı Sonuçlar", selected_region, selected_district, selected_ballot_box)
        st.header(title)
        
        col1, col2 = st.columns(2)
        with col1:
            display_year_results(filtered_df_2020, candidate_votes_2020_filtered, "2020", "2020 Yılı")
        with col2:
            display_year_results(filtered_df_2025, candidate_votes_2025_filtered, "2025", "2025 Yılı")
else:
    st.warning("Veri yüklenemedi. Lütfen CSV dosyalarını kontrol edip sayfayı yenileyin.")