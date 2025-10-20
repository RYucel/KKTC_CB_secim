import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. SAYFA KONFİGÜRASYONU VE SEO ---
st.set_page_config(
    # Bu, tarayıcı sekmesinde ve Google arama sonuçlarında görünen başlık olacaktır.
    page_title="KKTC Seçim Sonuçları: 2020 & 2025 Analizi",
    page_icon="🗳️",
    layout="wide"
)

def inject_custom_html():
    """
    Bu fonksiyon, SEO ve sosyal medya paylaşım kartları için gerekli
    olan özel HTML meta etiketlerini sayfanın <head> bölümüne ekler.
    """
    st.markdown(
        """
        <head>
            <!-- SEO Meta Etiketleri -->
            <meta name="description" content="KKTC 2020 ve 2025 Cumhurbaşkanlığı seçim sonuçlarını karşılaştırın. Ersin Tatar, Tufan Erhürman ve diğer adayların oy değişimlerini ve cephe analizlerini interaktif olarak inceleyin.">
            <meta name="keywords" content="KKTC, seçim, seçim sonuçları, Ersin Tatar, Tufan Erhürman, Mustafa Akıncı, 2020 seçim, 2025 seçim, cumhurbaşkanlığı, siyaset, analiz">
            
            <!-- Open Graph Meta Etiketleri (Facebook, LinkedIn, vb. için paylaşım kartları) -->
            <meta property="og:title" content="KKTC Seçim Sonuçları: 2020 & 2025 Karşılaştırmalı Analiz">
            <meta property="og:description" content="İnteraktif panel ile KKTC seçim verilerini keşfedin. Aday ve blok bazında karşılaştırmalar yapın.">
            <meta property="og:image" content="https://imgur.com/a/Zm1q9N1>  <!-- ÖNEMLİ: Buraya kendi resminizin URL'sini koyun -->
            <meta property="og:url" content="https://kktc-cb-secim-2020vs2025.streamlit.app"> <!-- ÖNEMLİ: Streamlit Cloud URL'nizi buraya koyun -->
            <meta property="og:type" content="website">
        </head>
        """,
        unsafe_allow_html=True,
    )

# --- Veri Yükleme ve Diğer Fonksiyonlar ---
@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_csv(file_path, on_bad_lines='warn')
        df.rename(columns=lambda c: c.strip('\ufeff'), inplace=True)
        rename_map = {'Sandık No': 'Sandik_No', 'Sandik No': 'Sandik_No', 'Seçim Çevresi': 'Secim_Cevresi'}
        df.rename(columns=rename_map, inplace=True)
        df.columns = [col.strip().replace(' ', '_') for col in df.columns]

        for col in ['Region', 'Secim_Cevresi']:
            if col in df.columns: df[col] = df[col].astype(str)

        df.dropna(subset=['Region', 'Secim_Cevresi'], inplace=True)
        numeric_cols = df.columns.drop(['Region', 'Secim_Cevresi', 'Sandik_No'], errors='ignore')
        for col in numeric_cols: df[col] = pd.to_numeric(df[col], errors='coerce')
        df.fillna(0, inplace=True)
        return df
    except FileNotFoundError:
        st.error(f"Hata: {file_path} dosyası bulunamadı.")
        return None
    except Exception as e:
        st.error(f"{file_path} yüklenirken bir hata oluştu: {e}")
        return None

df_2020 = load_data('TumSandiklar2020.csv')
df_2025 = load_data('TumSandiklar2025.csv')

def process_election_data(df, year):
    if df is None or df.empty: return None, []
    try:
        if year == 2020: start_col, end_col = 'Ersin_Tatar', 'Serdar_Denktaş'
        else: start_col, end_col = 'Osman_Zorba_(KSP)', 'Ersin_Tatar_(BAĞ_6)'
        if start_col not in df.columns or end_col not in df.columns: return None, []
        start_idx, end_idx = df.columns.get_loc(start_col), df.columns.get_loc(end_col)
        candidate_columns = df.columns[start_idx : end_idx + 1]
        return df[candidate_columns].sum().sort_values(ascending=False), candidate_columns
    except KeyError: return None, []

# --- Kenar Çubuğu Filtreleri ---
st.sidebar.header("Filtreler")
selected_year = st.sidebar.radio("Görünüm Seçimi", ('2020', '2025', 'Genel Karşılaştırma', 'Tatar vs. Erhürman', 'Cephe Karşılaştırması'))

