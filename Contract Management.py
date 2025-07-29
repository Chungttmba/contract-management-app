import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io
from datetime import datetime

# === Cấu hình ===
FILE_NAME = "contracts.xlsx"
INFO_FILE = "info.xlsx"
columns = [
    "Mã hợp đồng", "Khách hàng", "Ngày ký", "Giá trị", "Trạng thái",
    "Tình trạng thanh toán", "Giá trị quyết toán",
    "Lịch sử thanh toán", "Tổng đã thanh toán", "Còn lại",
    "Trạng thái hóa đơn", "Số hóa đơn", "Ngày hóa đơn"
]

# === Tạo file nếu chưa có ===
if not os.path.exists(FILE_NAME):
    df = pd.DataFrame(columns=columns)
    df.to_excel(FILE_NAME, index=False)

def load_data():
    df = pd.read_excel(FILE_NAME)
    for col in columns:
        if col not in df.columns:
            if col in ["Giá trị", "Giá trị quyết toán", "Tổng đã thanh toán", "Còn lại"]:
                df[col] = 0.0
            else:
                df[col] = ""
    return df

def save_data(df):
    df.to_excel(FILE_NAME, index=False)

def load_info():
    if os.path.exists(INFO_FILE):
        df_info = pd.read_excel(INFO_FILE)
        if not df_info.empty:
            return df_info.iloc[0]
    return {
        "Tên doanh nghiệp": "",
        "Địa chỉ": "",
        "Logo": ""
    }

def save_info(data):
    df_info = pd.DataFrame([data])
    df_info.to_excel(INFO_FILE, index=False)

# === Giao diện chính ===
st.set_page_config(page_title="Quản lý hợp đồng", layout="wide")

# === Sidebar Thông tin doanh nghiệp ===
st.sidebar.header("🏢 Thông tin doanh nghiệp")
info = load_info()
ten_dn = st.sidebar.text_input("Tên doanh nghiệp", value=info.get("Tên doanh nghiệp", ""))
dia_chi = st.sidebar.text_input("Địa chỉ", value=info.get("Địa chỉ", ""))
logo_file = st.sidebar.file_uploader("Logo (nếu có)", type=["png", "jpg", "jpeg"])

if st.sidebar.button("💾 Lưu thông tin"):
    logo_path = info.get("Logo", "")
    if logo_file:
        logo_path = f"logo_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        with open(logo_path, "wb") as f:
            f.write(logo_file.read())
    save_info({"Tên doanh nghiệp": ten_dn, "Địa chỉ": dia_chi, "Logo": logo_path})
    st.sidebar.success("Đã lưu thông tin doanh nghiệp")

# === Header chính ===
st.title("📋 Theo dõi Hợp đồng & Đơn hàng")

info = load_info()
if info.get("Logo") and os.path.exists(info.get("Logo")):
    st.image(info.get("Logo"), width=100)
st.markdown(f"**{info.get('Tên doanh nghiệp', '')}**")
st.markdown(f"📍 {info.get('Địa chỉ', '')}")

# === Nhập hợp đồng mới ===
with st.expander("➕ Thêm hợp đồng mới"):
    col1, col2 = st.columns(2)

    with col1:
        ma_hd = st.text_input("Mã hợp đồng")
        khach_hang = st.text_input("Khách hàng")
        ngay_ky = st.date_input("Ngày ký")
        gia_tri = st.number_input("Giá trị hợp đồng", min_value=0.0)
        trang_thai = st.selectbox("Trạng thái", ["Đang xử lý", "Hoàn thành", "Hủy bỏ"])

    with col2:
        tt_thanh_toan = st.selectbox("Tình trạng thanh toán", ["Chưa thanh toán", "Một phần", "Đã thanh toán"])
        gia_tri_quyet_toan = st.number_input("Giá trị quyết toán", min_value=0.0)
        trang_thai_hd = st.selectbox("Trạng thái hóa đơn", ["Chưa xuất", "Đã xuất", "Trả lại"])

    so_hoa_don = ""
    ngay_hoa_don = ""
    if trang_thai_hd == "Đã xuất":
        col_a, col_b = st.columns(2)
        with col_a:
            so_hoa_don = st.text_input("Số hóa đơn")
        with col_b:
            ngay_hoa_don = st.date_input("Ngày hóa đơn")

    st.markdown("#### 📅 Nhập các đợt thanh toán:")
    payment_dates = st.text_area("Nhập các ngày thanh toán (phân cách bằng dấu phẩy)")
    payment_values = st.text_area("Nhập các giá trị tương ứng (phân cách bằng dấu phẩy)")

    if st.button("✅ Lưu hợp đồng"):
        if ma_hd == "" or khach_hang == "":
            st.warning("⚠️ Vui lòng nhập đầy đủ Mã hợp đồng và Khách hàng.")
        else:
            dates = [x.strip() for x in payment_dates.split(",") if x.strip()]
            try:
                values = [float(x.strip()) for x in payment_values.split(",") if x.strip()]
            except ValueError:
                st.error("⚠️ Giá trị thanh toán phải là số.")
                st.stop()

            if len(dates) != len(values):
                st.error("⚠️ Số lượng ngày và giá trị không khớp.")
            else:
                lich_su_thanh_toan = "; ".join([f"{d}: {v:,.0f}đ" for d, v in zip(dates, values)])
                tong_da_tt = sum(values)
                gia_tri_con_lai = max(gia_tri_quyet_toan - tong_da_tt, 0)

                df = load_data()
                new_data = {
                    "Mã hợp đồng": ma_hd,
                    "Khách hàng": khach_hang,
                    "Ngày ký": ngay_ky,
                    "Giá trị": gia_tri,
                    "Trạng thái": trang_thai,
                    "Tình trạng thanh toán": tt_thanh_toan,
                    "Giá trị quyết toán": gia_tri_quyet_toan,
                    "Lịch sử thanh toán": lich_su_thanh_toan,
                    "Tổng đã thanh toán": tong_da_tt,
                    "Còn lại": gia_tri_con_lai,
                    "Trạng thái hóa đơn": trang_thai_hd,
                    "Số hóa đơn": so_hoa_don,
                    "Ngày hóa đơn": ngay_hoa_don if trang_thai_hd == "Đã xuất" else ""
                }
                df = df.append(new_data, ignore_index=True)
                save_data(df)
                st.success("✅ Đã lưu hợp đồng mới!")

