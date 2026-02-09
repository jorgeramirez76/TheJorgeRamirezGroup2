"""
Property Lead Management System - Main Streamlit Application
For Jorge - NJ Property Investment Leads

Features:
- Dashboard with lead statistics
- Property list with filtering
- Manual property entry
- Lead scoring
- Avery 5160 label export
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# Import our modules
from database import (
    init_db, get_session, add_property, get_all_properties,
    get_filtered_properties, get_cities, update_property,
    delete_property, get_stats, Property
)
from collector import collect_sample_data
from scorer import score_all_properties, rescore_all_properties
from labels import (
    create_label_pdf, preview_label_text, 
    export_filtered_labels
)

# Page configuration
st.set_page_config(
    page_title="Property Lead Manager",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
init_db()


def get_session_state():
    """Initialize session state variables."""
    if 'last_action' not in st.session_state:
        st.session_state.last_action = None


# Sidebar navigation
st.sidebar.title("🏠 Property Leads")
page = st.sidebar.radio("Navigation", [
    "Dashboard",
    "All Properties", 
    "Add Property",
    "Generate Sample Data",
    "Scoring",
    "Export Labels"
])

get_session_state()

# ==================== DASHBOARD ====================
if page == "Dashboard":
    st.title("Property Lead Management Dashboard")
    st.markdown("Welcome to your NJ Property Lead System, Jorge!")
    
    # Get stats
    session = get_session()
    stats = get_stats(session)
    cities = get_cities(session)
    session.close()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Properties", stats['total_properties'])
    
    with col2:
        st.metric("Average Score", f"{stats['average_score']:.1f}")
    
    with col3:
        st.metric("Cities Covered", stats['cities'])
    
    with col4:
        # High score count
        session = get_session()
        high_score_count = len(get_filtered_properties(session, min_score=70))
        # Check for unscored properties
        unscored = session.query(Property).filter((Property.sell_score == 0) | (Property.sell_score == None)).count()
        session.close()
        st.metric("High-Value Leads (70+)", high_score_count)
        
    # Warning if there are unscored properties
    if unscored > 0:
        st.warning(f"⚠️ {unscored} properties have no score. Click '🔄 Rescore All' above to calculate scores.")
    
    st.divider()
    
    # Quick actions
    st.subheader("Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🎯 View High-Value Leads", use_container_width=True):
            st.session_state.page = "All Properties"
            st.rerun()
    
    with col2:
        if st.button("➕ Add New Property", use_container_width=True):
            st.session_state.page = "Add Property"
            st.rerun()
    
    with col3:
        if st.button("📤 Export Labels", use_container_width=True):
            st.session_state.page = "Export Labels"
            st.rerun()
    
    with col4:
        if st.button("🔄 Rescore All", use_container_width=True):
            with st.spinner("Recalculating all scores..."):
                count = rescore_all_properties()
            st.success(f"Rescored {count} properties!")
            st.rerun()
    
    st.divider()
    
    # Scoring explanation
    with st.expander("ℹ️ How Are Scores Calculated?"):
        st.write("Each property gets a 0-100 score based on these factors:")
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Property Factors:**")
            st.write("• Years Owned (15%) - Longer = higher score")
            st.write("• Property Age (10%) - Older = higher score")
            st.write("• Assessed Value (10%) - Higher equity = higher score")
            st.write("• Property Type (5%) - Multi-family scores higher")
        with col2:
            st.write("**Owner/Market Factors:**")
            st.write("• Absentee Owner (20%) - Different address = higher score")
            st.write("• Market Timing (15%) - Seasonal trends")
            st.write("• Distress Signals (25%) - Tax issues, probate, etc.")
        st.write("\n**Score Ranges:** 🔴 70-100 Hot | 🟠 50-69 Warm | 🟡 30-49 Cool | ⚪ 0-29 Cold")
    
    st.divider()
    
    # Recent properties
    st.subheader("Top Scored Properties")
    session = get_session()
    top_props = get_filtered_properties(session, min_score=0)[:10]
    session.close()
    
    if top_props:
        df = pd.DataFrame([{
            'ID': p.id,
            'Address': p.address,
            'City': p.city,
            'Owner': p.owner_name or 'N/A',
            'Score': p.sell_score,
            'Type': p.property_type or 'N/A'
        } for p in top_props])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No properties in database. Generate sample data or add properties manually.")


# ==================== ALL PROPERTIES ====================
elif page == "All Properties":
    st.title("Property Database")
    
    # Filters
    st.subheader("Filters")
    
    session = get_session()
    cities = ['All'] + get_cities(session)
    session.close()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_city = st.selectbox("City", cities)
    
    with col2:
        min_score = st.slider("Minimum Score", 0, 100, 0)
    
    with col3:
        max_score = st.slider("Maximum Score", 0, 100, 100)
    
    # Apply filters
    session = get_session()
    city_filter = None if selected_city == 'All' else selected_city
    properties = get_filtered_properties(
        session, 
        city=city_filter,
        min_score=min_score,
        max_score=max_score
    )
    session.close()
    
    st.write(f"Showing {len(properties)} properties")
    
    # Display as table
    if properties:
        df = pd.DataFrame([{
            'ID': p.id,
            'Address': p.address,
            'City': p.city,
            'Owner': p.owner_name or 'N/A',
            'Score': p.sell_score,
            'Type': p.property_type or 'N/A',
            'Value': f"${p.assessed_value:,.0f}" if p.assessed_value else 'N/A',
            'Year': p.year_built or 'N/A',
            'Status': p.status
        } for p in properties])
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Detail view
        st.subheader("Property Details")
        selected_id = st.selectbox("Select Property ID for Details", [p.id for p in properties])
        
        if selected_id:
            session = get_session()
            prop = session.query(get_session().bind.engine.table_names())
            # Re-query to get the property
            from database import Property
            prop = session.query(Property).filter(Property.id == selected_id).first()
            
            if prop:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Property Information**")
                    st.write(f"Address: {prop.full_address}")
                    st.write(f"Type: {prop.property_type or 'Unknown'}")
                    st.write(f"Year Built: {prop.year_built or 'Unknown'}")
                    st.write(f"Bedrooms: {prop.bedrooms or 'N/A'}")
                    st.write(f"Bathrooms: {prop.bathrooms or 'N/A'}")
                    st.write(f"Sq Ft: {prop.square_footage:,}" if prop.square_footage else "Sq Ft: N/A")
                
                with col2:
                    st.write("**Owner & Scoring**")
                    st.write(f"Owner: {prop.owner_name or 'Unknown'}")
                    st.write(f"Mailing: {prop.owner_address or 'Same as property'}")
                    
                    # Score display with color coding
                    score = prop.sell_score or 0
                    if score >= 70:
                        score_color = "🔴"
                        score_label = "HOT LEAD"
                    elif score >= 50:
                        score_color = "🟠"
                        score_label = "WARM LEAD"
                    elif score >= 30:
                        score_color = "🟡"
                        score_label = "COOL LEAD"
                    else:
                        score_color = "⚪"
                        score_label = "COLD LEAD"
                    
                    st.markdown(f"**Sell Score: {score}/100** {score_color} *{score_label}*")
                    
                    # Detailed scoring breakdown
                    with st.expander("📊 View Detailed Scoring Breakdown"):
                        st.write("**Factors Contributing to Score:**")
                        
                        if prop.score_reasons:
                            reasons = prop.score_reasons.split(';')
                            for reason in reasons:
                                if reason.strip():
                                    st.write(f"  ✅ {reason.strip()}")
                        else:
                            st.write("  • Not yet scored")
                        
                        st.divider()
                        st.write("**Scoring Factors Used:**")
                        st.write("  • Years Owned (15% weight)")
                        st.write("  • Property Age (10% weight)")
                        st.write("  • Assessed Value (10% weight)")
                        st.write("  • Absentee Owner (20% weight)")
                        st.write("  • Property Type (5% weight)")
                        st.write("  • Market Timing (15% weight)")
                        st.write("  • Distress Signals (25% weight)")
                        
                        if prop.year_built:
                            age = datetime.now().year - prop.year_built
                            st.write(f"\n  **Property Age:** {age} years")
                        if prop.assessed_value:
                            st.write(f"  **Assessed Value:** ${prop.assessed_value:,.0f}")
                    
                    st.write(f"Status: **{prop.status.upper()}**")
                    
                    # Status update
                    new_status = st.selectbox(
                        "Update Status",
                        ['new', 'contacted', 'qualified', 'unqualified'],
                        index=['new', 'contacted', 'qualified', 'unqualified'].index(prop.status)
                    )
                    
                    if new_status != prop.status:
                        if st.button("Update Status"):
                            prop.status = new_status
                            session.commit()
                            st.success(f"Status updated to {new_status}")
                            st.rerun()
                
                # Notes
                st.write("**Notes**")
                notes = st.text_area("Property Notes", value=prop.notes or "", key=f"notes_{prop.id}")
                if st.button("Save Notes"):
                    prop.notes = notes
                    session.commit()
                    st.success("Notes saved!")
            
            session.close()
    else:
        st.info("No properties match your filters.")


# ==================== ADD PROPERTY ====================
elif page == "Add Property":
    st.title("Add New Property")
    
    with st.form("add_property_form"):
        st.subheader("Property Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            address = st.text_input("Street Address*", placeholder="123 Main St")
            city = st.text_input("City*", placeholder="Newark")
            state = st.text_input("State", value="NJ", max_chars=2)
            zip_code = st.text_input("ZIP Code*", placeholder="07102", max_chars=10)
        
        with col2:
            property_type = st.selectbox(
                "Property Type",
                ['', 'Single Family', 'Condo', 'Townhouse', 'Multi-Family', 'Commercial']
            )
            year_built = st.number_input("Year Built", min_value=1800, max_value=2024, value=None)
            assessed_value = st.number_input("Assessed Value ($)", min_value=0, value=None)
            square_footage = st.number_input("Square Footage", min_value=0, value=None)
        
        st.subheader("Owner Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            owner_name = st.text_input("Owner Name", placeholder="John Smith")
        
        with col2:
            use_diff_address = st.checkbox("Different Mailing Address")
        
        owner_address = None
        if use_diff_address:
            owner_address = st.text_area(
                "Mailing Address",
                placeholder="456 Oak Ave\nJersey City, NJ 07302"
            )
        
        notes = st.text_area("Notes")
        
        submitted = st.form_submit_button("Add Property", use_container_width=True)
        
        if submitted:
            if not address or not city or not zip_code:
                st.error("Please fill in required fields (marked with *)")
            else:
                session = get_session()
                prop = add_property(
                    session,
                    address=address,
                    city=city,
                    state=state or 'NJ',
                    zip_code=zip_code,
                    owner_name=owner_name or None,
                    owner_address=owner_address,
                    property_type=property_type or None,
                    year_built=year_built,
                    assessed_value=assessed_value,
                    square_footage=square_footage,
                    notes=notes,
                    data_source='manual'
                )
                session.close()
                
                st.success(f"Property added successfully! ID: {prop.id}")
                st.info("Go to 'Scoring' to calculate the sell score for this property.")


# ==================== GENERATE SAMPLE DATA ====================
elif page == "Generate Sample Data":
    st.title("Generate Sample Data")
    st.markdown("Create demo property data for testing the system.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        sample_city = st.selectbox(
            "Select City (or leave for random)",
            ['Random Mix'] + [
                'Newark', 'Jersey City', 'Paterson', 'Elizabeth', 'Edison',
                'Toms River', 'Trenton', 'Clifton', 'Cherry Hill'
            ]
        )
    
    with col2:
        sample_count = st.number_input("Number of Properties", min_value=1, max_value=500, value=50)
    
    city_param = None if sample_city == 'Random Mix' else sample_city
    
    if st.button("Generate Sample Data", use_container_width=True):
        with st.spinner("Generating properties..."):
            ids = collect_sample_data(city=city_param, count=sample_count)
        
        st.success(f"Generated {len(ids)} sample properties!")
        st.info("Now go to 'Scoring' to calculate sell scores for these properties.")
        
        # Preview
        if st.checkbox("Show Preview"):
            session = get_session()
            from database import Property
            props = session.query(Property).order_by(Property.id.desc()).limit(5).all()
            session.close()
            
            for p in props:
                st.write(f"- {p.address}, {p.city} - Owner: {p.owner_name}")


# ==================== SCORING ====================
elif page == "Scoring":
    st.title("Lead Scoring Engine")
    st.markdown("Calculate selling likelihood scores for properties.")
    
    # Show scoring factors
    with st.expander("View Scoring Factors"):
        st.write("The scoring engine considers:")
        st.write("- **Years Owned** (15%): Long-term owners more likely to sell")
        st.write("- **Property Age** (10%): Older properties may need updates")
        st.write("- **Assessed Value** (10%): Higher values indicate equity position")
        st.write("- **Absentee Owner** (20%): Non-occupant owners more likely to sell")
        st.write("- **Property Type** (5%): Multi-family/commercial factors")
        st.write("- **Market Timing** (15%): Seasonal trends")
        st.write("- **Distress Signals** (25%): Tax issues, probate, etc.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Score New Properties")
        if st.button("Score Unscored Properties", use_container_width=True):
            with st.spinner("Calculating scores..."):
                count = score_all_properties()
            st.success(f"Scored {count} properties!")
    
    with col2:
        st.subheader("Re-score All")
        st.warning("This will overwrite existing scores")
        if st.button("Re-score All Properties", use_container_width=True):
            with st.spinner("Re-scoring all properties..."):
                count = rescore_all_properties()
            st.success(f"Re-scored {count} properties!")
    
    st.divider()
    
    # Show score distribution
    st.subheader("Score Distribution")
    
    session = get_session()
    properties = get_all_properties(session)
    session.close()
    
    if properties:
        scores = [p.sell_score for p in properties if p.sell_score > 0]
        
        if scores:
            # Use Streamlit's native bar chart instead of plotly
            import pandas as pd
            
            # Create bins for the histogram
            bins = [0, 20, 40, 60, 80, 100]
            labels = ['0-20', '21-40', '41-60', '61-80', '81-100']
            
            # Count properties in each bin
            bin_counts = {}
            for label in labels:
                bin_counts[label] = 0
            
            for score in scores:
                if score <= 20:
                    bin_counts['0-20'] += 1
                elif score <= 40:
                    bin_counts['21-40'] += 1
                elif score <= 60:
                    bin_counts['41-60'] += 1
                elif score <= 80:
                    bin_counts['61-80'] += 1
                else:
                    bin_counts['81-100'] += 1
            
            chart_data = pd.DataFrame({
                'Score Range': list(bin_counts.keys()),
                'Number of Properties': list(bin_counts.values())
            })
            
            st.bar_chart(chart_data.set_index('Score Range'))
            
            # Score ranges
            st.write("**Score Ranges:**")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                high = len([s for s in scores if s >= 70])
                st.metric("High (70-100)", high)
            
            with col2:
                med = len([s for s in scores if 40 <= s < 70])
                st.metric("Medium (40-69)", med)
            
            with col3:
                low = len([s for s in scores if s < 40])
                st.metric("Low (0-39)", low)
            
            with col4:
                unscored = len([p for p in properties if p.sell_score == 0])
                st.metric("Unscored", unscored)
        else:
            st.info("No properties have been scored yet. Click 'Score Unscored Properties' above.")
    else:
        st.info("No properties in database.")


# ==================== EXPORT LABELS ====================
elif page == "Export Labels":
    st.title("Export Mailing Labels")
    st.markdown("Generate PDF mailing labels for Avery 5160 label sheets.")
    
    st.info("📄 **Avery 5160 Specs:** 30 labels per sheet, 1\" x 2-5/8\", 3 columns x 10 rows")
    
    # Filters for export
    st.subheader("Filter Properties for Export")
    
    session = get_session()
    cities = ['All'] + get_cities(session)
    session.close()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        export_city = st.selectbox("City", cities, key="export_city")
    
    with col2:
        export_min_score = st.slider("Min Score", 0, 100, 50, key="export_min")
    
    with col3:
        export_max_score = st.slider("Max Score", 0, 100, 100, key="export_max")
    
    # Address preference
    use_mailing = st.checkbox("Use owner's mailing address when available", value=True)
    
    # Preview
    if st.button("Preview Labels"):
        session = get_session()
        city_filter = None if export_city == 'All' else export_city
        properties = get_filtered_properties(
            session,
            city=city_filter,
            min_score=export_min_score,
            max_score=export_max_score
        )
        session.close()
        
        if properties:
            st.text(preview_label_text(properties, max_preview=5))
            st.write(f"Total: {len(properties)} labels ({(len(properties) + 29) // 30} pages)")
        else:
            st.warning("No properties match your filters.")
    
    # Generate PDF
    if st.button("Generate PDF Labels", type="primary", use_container_width=True):
        session = get_session()
        city_filter = None if export_city == 'All' else export_city
        properties = get_filtered_properties(
            session,
            city=city_filter,
            min_score=export_min_score,
            max_score=export_max_score
        )
        session.close()
        
        if properties:
            from io import BytesIO
            
            pdf_buffer = create_label_pdf(properties, use_mailing_address=use_mailing)
            
            st.success(f"Generated {len(properties)} labels ({(len(properties) + 29) // 30} pages)")
            
            st.download_button(
                label="📥 Download PDF Labels",
                data=pdf_buffer,
                file_name=f"property_labels_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.error("No properties match your filters. Cannot generate empty PDF.")


# Footer
st.sidebar.divider()
st.sidebar.caption("Property Lead Manager v1.0")
st.sidebar.caption("Built for Jorge 🏠")