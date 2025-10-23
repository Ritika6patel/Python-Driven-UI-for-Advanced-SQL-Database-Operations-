import pandas as pd
import streamlit as st

from db_function import (
    connect_to_db,
    get_basic_info,
    get_additional_tables,
    get_categories,
    get_suppliers,
    add_new_manual_id, get_all_products, get_product_history, place_reorder, get_pending_reorders,
    mark_reorder_as_received
)

# sidebar3

st.sidebar.title("Inventory Management Dashboard")
option = st.sidebar.radio("select option:", ["Basic Information", "Operational Task"])

# main space

st.title("Inventory and Supply chain Dashboard")
db = connect_to_db()
cursor = db.cursor(dictionary=True)

# -----------------BASIC INFORMATION PAGE -----------------

if option == "Basic Information":
    st.header("Basic Metrics")

    # get basic information from DB

    basic_info = get_basic_info(cursor)

    cols = st.columns(3)
    keys = list(basic_info.keys())

    for i in range(3):
        cols[i].metric(label=keys[i], value=basic_info[keys[i]])

    cols = st.columns(3)
    for i in range(3, 6):
        cols[i - 3].metric(label=keys[i], value=basic_info[keys[i]])

    st.divider()

    # fetch and display detailed tables

    tables = get_additional_tables(cursor)
    for labels, data in tables.items():
        st.header(labels)
        df = pd.DataFrame(data)
        st.dataframe(df)
        st.divider()

elif option == "Operational Task":
    st.header("Operational Tasks")
    selected_task = st.selectbox("choose a Task",
                                 ["Add New Product", "Product History", "Place Reorder", "Receive Reorder"])
    if selected_task == "Add New Product":
        st.header("Add New Product")
        categories = get_categories(cursor)
        suppliers = get_suppliers(cursor)

        with st.form("Add Product Form"):
            product_name = st.text_input("Product_Name")
            product_category = st.selectbox("category", categories)
            product_price = st.number_input("price", min_value=0.00)
            product_stock = st.number_input("stock quantity", min_value=0, step=1)
            product_level = st.number_input("reorder level", min_value=0, step=1)

            suppliers_id = [s["supplier_id"] for s in suppliers]
            suppliers_name = [s["supplier_name"] for s in suppliers]

            suppliers_id = st.selectbox(
                "suppliers",
                options=suppliers_id,
                format_func=lambda x: suppliers_name[suppliers_id.index(x)]
            )
            submitted = st.form_submit_button("Add Product")

            if submitted:
                if not product_name:
                    st.error("please enter the product name")
                else:
                    try:
                        add_new_manual_id(cursor,
                                          db,
                                          product_name,
                                          product_category,
                                          product_price,
                                          product_stock,
                                          product_level,
                                          suppliers_id, )
                        st.success(f"product {product_name} added successfully")

                    except Exception as e:
                        st.error("f Error adding the product : {e}")

    # --------------product history ----------------------#

    if selected_task == "Product History":

        st.header("product inventory History")
        product = get_all_products(cursor)
        product_name = [p['product_name'] for p in product]
        product_id = [p['product_id'] for p in product]

        selected_product_name = st.selectbox("select a product", options=product_name)
        if selected_product_name:
            selected_product_ids = product_id[product_name.index(selected_product_name)]
            history_data = get_product_history(cursor, selected_product_ids)
            if history_data:
                df = pd.DataFrame(history_data)
                st.dataframe(df)
            else:
                st.info("No history found for selected product")
    # ---------------place reorder----------------------

    if selected_task == "Place Reorder":
        st.header("Place Reorder")

        product = get_all_products(cursor)
        product_name = [p['product_name'] for p in product]
        product_id = [p['product_id'] for p in product]

        selected_product_name = st.selectbox("select a product", options=product_name)
        reorder_qty = st.number_input("Reorder Quantity", min_value=1, step=1)

        if st.button("Place reorder"):
            if not selected_product_name:
                st.error("Please Select a Product")
            elif reorder_qty <= 0:
                st.error("Reorder Quantity Must Be Greater Than 0")
            else:
                selected_product_ids = product_id[product_name.index(selected_product_name)]
                try:
                    place_reorder(cursor, db, selected_product_name, reorder_qty)
                    st.success(f"order placed for {selected_product_name} with quantity {reorder_qty}")
                except Exception as e:
                    st.error(f"Error replacing reorder {e}")

    # ------------------receiving an order-----------------

    if selected_task == "Receive Reorder":
        st.header("Mark Reorder as Received")

        # fetch order in ordered stage
        pending_reorders = get_pending_reorders(cursor)
        if not pending_reorders:
            st.info("No pending order to receive")
        else:
            reorders_ids = [r['reorder_id'] for r in pending_reorders]
            reorder_labels = [f"ID {r['reorder_id']} - {r['product_name']}" for r in pending_reorders]

            selected_label = st.selectbox("select reorder to mark as received", options=reorder_labels)
            if selected_label:
                selected_reorder_id = reorders_ids[reorder_labels.index(selected_label)]

                if st.button("Mark as Received"):
                    try:
                        mark_reorder_as_received(cursor,db, selected_reorder_id)
                        st.success(f" reorder ID {selected_reorder_id} marked as received")
                    except Exception as e:
                        st.error(f" error {e}")
