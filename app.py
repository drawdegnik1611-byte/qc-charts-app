import streamlit as st
import pandas as pd
import docx # Thư viện đọc Word
import io
from charts.shewhart import calculate_capability, create_shewhart_chart
from charts.scatter import create_scatter_chart

st.set_page_config(page_title="Hệ thống Biểu đồ Chất lượng", layout="wide")

st.markdown("""
    
""", unsafe_allow_html=True)

# --- HÀM TRÍCH XUẤT BẢNG TỪ FILE WORD ---
def extract_tables_from_word(uploaded_file):
    doc = docx.Document(uploaded_file)
    tables_data = []
    for i, table in enumerate(doc.tables):
        data = [[cell.text.strip().replace('\n', ' ') for cell in row.cells] for row in table.rows]
        if len(data) > 1:
            raw_columns = data[0]
            
            # Tự động phát hiện và đổi tên nếu có cột trùng lặp
            new_cols = []
            col_counts = {}
            for col in raw_columns:
                col_name = col if col else "Cột_trống"
                if col_name in col_counts:
                    col_counts[col_name] += 1
                    new_cols.append(f"{col_name}_{col_counts[col_name]}")
                else:
                    col_counts[col_name] = 0
                    new_cols.append(col_name)
                    
            df = pd.DataFrame(data[1:], columns=new_cols)
            tables_data.append((f"Bảng {i+1} trong Word", df))
    return tables_data

# Khởi tạo session state
if 'metrics_list' not in st.session_state:
    st.session_state.metrics_list = []

# --- MENU CHÍNH THANH BÊN TRÁI ---
with st.sidebar:
    st.title("⚙️ BỘ CÔNG CỤ")
    tool_mode = st.radio("Chọn loại biểu đồ:", ["📉 Biểu đồ Shewhart (I-MR)", "📈 Biểu đồ Phân tán (Scatter)"])
    st.markdown("---")
    pl_num = st.text_input("Số lô / Phụ lục:", value="147001")

st.title(f"📊 {tool_mode}")
st.markdown("---")

# ==========================================
# GIAO DIỆN 1: BIỂU ĐỒ SHEWHART (Giữ nguyên)
# ==========================================
if tool_mode == "📉 Biểu đồ Shewhart (I-MR)":
    with st.sidebar:
        st.header("📥 Nhập Liệu Shewhart")
        name = st.selectbox("Tên chỉ tiêu:", ["Tỷ trọng", "Độ cứng", "Độ mài mòn", "Khác..."])
        if name == "Khác...": name = st.text_input("Nhập tên chỉ tiêu:")
            
        col1, col2 = st.columns(2)
        lsl_input = col1.text_input("LSL (Dưới):")
        usl_input = col2.text_input("USL (Trên):")
        data_input = st.text_area("Dữ liệu (Copy dán):", height=120)
        
        st.write("")
        if st.button("➕ THÊM CHỈ TIÊU", type="primary", use_container_width=True):
            parts = data_input.replace(",", ".").split()
            data = [float(p) for p in parts if p.replace('.','',1).replace('-','',1).isdigit()]
            if not name or len(data) < 2:
                st.error("⚠️ Vui lòng nhập Tên chỉ tiêu và ít nhất 2 số liệu.")
            else:
                lsl = float(lsl_input.replace(",", ".")) if lsl_input else None
                usl = float(usl_input.replace(",", ".")) if usl_input else None
                cap = calculate_capability(data, lsl, usl)
                st.session_state.metrics_list.append({"name": name, "data": data, "cap": cap})
                st.success(f"✅ Đã thêm: {name}")
                    
        if st.button("🗑️ Xóa Danh Sách", use_container_width=True):
            st.session_state.metrics_list.clear()
            st.rerun()

    if st.session_state.metrics_list:
        fig = create_shewhart_chart(st.session_state.metrics_list, pl_num)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        st.write("")
        col_empty1, col_btn, col_empty2 = st.columns([1, 2, 1])
        with col_btn:
            try:
                img_bytes = fig.to_image(format="png", width=1100, height=500 * len(st.session_state.metrics_list), scale=2)
                st.download_button("📥 TẢI BIỂU ĐỒ (PNG)", data=img_bytes, file_name=f"Shewhart-{pl_num}.png", mime="image/png", use_container_width=True, type="primary")
            except: pass

