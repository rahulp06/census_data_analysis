import streamlit as st
import pandas as pd
import numpy as np

# Set page configuration for a wider layout
st.set_page_config(layout="wide")

st.title("📊 Complete Census Data Analysis Dashboard")
st.markdown("Upload the `census.csv` file to generate a full suite of demographic, income, and projection reports.")

# --- Constants ---
CITIZEN_STATUS = 'NativeBornintheUnitedStates'

# --- Data Cleaning Function ---
@st.cache_data
def clean_data(data):
    """Performs necessary cleaning and standardization on the DataFrame."""
    
    # 1. Standardize column names
    data.columns = data.columns.str.replace(' ', '_').str.replace('[\(\)/,-]+', '', regex=True)
    data.columns = data.columns.str.replace('.', '', regex=False)

    # 2. Clean string columns (removing spaces and hyphens)
    for col in ['Education', 'Marital_Status', 'Gender', 'Tax_status', 'Parental_status', 'Country', 'Citizenship']:
        if col in data.columns:
            # Handle potential non-string types before calling str methods
            data[col] = data[col].astype(str).str.replace(' ', '').str.replace('-', '')
            # Specific cleanup for concatenated values
            data[col] = data[col].str.replace('civilianspousepresent', '').str.replace('ArmedForcesspousepresent', '')
            
    # 3. Clean and convert Weeks_worked to integer
    if 'Weeks_worked' in data.columns:
        # Coerce errors (like '?') to NaN, fill NaN with 0, then convert to int
        data['Weeks_worked'] = pd.to_numeric(data['Weeks_worked'], errors='coerce').fillna(0).astype(int)
        
    return data

# --- Main Application Logic ---
uploaded_file = st.file_uploader("Upload a CSV file (e.g., 'census.csv')", type="csv")
census_data = None
X_years = 5 # Default projection period

if uploaded_file is not None:
    try:
        raw_data = pd.read_csv(uploaded_file)
        # Use copy to avoid setting value warning on slice in the cleaning function
        census_data = clean_data(raw_data.copy()) 
        
        st.success("✅ File uploaded and cleaned successfully!")
        st.subheader("🔍 Data Preview (Cleaned)")
        st.dataframe(census_data.head())
        
        st.markdown("---")

        # --- Projection Input ---
        st.header("⚙️ Settings")
        # X_years updates on every script rerun (i.e., whenever the input changes)
        X_years = st.number_input(
            "Set Projection Period (X years)", 
            min_value=1, 
            max_value=20, 
            value=5, 
            step=1, 
            help="This value (X) is used to project future senior citizens and voters."
        )
        st.markdown("---")
        
    except Exception as e:
        st.error(f"Error processing file: {e}")
        census_data = None

