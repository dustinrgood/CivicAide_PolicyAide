import streamlit as st
import pandas as pd
import numpy as np

# Set page title
st.title('Policy Analysis Dashboard - Test')

# Add some sample text
st.write('This is a test dashboard to verify Streamlit is working correctly.')

# Create some sample data
data = {
    'Policy': ['Policy A', 'Policy B', 'Policy C'],
    'Environmental Impact': [8, 6, 9],
    'Economic Feasibility': [7, 8, 5],
    'Equity': [6, 7, 8],
    'Implementation Complexity': [5, 4, 7]
}

df = pd.DataFrame(data)

# Display the data as a table
st.subheader('Sample Policy Impact Matrix')
st.dataframe(df)

# Create a simple chart
st.subheader('Impact Visualization')
chart_data = df.set_index('Policy')
st.bar_chart(chart_data)

# Add an interactive element
st.subheader('Interactive Elements')
selected_policy = st.selectbox('Select a policy to view details:', df['Policy'])
st.write(f'You selected: {selected_policy}')

# Show filtered data based on selection
filtered_data = df[df['Policy'] == selected_policy]
st.write('Details:')
st.dataframe(filtered_data) 