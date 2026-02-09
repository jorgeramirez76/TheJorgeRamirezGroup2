import streamlit as st
import pandas as pd
from database import (
    add_property, get_all_properties, get_property_by_id,
    update_property_score, delete_property, get_cities, 
    mark_as_exported, get_property_count, get_stats_by_city
)
from collector import collect_sample_data
from scorer import calculate_selling_likelihood, get_score_category, get_score_color
from labels import create_labels_for_properties
import os

st.set_page_config(page_title="Property Lead Manager", page_icon="🏠", layout="wide")

st.sidebar.title("🏠 Property Lead Manager")
page = st.sidebar.radio("Navigation", [
    "📊 Dashboard", "🏘️ All Properties", "🔍 Filter & Export", 
    "➕ Add Property", "📥 Import Sample Data"
])

if page == "📊 Dashboard":
    st.title("📊 Dashboard")
    total = get_property_count()
    stats = get_stats_by_city()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Properties", total)
    col2.metric("Cities", len(stats) if stats else 0)
    if stats:
        avg = sum(s['avg_score'] for s in stats) / len(stats)
        col3.metric("Avg Score", f"{avg:.1f}")
    
    if stats:
        st.subheader("By City")
        df = pd.DataFrame(stats)
        st.dataframe(df)
    else:
        st.info("Import sample data to get started!")

elif page == "🏘️ All Properties":
    st.title("🏘️ All Properties")
    props = get_all_properties()
    
    if not props:
        st.info("No properties found.")
    else:
        for p in props:
            if not p.get('score'):
                score, reasons = calculate_selling_likelihood(p)
                p['score'] = score
        
        df = pd.DataFrame(props)
        st.dataframe(df[['address', 'city', 'owner_name', 'score', 'property_type']])

elif page == "🔍 Filter & Export":
    st.title("🔍 Filter & Export")
    
    cities = get_cities()
    city = st.selectbox("City", ["All"] + cities)
    min_score = st.slider("Min Score", 0, 100, 70)
    
    city_filter = None if city == "All" else city
    props = get_all_properties(city=city_filter, min_score=min_score)
    
    st.write(f"Found {len(props)} properties")
    
    if props:
        df = pd.DataFrame(props)
        st.dataframe(df[['address', 'city', 'owner_name', 'score']])
        
        if st.button("Generate Avery 5160 Labels"):
            with st.spinner("Creating labels..."):
                path = create_labels_for_properties(props, "labels.pdf")
                mark_as_exported([p['id'] for p in props])
                with open(path, "rb") as f:
                    st.download_button("Download PDF", f, "labels.pdf", "application/pdf")

elif page == "➕ Add Property":
    st.title("➕ Add Property")
    with st.form("add"):
        addr = st.text_input("Address*")
        city = st.text_input("City*")
        zipc = st.text_input("ZIP*")
        owner = st.text_input("Owner Name")
        ptype = st.selectbox("Type", ["Single Family", "Condo", "Townhouse", "Multi-Family"])
        year = st.number_input("Year Built", 1800, 2024, 2000)
        price = st.number_input("Purchase Price", 0, value=300000)
        value = st.number_input("Current Value", 0, value=400000)
        
        if st.form_submit_button("Add"):
            data = {"address": addr, "city": city, "zip_code": zipc, "owner_name": owner,
                    "property_type": ptype, "year_built": year, "purchase_price": price,
                    "estimated_value": value, "state": "NJ", "purchase_date": "2020-01-01"}
            pid = add_property(data)
            score, _ = calculate_selling_likelihood(data)
            update_property_score(pid, score, "")
            st.success(f"Added! Score: {score}")

elif page == "📥 Import Sample Data":
    st.title("📥 Import Sample Data")
    n = st.number_input("Count", 1, 200, 50)
    if st.button("Generate"):
        with st.spinner("Generating..."):
            props = collect_sample_data(n)
            for p in props:
                pid = add_property(p)
                score, reasons = calculate_selling_likelihood(p)
                update_property_score(pid, score, reasons)
            st.success(f"Added {n} properties!")