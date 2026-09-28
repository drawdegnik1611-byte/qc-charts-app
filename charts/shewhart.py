import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def calculate_imr_limits(data):
    x_bar = np.mean(data)
    mr = [abs(data[i] - data[i-1]) for i in range(1, len(data))]
    mr_bar = np.mean(mr) if len(mr) > 0 else 0
    ucl = x_bar + 2.66 * mr_bar
    lcl = x_bar - 2.66 * mr_bar
    return x_bar, ucl, lcl

def calculate_capability(data, lsl=None, usl=None):
    x_bar = np.mean(data)
    s = np.std(data, ddof=1)
    mr = [abs(data[i] - data[i-1]) for i in range(1, len(data))]
    mr_bar = np.mean(mr) if len(mr) > 0 else 0
    sigma_within = mr_bar / 1.128 if mr_bar != 0 else 0.0001
    
    # --- TÍNH Pp, Ppk ---
    ppu = (usl - x_bar) / (3 * s) if usl is not None else float('inf')
    ppl = (x_bar - lsl) / (3 * s) if lsl is not None else float('inf')
    pp = (usl - lsl) / (6 * s) if (usl is not None and lsl is not None) else None
    ppk = min(ppu, ppl)
    
    # --- TÍNH Cp, Cpk (Đây là 4 dòng bị thiếu) ---
    cpu = (usl - x_bar) / (3 * sigma_within) if usl is not None else float('inf')
    cpl = (x_bar - lsl) / (3 * sigma_within) if lsl is not None else float('inf')
    cp = (usl - lsl) / (6 * sigma_within) if (usl is not None and lsl is not None) else None
    cpk = min(cpu, cpl)
    
    # Làm tròn số hoặc hiển thị N/A nếu không có giới hạn
    if cpk == float('inf'): cpk = "N/A"
    else: cpk = round(cpk, 2)
    
    if ppk == float('inf'): ppk = "N/A"
    else: ppk = round(ppk, 2)
    
    return {
        "Mean": round(x_bar, 3),
        "Cp": round(cp, 2) if cp is not None else "N/A",
        "Cpk": cpk,
        "Pp": round(pp, 2) if pp is not None else "N/A",
        "Ppk": ppk
    }

def create_shewhart_chart(metrics_list, pl_num):
    num_subplots = len(metrics_list)
    subplot_titles = [m['name'] for m in metrics_list]
    
    fig = make_subplots(rows=num_subplots, cols=1, shared_xaxes=False,
                        subplot_titles=subplot_titles, vertical_spacing=0.25)
                        
    for idx, item in enumerate(metrics_list):
        row = idx + 1
        data = item['data']
        cap = item['cap']
        
        x_axis = [f"Mẫu {j+1}" for j in range(len(data))]
        cl, ucl, lcl = calculate_imr_limits(data)
        
        # Vẽ các đường nét y hệt ảnh mẫu
        fig.add_trace(go.Scatter(x=x_axis, y=data, mode='lines+markers', name='Thực tế', line=dict(color='blue', width=2), marker=dict(size=8)), row=row, col=1)
        fig.add_trace(go.Scatter(x=x_axis, y=[cl]*len(data), mode='lines', name='CL', line=dict(color='green', dash='dash', width=2)), row=row, col=1)
        fig.add_trace(go.Scatter(x=x_axis, y=[ucl]*len(data), mode='lines', name='UCL', line=dict(color='red', dash='dash', width=2)), row=row, col=1)
        fig.add_trace(go.Scatter(x=x_axis, y=[lcl]*len(data), mode='lines', name='LCL', line=dict(color='red', dash='dash', width=2)), row=row, col=1)

        # Chèn Text thông số ngay bên dưới trục X
        stats_text = f"Mean (Trung bình): {cap['Mean']}   |   Cp: {cap['Cp']}   |   Cpk: {cap['Cpk']}   |   Pp: {cap['Pp']}   |   Ppk: {cap['Ppk']}"
        
        fig.add_annotation(
            xref=f"x{row} domain" if row > 1 else "x domain", 
            yref=f"y{row} domain" if row > 1 else "y domain",
            x=0.5, y=-0.25,  # Tọa độ âm giúp chữ nhảy xuống dưới gầm biểu đồ
            text=stats_text, 
            showarrow=False, 
            font=dict(size=16, color="black"),
            xanchor='center',
            yanchor='top'
        )

    # Tinh chỉnh Theme giống ảnh: Phông nền xanh nhạt, lưới trắng, font chữ Arial
    title_text = f"Biểu đồ Kiểm soát Shewhart (I-MR) - Phụ Lục PL-{pl_num}"
    fig.update_layout(
        title=dict(text=title_text, font=dict(size=22, color="#2C3E50"), x=0.5, xanchor='center'),
        height=450 * num_subplots, 
        showlegend=False, 
        margin=dict(t=80, b=100, l=50, r=50),
        plot_bgcolor='#EAF0F8', # Nền xanh xám nhạt như ảnh
        paper_bgcolor='white',  # Nền ngoài trắng
        font=dict(color='#2C3E50', family="Arial")
    )
    
    # Cấu hình đường lưới màu trắng y như ảnh mẫu
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='white', tickfont=dict(size=14))
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='white', tickfont=dict(size=14))

    return fig