if df_2020 is not None and df_2025 is not None:
    if selected_year in ['Genel Karşılaştırma', 'Tatar vs. Erhürman', 'Cephe Karşılaştırması']:
        regions = sorted(list(set(df_2020['Region'].unique()) | set(df_2025['Region'].unique())))
    else:
        active_df = df_2020 if selected_year == '2020' else df_2025
        regions = sorted(active_df['Region'].unique().tolist())
    
    selected_region = st.sidebar.selectbox("Bölge Seçimi", ["Tümü"] + regions)

    temp_df_2020 = df_2020[df_2020['Region'] == selected_region] if selected_region != "Tümü" else df_2020
    temp_df_2025 = df_2025[df_2025['Region'] == selected_region] if selected_region != "Tümü" else df_2025

    if selected_year in ['Genel Karşılaştırma', 'Tatar vs. Erhürman', 'Cephe Karşılaştırması']:
        districts = sorted(list(set(temp_df_2020['Secim_Cevresi'].unique()) | set(temp_df_2025['Secim_Cevresi'].unique())))
    else:
        active_temp_df = temp_df_2020 if selected_year == '2020' else temp_df_2025
        districts = sorted(active_temp_df['Secim_Cevresi'].unique().tolist())
    selected_district = st.sidebar.selectbox("Seçim Çevresi (İlçe)", ["Tümü"] + districts)

    if selected_district != "Tümü":
        temp_df_2020 = temp_df_2020[temp_df_2020['Secim_Cevresi'] == selected_district]
        temp_df_2025 = temp_df_2025[temp_df_2025['Secim_Cevresi'] == selected_district]

    if selected_year in ['Genel Karşılaştırma', 'Tatar vs. Erhürman', 'Cephe Karşılaştırması']:
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
# 2. ÖZEL HTML'İ BURADA ÇAĞIRIYORUZ
inject_custom_html()

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
    for i in range(3):
        if len(candidate_votes) > i:
            with cols[i]:
                label = ["Birinci 🥇", "İkinci 🥈", "Üçüncü 🥉"][i]
                candidate_name = candidate_votes.index[i].replace('_', ' ')
                vote_count = candidate_votes.iloc[i]
                vote_percentage = (vote_count / total_valid_votes) * 100 if total_valid_votes > 0 else 0
                st.metric(label=label, value=candidate_name)
                st.metric(label="Oy Sayısı", value=f"{int(vote_count):,}")
                st.metric(label="Oy Oranı", value=f"{vote_percentage:.2f}%")
    st.markdown("---")
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
            fig_pie = px.pie(pie_df, values='Oy_Sayısı', names='Aday', title=f"Toplam Geçerli Oy: {int(total_valid_votes):,}", hole=0.3)
            fig_pie.update_traces(textposition='inside', textinfo='percent+label', pull=[0.1 if i==0 else 0 for i in range(len(pie_df))])
            st.plotly_chart(fig_pie, use_container_width=True)
        else: st.warning("Bu seçimde geçerli oy bulunmamaktadır.")

def display_head_to_head(votes_2020, votes_2025, title):
    st.header(title)
    if (votes_2020 is None or votes_2020.empty) and (votes_2025 is None or votes_2025.empty):
        st.warning("Bu karşılaştırma için veri bulunamadı.")
        return

    tatar_2020 = votes_2020.get('Ersin_Tatar', 0) if votes_2020 is not None else 0
    erhurman_2020 = votes_2020.get('Tufan_Erhürman', 0) if votes_2020 is not None else 0
    tatar_2025 = votes_2025.get('Ersin_Tatar_(BAĞ_6)', 0) if votes_2025 is not None else 0
    erhurman_2025 = votes_2025.get('Tufan_Erhürman_(CTP)', 0) if votes_2025 is not None else 0
    max_vote = max(tatar_2020, erhurman_2020, tatar_2025, erhurman_2025)
    yaxis_range_max = max_vote * 1.15

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("2020 Karşılaştırması")
        if votes_2020 is not None and not votes_2020.empty:
            fark = tatar_2020 - erhurman_2020
            kazanan = "Ersin Tatar" if fark > 0 else "Tufan Erhürman" if fark < 0 else "Berabere"
            st.metric("Ersin Tatar'ın Oyu", f"{int(tatar_2020):,}")
            st.metric("Tufan Erhürman'ın Oyu", f"{int(erhurman_2020):,}")
            st.metric("Önde Olan Aday", kazanan, delta=f"{int(fark):,} Oy Fark")
            h2h_df = pd.DataFrame({'Aday': ['Ersin Tatar', 'Tufan Erhürman'], 'Oy': [tatar_2020, erhurman_2020]})
            fig = px.bar(h2h_df, x='Aday', y='Oy', title="2020 İkili Yarış", range_y=[0, yaxis_range_max])
            st.plotly_chart(fig, use_container_width=True)
        else: st.warning("2020 yılı için veri bulunamadı.")
    
    with col2:
        st.subheader("2025 Karşılaştırması")
        if votes_2025 is not None and not votes_2025.empty:
            fark = tatar_2025 - erhurman_2025
            kazanan = "Ersin Tatar" if fark > 0 else "Tufan Erhürman" if fark < 0 else "Berabere"
            st.metric("Ersin Tatar'ın Oyu", f"{int(tatar_2025):,}")
            st.metric("Tufan Erhürman'ın Oyu", f"{int(erhurman_2025):,}")
            st.metric("Önde Olan Aday", kazanan, delta=f"{int(fark):,} Oy Fark")
            h2h_df = pd.DataFrame({'Aday': ['Ersin Tatar', 'Tufan Erhürman'], 'Oy': [tatar_2025, erhurman_2025]})
            fig = px.bar(h2h_df, x='Aday', y='Oy', title="2025 İkili Yarış", range_y=[0, yaxis_range_max])
            st.plotly_chart(fig, use_container_width=True)
        else: st.warning("2025 yılı için veri bulunamadı.")