# --- Analysis Buttons Section (Vertical Stack) ---
if census_data is not None:
    
    st.header("🔬 Analytical Reports")
    
    # --- Section 1: Core Demographics & Income ---
    st.subheader("Core Metrics")
    
    b1_c1, b1_c2, b1_c3 = st.columns(3)
    
    with b1_c1:
        if st.button("Calculate Sex Ratio", use_container_width=True):
            gender_counts = census_data['Gender'].value_counts()
            male = gender_counts.get('Male', 0)
            female = gender_counts.get('Female', 0)
            st.metric("Sex Ratio (Male : Female)", f"{male} : {female}")
            st.info(f"Ratio: {male/female:.2f} males per female.")

        if st.button("Overall Per Capita Income", use_container_width=True):
            overall_income = census_data['Income'].sum() / census_data.shape[0]
            st.metric("Overall Per Capita Income", f"${overall_income:,.2f}")
    
    with b1_c2:
        if st.button("Gender-wise Per Capita Income", use_container_width=True):
            gender_per_capita = census_data.groupby('Gender')['Income'].mean().reset_index()
            st.dataframe(gender_per_capita)
        
        if st.button("Gender-wise Total Income", use_container_width=True):
            gender_total_income = census_data.groupby('Gender')['Income'].sum().reset_index()
            gender_total_income.columns = ['Gender', 'Total Income Generated']
            st.dataframe(gender_total_income)
            
            # --- Added the missing bar chart here ---
            st.bar_chart(gender_total_income.set_index('Gender'))
            # ---------------------------------------------

    with b1_c3:
        if st.button("Income by Tax Status (Total Tax)", use_container_width=True):
            tax_income = census_data.groupby('Tax_status')['Income'].sum().reset_index()
            tax_income.columns = ['Tax Status', 'Total Income Generated']
            st.dataframe(tax_income.sort_values(by='Total Income Generated', ascending=False))
            st.bar_chart(tax_income.set_index('Tax Status'))

    st.divider() # Visual separator
            
    # --- Section 2: Age and Dynamic Projections ---
    st.subheader("Age & Dynamic Projections (Based on X Years Setting)")
    
    b2_c1, b2_c2, b2_c3, b2_c4 = st.columns(4)
    
    # Static Report Button (Age > 60)
    with b2_c1:
        if st.button("Age > 60: Citizen vs. Non-Citizen", use_container_width=True):
            age_above_60 = census_data[census_data['Age'] > 60]
            citizens = age_above_60[age_above_60['Citizenship'] == CITIZEN_STATUS].shape[0]
            non_citizens = age_above_60[age_above_60['Citizenship'] != CITIZEN_STATUS].shape[0]
            
            st.metric("Citizens (Age > 60)", f"{citizens}")
            st.metric("Non-Citizens (Age > 60)", f"{non_citizens}")
    
    # Dynamic Projection Metrics (Update with X_years change)
    with b2_c2:
        # Senior Citizen Projection 
        senior_projection = census_data[
            (census_data['Age'] >= (60 - X_years)) & (census_data['Age'] <= (60 - 1))
        ].shape[0]
        st.metric(f"New Seniors in {X_years} Years (Ages {60-X_years}-{59})", senior_projection)

    with b2_c3:
        # Voter Projection 
        voter_projection = census_data[
            (census_data['Age'] >= (18 - X_years)) & (census_data['Age'] <= (18 - 1))
        ].shape[0]
        st.metric(f"New Voters in {X_years} Years (Ages {18-X_years}-{17})", voter_projection)
        
    with b2_c4:
        # Pension Amount Proxy 
        pension_amount = census_data[
            (census_data['Age'] >= (60 - X_years)) & (census_data['Age'] <= (60 - 1))
        ]['Income'].sum()
        st.metric("Pension Amount Proxy (Income of Near-Seniors)", f"${pension_amount:,.2f}")
            
    st.divider() # Visual separator

    # --- Section 3: Non-Citizens & Marital Status ---
    st.subheader("Non-Citizen & Marital Status")

    b3_c1, b3_c2, b3_c3 = st.columns(3)
    
    with b3_c1:
        if st.button("Money Generated for Non-Citizens", use_container_width=True):
            non_citizens = census_data[census_data['Citizenship'] != CITIZEN_STATUS]
            money_generated = non_citizens['Income'].sum()
            st.metric("Total Income from Non-Citizens", f"${money_generated:,.2f}")

        if st.button("Non-Citizens Working %", use_container_width=True):
            non_citizens = census_data[census_data['Citizenship'] != CITIZEN_STATUS]
            total_non_citizens = non_citizens.shape[0]
            working_non_citizens = non_citizens[non_citizens['Weeks_worked'] > 0].shape[0]
            working_percent = (working_non_citizens / total_non_citizens) * 100 if total_non_citizens > 0 else 0
            st.metric("Non-Citizens Working Percentage", f"{working_percent:.2f}%")
            
    with b3_c2:
        if st.button("Total Widow Female Candidates", use_container_width=True):
            widow_females = census_data[(census_data['Gender'] == 'Female') & (census_data['Marital_Status'] == 'Widowed')].shape[0]
            st.metric("Total Widow Female Candidates", widow_females)

        if st.button("Employable Widows/Divorced (Overall)", use_container_width=True):
            employable_overall = census_data[
                (census_data['Age'] >= 18) & (census_data['Marital_Status'].isin(['Widowed', 'Divorced'])) & 
                (census_data['Weeks_worked'] > 0)
            ].shape[0]
            st.metric("Overall Employable Widows/Divorced", employable_overall)

    with b3_c3:
        if st.button("Employable Female Citizens (W/D)", use_container_width=True):
             employable_fem_cit = census_data[
                (census_data['Age'] >= 18) & (census_data['Gender'] == 'Female') & (census_data['Citizenship'] == CITIZEN_STATUS) & 
                (census_data['Marital_Status'].isin(['Widowed', 'Divorced'])) & (census_data['Weeks_worked'] > 0)
            ].shape[0]
             st.metric("Empl. Female Citizen (Widow/Divorced)", employable_fem_cit)
            
    st.divider() # Visual separator
            
    # --- Section 4: Parental Status ---
    st.subheader("Parental Status")
    
    b4_c1, b4_c2 = st.columns(2)
    
    with b4_c1:
        if st.button("Orphan Count by Gender", use_container_width=True):
            # Orphan defined as Parental_status = 'Neitherparentpresent'
            orphan_counts = census_data[census_data['Parental_status'] == 'Neitherparentpresent'].groupby('Gender').size().reset_index(name='Count')
            st.dataframe(orphan_counts)
            st.info("Orphan defined as neither parent present.")

    with b4_c2:
        if st.button("Children (< 18) by Parental Status", use_container_width=True):
            children_data = census_data[census_data['Age'] < 18]
            children_parental_gender_count = children_data.groupby(['Parental_status', 'Gender']).size().reset_index(name='Count')
            st.dataframe(children_parental_gender_count)
            st.info("Count of individuals under 18 by their parental living situation.")
            
    st.divider() # Visual separator

    # --- Section 5: Education & Employment ---
    st.subheader("Education & Work")
    
    b5_c1, b5_c2 = st.columns(2)

    with b5_c1:
        if st.button("Education Distribution", use_container_width=True):
            education_distribution = census_data['Education'].value_counts().sort_values(ascending=False)
            st.bar_chart(education_distribution)
            st.dataframe(education_distribution)
            
        if st.button("Education Qualification Count based on Employment", use_container_width=True):
            employed_data = census_data[census_data['Weeks_worked'] > 0]
            employed_by_education = employed_data.groupby('Education').size().reset_index(name='Employed Count')
            employed_by_education = employed_by_education.sort_values(by='Employed Count', ascending=False)
            st.dataframe(employed_by_education)
            st.bar_chart(employed_by_education.set_index('Education'))

    with b5_c2:
        if st.button("Education category-wise gender-wise count", use_container_width=True):
            education_gender_count = census_data.groupby(['Education', 'Gender']).size().reset_index(name='Count')
            st.dataframe(education_gender_count.sort_values(by='Count', ascending=False))
            st.info("Shows the count for each combination of education and gender.")

        if st.button("Unemployed Citizens (Age >= 23) by Education", use_container_width=True):
            unemployed_citizens = census_data[
                (census_data['Age'] >= 23) & (census_data['Citizenship'] == CITIZEN_STATUS) & (census_data['Weeks_worked'] == 0)
            ]
            unemployed_by_education = unemployed_citizens.groupby('Education').size().reset_index(name='Count')
            unemployed_by_education = unemployed_by_education.sort_values(by='Count', ascending=False)
            st.dataframe(unemployed_by_education)
            st.bar_chart(unemployed_by_education.set_index('Education'))
            st.info("Filter: Citizens, Age 23+, Weeks Worked = 0.")

else:
    st.info("👆 Please upload a CSV file to continue with the analysis.")
