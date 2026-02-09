import streamlit as st
import pandas as pd
from database import (
    init_db, get_session, add_property, get_all_properties,
    get_property_by_id, update_property, get_cities, get_filtered_properties,
    get_stats
)
from collector import collect_sample_data
from scorer import calculate_selling_likelihood, get_score_category, get_score_color
from labels import create_labels_for_properties

st.set_page_config(page_title="Property Lead Manager", page_icon="🏠", layout="wide")

# Initialize database
init_db()

st.sidebar.title("🏠 Property Lead Manager")
page = st.sidebar.radio("Navigation", [
    "📊 Dashboard", "🏘️ All Properties", "🔍 Filter & Export", 
    "➕ Add Property", "📥 Import Sample Data"
])

session = get_session()

if page == "📊 Dashboard":
    st.title("📊 Dashboard")
    stats = get_stats(session)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Properties", stats['total_properties'])
    col2.metric("Cities", stats['cities'])
    col3.metric("Avg Score", f"{stats['average_score']:.1f}")

elif page == "🏘️ All Properties":
    st.title("🏘️ All Properties")
    props = get_all_properties(session)
    
    if not props:
        st.info("No properties found. Import sample data.")
    else:
        data = []
        for p in props:
            data.append({
                'ID': p.id,
                'Address': p.address,
                'City': p.city,
                'Owner': p.owner_name or 'N/A',
                'Score': p.sell_score,
                'Type': p.property_type or 'N/A'
            })
        df = pd.DataFrame(data)
        st.dataframe(df)

elif page == "🔍 Filter & Export":
    st.title("🔍 Filter & Export")
    
    cities = get_cities(session)
    city = st.selectbox("City", ["All"] + cities)
    min_score = st.slider("Min Score", 0, 100, 70)
    
    city_filter = None if city == "All" else city
    props = get_filtered_properties(session, city=city_filter, min_score=min_score)
    
    st.write(f"Found {len(props)} properties")
    
    if props:
        data = [{'address': p.address, 'city': p.city, 'owner_name': p.owner_name, 
                'zip_code': p.zip_code, 'score': p.sell_score} for p in props]
        df = pd.DataFrame(data)
        st.dataframe(df)
        
        if st.button("Generate Avery 5160 Labels"):
            with st.spinner("Creating labels..."):
                path = create_labels_for_properties(props, "labels.pdf")
                with open(path, "rb") as f:
                    st.download_button("Download PDF", f, "labels.pdf", "application/pdf")

elif page == "➕ Add Property":
    st.title("➕ Add Property")
    with st.form("add"):
        addr = st.text_input("Address*")
        city = st.text_input("City*")
        zipc = st.text_input("ZIP*")
        owner = st.text_input("Owner Name")
        ptype = st.selectbox("Type", ["Single Family", "Condo", "Townhouse"])
        year = st.number_input("Year Built", 1800, 2024, 2000)
        
        if st.form_submit_button("Add"):
            prop = add_property(session, address=addr, city=city, zip_code=zipc,
                              owner_name=owner, property_type=ptype, year_built=year,
                              state="NJ")
            st.success(f"Added property ID: {prop.id}")

elif page == "📥 Import Sample Data":
    st.title("📥 Import Sample Data")
    n = st.number_input("Count", 1, 200, 50)
    if st.button("Generate"):
        props = collect_sample_data(n)
        for p in props:
            score, reasons = calculate_selling_likelihood(p)
            add_property(session,
                address=p['address'],
                city=p['city'],
                state=p['state'],
                zip_code=p['zip_code'],
                owner_name=p['owner_name'],
                purchase_date=p['purchase_date'],
                purchase_price=p['purchase_price'],
                estimated_value=p['estimated_value'],
                property_type=p['property_type'],
                year_built=p['year_built'],
                sell_score=score,
                score_reasons=reasons
            )
        st.success(f"Added {n} properties!")