# ==========================================
# GIAO DIỆN 2: BIỂU ĐỒ PHÂN TÁN (MỚI)
# ==========================================
elif tool_mode == "📈 Biểu đồ Phân tán (Scatter)":
    st.info("💡 Bạn có thể tải lên file Word (.docx), Excel (.xlsx) hoặc CSV. Hệ thống sẽ tự động tìm bảng dữ liệu bên trong.")
    
    # Nút Upload File
    uploaded_file = st.file_uploader("Tải file dữ liệu lên", type=["docx", "xlsx", "csv"])
    
    if uploaded_file is not None:
        file_ext = uploaded_file.name.split('.')[-1]
        df_list = []
        
        # Xử lý các loại file khác nhau
        try:
            if file_ext == 'docx':
                df_list = extract_tables_from_word(uploaded_file)
            elif file_ext == 'xlsx':
                excel_file = pd.ExcelFile(uploaded_file)
                for sheet in excel_file.sheet_names:
                    df_list.append((f"Sheet: {sheet}", excel_file.parse(sheet).astype(str)))
            elif file_ext == 'csv':
                df_list.append(("Dữ liệu CSV", pd.read_csv(uploaded_file).astype(str)))
        except Exception as e:
            st.error(f"Lỗi đọc file: {e}")
            
        if not df_list:
            st.warning("⚠️ Không tìm thấy bảng dữ liệu nào trong file này.")
        else:
            # Nếu file Word có nhiều bảng, cho người dùng chọn bảng
            table_names = [item[0] for item in df_list]
            selected_table_name = st.selectbox("Chọn bảng chứa dữ liệu:", table_names)
            
            # Lấy DataFrame tương ứng với bảng được chọn
            df = next(item[1] for item in df_list if item[0] == selected_table_name)
            
            st.write("👀 **Kiểm tra & Chỉnh sửa Dữ liệu:**")
            st.caption("💡 Bạn có thể click đúp vào ô để sửa số, hoặc chọn các dòng thừa (chứa chữ/tiêu đề) và bấm phím Delete/Backspace để xóa.")
            
            # Vũ khí 1: Hiển thị bảng tương tác (cho phép thêm/sửa/xóa trực tiếp)
            edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, height=250)
            
            # Chọn cột X và Y từ bảng đã chỉnh sửa
            col1, col2 = st.columns(2)
            with col1:
                x_col = st.selectbox("Chọn cột cho Trục X (Hoành):", edited_df.columns)
            with col2:
                y_col = st.selectbox("Chọn cột cho Trục Y (Tung):", [c for c in edited_df.columns if c != x_col])
                
            if st.button("🚀 VẼ BIỂU ĐỒ PHÂN TÁN", type="primary"):
                try:
                    # Vũ khí 2: Ép kiểu dữ liệu cực mạnh. Cứ thấy chữ là biến thành NaN (Not a Number)
                    x_raw = edited_df[x_col].astype(str).str.replace(',', '.')
                    y_raw = edited_df[y_col].astype(str).str.replace(',', '.')
                    
                    x_clean = pd.to_numeric(x_raw, errors='coerce')
                    y_clean = pd.to_numeric(y_raw, errors='coerce')
                    
                    # Gom 2 cột lại và dropna() để lọc vứt bỏ các dòng NaN (các dòng ban đầu là chữ)
                    temp_df = pd.DataFrame({'x': x_clean, 'y': y_clean}).dropna()
                    
                    if temp_df.empty or len(temp_df) < 2:
                        st.error("⚠️ Sau khi làm sạch, không còn đủ dữ liệu số để vẽ. Vui lòng kiểm tra lại cột đã chọn.")
                    else:
                        x_data = temp_df['x'].tolist()
                        y_data = temp_df['y'].tolist()
                        
                        # Gọi hàm vẽ
                        fig_scatter = create_scatter_chart(x_data, y_data, x_col, y_col, pl_num)
                        st.plotly_chart(fig_scatter, use_container_width=True, config={'displayModeBar': False})
                        
                        # Nút Tải ảnh (Giữ nguyên)
                        st.write("")
                        col_empty1, col_btn, col_empty2 = st.columns([1, 2, 1])
                        with col_btn:
                            img_bytes = fig_scatter.to_image(format="png", width=1100, height=600, scale=2)
                            st.download_button("📥 TẢI BIỂU ĐỒ VỀ (PNG)", data=img_bytes, file_name=f"Scatter-{pl_num}.png", mime="image/png", use_container_width=True, type="primary")
                except Exception as e:
                    st.error(f"⚠️ Đã có lỗi xảy ra: {e}")