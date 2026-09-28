import plotly.graph_objects as go
import numpy as np
import pandas as pd

def create_scatter_chart(x_data, y_data, x_name, y_name, pl_num):
    fig = go.Figure()

    # Vẽ các điểm phân tán (Scatter)
    fig.add_trace(go.Scatter(
        x=x_data, 
        y=y_data, 
        mode='markers', 
        name='Dữ liệu thực tế',
        marker=dict(size=10, color='#3498DB', line=dict(width=1, color='DarkSlateGrey'))
    ))

    # Tính toán đường xu hướng (Linear Regression)
    if len(x_data) > 1:
        # Tính phương trình y = mx + b
        m, b = np.polyfit(x_data, y_data, 1)
        trendline = m * np.array(x_data) + b
        
        # Tính hệ số R bình phương (R-squared)
        correlation_matrix = np.corrcoef(x_data, y_data)
        correlation_xy = correlation_matrix[0,1]
        r_squared = correlation_xy**2
        
        # Vẽ đường xu hướng nét đứt màu đỏ
        fig.add_trace(go.Scatter(
            x=x_data, 
            y=trendline, 
            mode='lines', 
            name='Đường xu hướng',
            line=dict(color='red', dash='dash', width=2)
        ))
        
        stats_text = f"Phương trình: y = {m:.4f}x + {b:.4f}   |   Hệ số tương quan (R²): {r_squared:.4f}"
        
        # Thêm text thông số xuống dưới cùng
        fig.add_annotation(
            xref="paper", yref="paper",
            x=0.5, y=-0.2, 
            text=stats_text, 
            showarrow=False, 
            font=dict(size=15, color="black"),
            xanchor='center', yanchor='top'
        )

    # Căn chỉnh giao diện Theme Sáng chuyên nghiệp
    title_text = f"Biểu đồ Phân tán (Scatter Plot) - Phụ Lục PL-{pl_num}"
    fig.update_layout(
        title=dict(text=title_text, font=dict(size=22, color="#2C3E50"), x=0.5, xanchor='center'),
        xaxis_title=dict(text=x_name, font=dict(size=14, color='black')),
        yaxis_title=dict(text=y_name, font=dict(size=14, color='black')),
        height=550, 
        margin=dict(t=80, b=100, l=60, r=50),
        plot_bgcolor='#EAF0F8', 
        paper_bgcolor='white',
        font=dict(color='#2C3E50', family="Arial"),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='white')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='white')

    return fig