# === Dữ liệu và bộ lọc ===
df = load_data()

st.markdown("### 📑 Danh sách hợp đồng")
st.dataframe(df)

# === Lọc theo năm ===
st.markdown("### 📅 Lọc theo năm ký")
if not df.empty:
    df['Năm'] = pd.to_datetime(df['Ngày ký']).dt.year
    year_filter = st.selectbox("Chọn năm", ["Tất cả"] + sorted(df['Năm'].dropna().unique().tolist()))
    if year_filter != "Tất cả":
        df = df[df['Năm'] == year_filter]

# === Thống kê doanh thu ===
if not df.empty:
    df['Tháng'] = pd.to_datetime(df['Ngày ký']).dt.month
    df['Quý'] = pd.to_datetime(df['Ngày ký']).dt.quarter
    
    st.markdown("### 📊 Thống kê doanh thu")
    doanh_thu_thang = df.groupby('Tháng')['Giá trị quyết toán'].sum().reset_index()
    fig_thang = px.bar(doanh_thu_thang, x='Tháng', y='Giá trị quyết toán', title="Doanh thu theo tháng")
    st.plotly_chart(fig_thang, use_container_width=True)

    doanh_thu_quy = df.groupby('Quý')['Giá trị quyết toán'].sum().reset_index()
    fig_quy = px.pie(doanh_thu_quy, names='Quý', values='Giá trị quyết toán', title="Tỷ trọng doanh thu theo quý")
    st.plotly_chart(fig_quy, use_container_width=True)

# === Lọc trạng thái hóa đơn ===
st.markdown("### 📂 Lọc theo trạng thái hóa đơn")
hoa_don_filter = st.selectbox("Chọn trạng thái hóa đơn", ["Tất cả"] + df["Trạng thái hóa đơn"].unique().tolist())
filtered_df = df.copy()
if hoa_don_filter != "Tất cả":
    filtered_df = df[df["Trạng thái hóa đơn"] == hoa_don_filter]

# === Xuất dữ liệu ===
st.markdown("### 📤 Xuất dữ liệu")
col_all, col_kh, col_filter = st.columns(3)

with col_all:
    if st.button("📥 Tải toàn bộ danh sách"):
        excel_bytes = io.BytesIO()
        df.to_excel(excel_bytes, index=False)
        st.download_button("Tải tất cả hợp đồng", data=excel_bytes.getvalue(), file_name="toan_bo_hop_dong.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with col_kh:
    selected_kh = st.selectbox("Chọn khách hàng để xuất", ["-- Chọn --"] + sorted(df["Khách hàng"].dropna().unique().tolist()))
    if selected_kh != "-- Chọn --":
        kh_df = df[df["Khách hàng"] == selected_kh]
        excel_kh = io.BytesIO()
        kh_df.to_excel(excel_kh, index=False)
        st.download_button(f"📥 Tải hợp đồng của {selected_kh}", data=excel_kh.getvalue(), file_name=f"hop_dong_{selected_kh}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with col_filter:
    if st.button("📥 Tải danh sách đã lọc"):
        excel_bytes = io.BytesIO()
        filtered_df.to_excel(excel_bytes, index=False)
        st.download_button("Tải file Excel", data=excel_bytes.getvalue(), file_name="hop_dong_da_loc.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# === Cảnh báo chưa xuất hóa đơn ===
chua_xuat = df[df["Trạng thái hóa đơn"] == "Chưa xuất"]
if not chua_xuat.empty:
    st.warning(f"🚨 Có {len(chua_xuat)} hợp đồng chưa xuất hóa đơn!")
    with st.expander("📌 Danh sách chưa xuất hóa đơn"):
        st.dataframe(chua_xuat)
