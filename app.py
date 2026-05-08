import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="EV Industrial ERP", layout="wide", page_icon="🏭")

FILE_NAME = "ev_industrial_data.csv"

def load_data():
    default_columns = ["Date", "Dealer", "Model", "Battery Config", "Color Details", "Total Qty", "Total Value", "Paid", "Balance", "Stage"]
    if os.path.exists(FILE_NAME):
        df = pd.read_csv(FILE_NAME)
        for col in default_columns:
            if col not in df.columns: df[col] = "N/A"
        return df
    return pd.DataFrame(columns=default_columns)

if 'data' not in st.session_state:
    st.session_state.data = load_data()

# --- SIDEBAR: NEW BOOKING ---
st.sidebar.title("🏭 EV ERP System")
with st.sidebar.form("booking_form", clear_on_submit=True):
    b_date = st.date_input("Booking Date", datetime.now())
    b_name = st.text_input("Dealer Name")
    b_model = st.selectbox("Vehicle Model", ["SL", "DL", "CS", "LOADER"])
    b_type = st.radio("Battery Option", ["With Battery", "Without Battery"])
    
    battery_info = "No Battery"
    if b_type == "With Battery":
        b_volts = st.selectbox("Voltage", ["48V", "60V", "72V"])
        b_pieces = st.number_input("Pieces per Vehicle", min_value=1, value=4)
        battery_info = f"{b_volts} ({b_pieces} Pcs)"
    
    st.write("---")
    st.write("**Colors:**")
    c1, c2 = st.columns(2)
    q_red, q_blue = c1.number_input("RED", 0), c2.number_input("BLUE", 0)
    q_grey, q_silver = c1.number_input("GREY", 0), c2.number_input("SILVER", 0)
    q_green, q_l_green = c1.number_input("GREEN", 0), c2.number_input("L-GREEN", 0)
    q_m_blue = st.number_input("MATT BLUE", 0)
    
    b_total_val = st.number_input("Total Value (₹)", 0)
    b_adv = st.number_input("Advance (₹)", 0)
    
    if st.form_submit_button("Confirm Booking"):
        if b_name:
            color_map = {"RED":q_red, "BLUE":q_blue, "GREY":q_grey, "SILVER":q_silver, "GREEN":q_green, "L-GREEN":q_l_green, "M-BLUE":q_m_blue}
            colors = [f"{c}:{v}" for c, v in color_map.items() if v > 0]
            color_str = ", ".join(colors)
            total_qty = sum(color_map.values())
            new_entry = pd.DataFrame([[b_date.strftime("%Y-%m-%d"), b_name, b_model, battery_info, color_str, total_qty, b_total_val, b_adv, b_total_val-b_adv, "Awaiting Dispatch"]], columns=st.session_state.data.columns)
            st.session_state.data = pd.concat([st.session_state.data, new_entry], ignore_index=True)
            st.session_state.data.to_csv(FILE_NAME, index=False)
            st.rerun()

# --- MAIN DASHBOARD ---
st.title("⚡ EV B2B Business Dashboard")
df = st.session_state.data

if not df.empty:
    m1, m2, m3 = st.columns(3)
    pending = df[df['Stage'] == "Awaiting Dispatch"]
    m1.metric("Pending Units", int(pending['Total Qty'].sum()))
    m2.metric("Total Outstanding", f"₹{df['Balance'].sum():,.2f}")
    m3.metric("Total Bookings", len(df))

    tab1, tab2 = st.tabs(["🚀 Dispatch Queue", "📜 Full Ledger & Delete"])

    with tab1:
        if pending.empty:
            st.success("No pending dispatches.")
        else:
            for idx, row in pending.iterrows():
                # Expandable row
                with st.expander(f"Dealer: {row['Dealer']} | Model: {row['Model']} | Qty: {int(row['Total Qty'])}"):
                    st.write(f"**Battery:** {row['Battery Config']} | **Colors:** {row['Color Details']}")
                    if st.button(f"Mark as Dispatched ✅", key=f"disp_{idx}"):
                        st.session_state.data.at[idx, 'Stage'] = "Dispatched"
                        st.session_state.data.to_csv(FILE_NAME, index=False)
                        st.rerun()

    with tab2:
        st.dataframe(df, use_container_width=True)
        
        st.divider()
        st.subheader("🗑️ Delete/Cancel an Order")
        # Direct Delete Dropdown
        delete_row = st.selectbox("Select Dealer to Delete:", df.index, format_func=lambda x: f"{df.iloc[x]['Dealer']} - {df.iloc[x]['Date']}")
        if st.button("Delete Selected Record"):
            st.session_state.data = st.session_state.data.drop(delete_row).reset_index(drop=True)
            st.session_state.data.to_csv(FILE_NAME, index=False)
            st.warning("Record Deleted!")
            st.rerun()

else:
    st.info("No records found.")