def display_bloc_comparison(votes_2020, votes_2025, title):
    st.header(title)
    if (votes_2020 is None or votes_2020.empty) and (votes_2025 is None or votes_2025.empty):
        st.warning("Bu karşılaştırma için veri bulunamadı.")
        return

    sol_merkez_2020 = (votes_2020.get('Tufan_Erhürman', 0) + votes_2020.get('Mustafa_Akıncı', 0)) if votes_2020 is not None else 0
    sag_merkez_2020 = votes_2020.get('Ersin_Tatar', 0) if votes_2020 is not None else 0
    sol_merkez_2025 = votes_2025.get('Tufan_Erhürman_(CTP)', 0) if votes_2025 is not None else 0
    sag_merkez_2025 = votes_2025.get('Ersin_Tatar_(BAĞ_6)', 0) if votes_2025 is not None else 0
    max_vote = max(sol_merkez_2020, sag_merkez_2020, sol_merkez_2025, sag_merkez_2025)
    yaxis_range_max = max_vote * 1.15

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("2020 Cephe Analizi")
        fark = sol_merkez_2020 - sag_merkez_2020
        kazanan = "Sol/Merkez Blok" if fark > 0 else "Sağ/Merkez Blok" if fark < 0 else "Berabere"
        st.metric("Sol/Merkez Blok Oyu", f"{int(sol_merkez_2020):,}", help="Tufan Erhürman + Mustafa Akıncı")
        st.metric("Sağ/Merkez Blok Oyu", f"{int(sag_merkez_2020):,}", help="Ersin Tatar")
        st.metric("Önde Olan Blok", kazanan, delta=f"{int(fark):,} Oy Fark")
        bloc_df = pd.DataFrame({'Cephe': ['Sol/Merkez Blok', 'Sağ/Merkez Blok'], 'Oy': [sol_merkez_2020, sag_merkez_2020]})
        fig = px.bar(bloc_df, x='Cephe', y='Oy', title="2020 Blok Oy Dağılımı", range_y=[0, yaxis_range_max], color='Cephe', color_discrete_map={'Sol/Merkez Blok': '#1f77b4', 'Sağ/Merkez Blok': '#d62728'})
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("2025 Cephe Analizi")
        fark = sol_merkez_2025 - sag_merkez_2025
        kazanan = "Sol/Merkez Blok" if fark > 0 else "Sağ/Merkez Blok" if fark < 0 else "Berabere"
        st.metric("Sol/Merkez Blok Oyu", f"{int(sol_merkez_2025):,}", help="Tufan Erhürman")
        st.metric("Sağ/Merkez Blok Oyu", f"{int(sag_merkez_2025):,}", help="Ersin Tatar")
        st.metric("Önde Olan Blok", kazanan, delta=f"{int(fark):,} Oy Fark")
        bloc_df = pd.DataFrame({'Cephe': ['Sol/Merkez Blok', 'Sağ/Merkez Blok'], 'Oy': [sol_merkez_2025, sag_merkez_2025]})
        fig = px.bar(bloc_df, x='Cephe', y='Oy', title="2025 Blok Oy Dağılımı", range_y=[0, yaxis_range_max], color='Cephe', color_discrete_map={'Sol/Merkez Blok': '#1f77b4', 'Sağ/Merkez Blok': '#d62728'})
        st.plotly_chart(fig, use_container_width=True)

# --- Ana uygulama mantığı ---
if 'selected_region' in locals():
    if selected_year == '2020':
        title = get_title("2020 Sonuçları", selected_region, selected_district, selected_ballot_box)
        display_year_results(filtered_df_2020, candidate_votes_2020_filtered, "2020", title)
    elif selected_year == '2025':
        title = get_title("2025 Sonuçları", selected_region, selected_district, selected_ballot_box)
        display_year_results(filtered_df_2025, candidate_votes_2025_filtered, "2025", title)
    elif selected_year == 'Genel Karşılaştırma':
        title = get_title("Genel Karşılaştırmalı Sonuçlar", selected_region, selected_district, selected_ballot_box)
        st.header(title)
        col1, col2 = st.columns(2)
        with col1: display_year_results(filtered_df_2020, candidate_votes_2020_filtered, "2020", "2020 Yılı")
        with col2: display_year_results(filtered_df_2025, candidate_votes_2025_filtered, "2025", "2025 Yılı")
    elif selected_year == 'Tatar vs. Erhürman':
        title = get_title("Tatar vs. Erhürman Analizi", selected_region, selected_district, selected_ballot_box)
        display_head_to_head(candidate_votes_2020_filtered, candidate_votes_2025_filtered, title)
    elif selected_year == 'Cephe Karşılaştırması':
        title = get_title("Cephe Karşılaştırması", selected_region, selected_district, selected_ballot_box)
        display_bloc_comparison(candidate_votes_2020_filtered, candidate_votes_2025_filtered, title)
else:
    st.warning("Veri yüklenemedi. Lütfen CSV dosyalarını kontrol edip sayfayı yenileyin.")