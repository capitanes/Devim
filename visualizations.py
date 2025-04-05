import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_delinquency_trend_chart(df):
    """
    Создает график, показывающий тренды просрочек платежей во времени.
    
    Args:
        df: DataFrame, содержащий метрики просрочек
    
    Returns:
        Объект графика Plotly
    """
    # Группировка по дате плана и расчет средней просрочки в днях
    trend_df = df.groupby(df['plan_at'].dt.to_period('M').astype(str)).agg({
        'days_late': 'mean',
        'is_delinquent': 'mean',
        'order_id': 'count'
    }).reset_index()
    
    trend_df.rename(columns={
        'is_delinquent': 'delinquency_rate',
        'order_id': 'payment_count'
    }, inplace=True)
    
    trend_df['delinquency_rate'] = trend_df['delinquency_rate'] * 100
    
    # Создание подграфиков с общей осью X
    fig = make_subplots(
        rows=2, 
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=("Средняя просрочка платежей по месяцам (в днях)", "Процент просроченных платежей по месяцам (%)")
    )
    
    # Добавление столбчатой диаграммы для средней просрочки в днях
    fig.add_trace(
        go.Bar(
            x=trend_df['plan_at'],
            y=trend_df['days_late'],
            name='Средняя просрочка (дни)',
            marker_color='#E74C3C'
        ),
        row=1, col=1
    )
    
    # Добавление линейного графика для процента просроченных платежей
    fig.add_trace(
        go.Scatter(
            x=trend_df['plan_at'],
            y=trend_df['delinquency_rate'],
            name='Процент просрочек (%)',
            mode='lines+markers',
            line=dict(color='#2C3E50', width=2),
            marker=dict(size=8)
        ),
        row=2, col=1
    )
    
    # Обновление макета
    fig.update_layout(
        height=600,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis2_title="Месяц",
        yaxis_title="Средняя просрочка (дни)",
        yaxis2_title="Процент просрочек (%)",
        title={
            'text': "Анализ тенденций просрочек платежей",
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        annotations=[
            dict(
                text="<i>График показывает динамику просрочек платежей во времени. Верхняя часть отображает среднее количество дней просрочки по месяцам, нижняя - процент платежей с просрочкой. Данные агрегированы по месяцам на основе запланированной даты платежа.</i>",
                showarrow=False,
                xref="paper",
                yref="paper",
                x=0.5,
                y=-0.15,
                font=dict(size=14),
                xanchor='center',
                yanchor='bottom'
            )
        ]
    )
    
    return fig

def create_payment_comparison_chart(df):
    """
    Создает график, сравнивающий запланированные и фактические платежи.
    
    Args:
        df: DataFrame, содержащий данные о платежах
    
    Returns:
        Объект графика Plotly
    """
    # Группировка по дате плана и агрегация сумм платежей
    payment_comp_df = df.groupby(df['plan_at'].dt.to_period('M').astype(str)).agg({
        'plan_sum_total': 'sum',
        'paid_sum': 'sum'
    }).reset_index()
    
    # Расчет процента запланированных платежей, которые были фактически оплачены
    payment_comp_df['payment_rate'] = payment_comp_df['paid_sum'] / payment_comp_df['plan_sum_total'] * 100
    
    # Создание подграфиков
    fig = make_subplots(
        rows=2, 
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=("Сравнение запланированных и фактических сумм платежей", "Процент выполнения платежей (%)")
    )
    
    # Добавление столбчатой диаграммы для запланированных и фактических сумм платежей
    fig.add_trace(
        go.Bar(
            x=payment_comp_df['plan_at'],
            y=payment_comp_df['plan_sum_total'],
            name='Запланированные платежи',
            marker_color='#2C3E50'
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=payment_comp_df['plan_at'],
            y=payment_comp_df['paid_sum'],
            name='Фактические платежи',
            marker_color='#27AE60'
        ),
        row=1, col=1
    )
    
    # Добавление линейного графика для процента выполнения платежей
    fig.add_trace(
        go.Scatter(
            x=payment_comp_df['plan_at'],
            y=payment_comp_df['payment_rate'],
            name='Процент выполнения (%)',
            mode='lines+markers',
            line=dict(color='#E74C3C', width=2),
            marker=dict(size=8)
        ),
        row=2, col=1
    )
    
    # Добавление референсной линии 100%
    fig.add_trace(
        go.Scatter(
            x=payment_comp_df['plan_at'],
            y=[100] * len(payment_comp_df),
            name='Целевые 100%',
            mode='lines',
            line=dict(color='rgba(0,0,0,0.3)', width=1, dash='dash')
        ),
        row=2, col=1
    )
    
    # Обновление макета
    fig.update_layout(
        height=600,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis2_title="Месяц",
        yaxis_title="Сумма платежей",
        yaxis2_title="Процент выполнения (%)",
        barmode='group',
        title={
            'text': "Сравнение запланированных и фактических платежей",
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        annotations=[
            dict(
                text="<i>График сравнивает запланированные и фактические суммы платежей по месяцам. Верхняя часть показывает абсолютные суммы, нижняя - процент выполнения платежей (отношение фактически оплаченной суммы к запланированной). Пунктирная линия обозначает целевой уровень 100%.</i>",
                showarrow=False,
                xref="paper",
                yref="paper",
                x=0.5,
                y=-0.15,
                font=dict(size=12)
            )
        ]
    )
    
    return fig

def create_payment_behavior_chart(df):
    """
    Создает график, показывающий модели поведения плательщиков.
    
    Args:
        df: DataFrame, содержащий данные о платежах
    
    Returns:
        Объект графика Plotly
    """
    # Расчет распределения статусов платежей по месяцам
    behavior_df = df.copy()
    behavior_df['month'] = behavior_df['plan_at'].dt.to_period('M').astype(str)
    
    # Сводная таблица для получения количества платежей по статусам и месяцам
    behavior_pivot = pd.pivot_table(
        behavior_df,
        values='order_id',
        index='month',
        columns='payment_status',
        aggfunc='count',
        fill_value=0,
        observed=True  # Добавлено observed=True для устранения FutureWarning
    ).reset_index()
    
    # Расчет общего количества платежей в месяц для процентного расчета
    behavior_pivot['total'] = behavior_pivot.iloc[:, 1:].sum(axis=1)
    
    # Преобразование в проценты
    for col in behavior_pivot.columns:
        if col not in ['month', 'total']:
            behavior_pivot[f'{col}_pct'] = behavior_pivot[col] / behavior_pivot['total'] * 100
    
    # Создание графика
    fig = make_subplots(
        rows=2, 
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=("Распределение статусов платежей (количество)", "Распределение статусов платежей (%)")
    )
    
    # Определение цветов для статусов платежей
    status_colors = {
        'Early': '#27AE60',
        'On Time': '#2C3E50',
        'Slightly Late (1-7 days)': '#F39C12',
        'Late (8-30 days)': '#E67E22',
        'Very Late (31-60 days)': '#D35400',
        'Extremely Late (60+ days)': '#E74C3C',
        'Досрочно': '#27AE60',
        'Вовремя': '#2C3E50',
        'Немного просрочено (1-7 дней)': '#F39C12',
        'Просрочено (8-30 дней)': '#E67E22',
        'Сильно просрочено (31-60 дней)': '#D35400',
        'Критически просрочено (60+ дней)': '#E74C3C'
    }
    
    # Добавление столбчатой диаграммы для количества
    for status in behavior_pivot.columns:
        if status not in ['month', 'total'] and not status.endswith('_pct'):
            # Перевод статусов на русский язык для отображения
            status_ru = status
            if status == 'Early':
                status_ru = 'Досрочно'
            elif status == 'On Time':
                status_ru = 'Вовремя'
            elif status == 'Slightly Late (1-7 days)':
                status_ru = 'Немного просрочено (1-7 дней)'
            elif status == 'Late (8-30 days)':
                status_ru = 'Просрочено (8-30 дней)'
            elif status == 'Very Late (31-60 days)':
                status_ru = 'Сильно просрочено (31-60 дней)'
            elif status == 'Extremely Late (60+ days)':
                status_ru = 'Критически просрочено (60+ дней)'
                
            fig.add_trace(
                go.Bar(
                    x=behavior_pivot['month'],
                    y=behavior_pivot[status],
                    name=status_ru,
                    marker_color=status_colors.get(status, '#000000')
                ),
                row=1, col=1
            )
    
    # Добавление столбчатой диаграммы для процентов
    for status in behavior_pivot.columns:
        if status.endswith('_pct'):
            status_name = status.replace('_pct', '')
            if status_name not in ['month', 'total']:
                # Перевод статусов на русский язык для отображения
                status_ru = status_name
                if status_name == 'Early':
                    status_ru = 'Досрочно'
                elif status_name == 'On Time':
                    status_ru = 'Вовремя'
                elif status_name == 'Slightly Late (1-7 days)':
                    status_ru = 'Немного просрочено (1-7 дней)'
                elif status_name == 'Late (8-30 days)':
                    status_ru = 'Просрочено (8-30 дней)'
                elif status_name == 'Very Late (31-60 days)':
                    status_ru = 'Сильно просрочено (31-60 дней)'
                elif status_name == 'Extremely Late (60+ days)':
                    status_ru = 'Критически просрочено (60+ дней)'
                
                fig.add_trace(
                    go.Bar(
                        x=behavior_pivot['month'],
                        y=behavior_pivot[status],
                        name=f"{status_ru} (%)",
                        marker_color=status_colors.get(status_name, '#000000'),
                        showlegend=False
                    ),
                    row=2, col=1
                )
    
    # Обновление макета
    fig.update_layout(
        height=700,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis2_title="Месяц",
        yaxis_title="Количество платежей",
        yaxis2_title="Процент (%)",
        barmode='stack',
        title={
            'text': "Анализ поведения плательщиков",
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        annotations=[
            dict(
                text="<i>График показывает распределение платежей по статусам своевременности. Верхняя часть отображает абсолютное количество платежей каждого статуса по месяцам, нижняя - процентное соотношение. Статусы варьируются от досрочных платежей до критически просроченных (более 60 дней).</i>",
                showarrow=False,
                xref="paper",
                yref="paper",
                x=0.5,
                y=-0.15,
                font=dict(size=12)
            )
        ]
    )
    
    return fig

def create_delinquency_heatmap(df):
    """
    Создает тепловую карту, показывающую закономерности просрочек.
    
    Args:
        df: DataFrame, содержащий метрики просрочек
    
    Returns:
        Объект графика Plotly
    """
    # Создание копии датафрейма
    heatmap_df = df.copy()
    
    # Извлечение месяца и года из даты плана
    heatmap_df['month'] = heatmap_df['plan_at'].dt.month
    heatmap_df['year'] = heatmap_df['plan_at'].dt.year
    
    # Группировка по месяцу и диапазону суммы займа
    # Создание диапазонов сумм займа вручную вместо использования pd.cut
    # Определение границ и меток диапазонов
    bin_edges = [0, 1000, 2000, 5000, 10000, float('inf')]
    bin_labels = ['0-1 тыс.', '1-2 тыс.', '2-5 тыс.', '5-10 тыс.', '10+ тыс.']
    
    # Функция для присвоения каждому займу соответствующего диапазона
    def get_loan_range(loan_amount):
        for i in range(len(bin_edges) - 1):
            if bin_edges[i] <= loan_amount < bin_edges[i + 1]:
                return bin_labels[i]
        return bin_labels[-1]  # Для максимального значения
    
    # Применение функции для создания диапазонов сумм займа
    heatmap_df['loan_amount_range'] = heatmap_df['issued_sum'].apply(get_loan_range)

    heatmap_df['loan_amount_range'] = pd.Categorical(
    heatmap_df['loan_amount_range'],
    categories=['0-1 тыс.', '1-2 тыс.', '2-5 тыс.', '5-10 тыс.', '10+ тыс.'],
    ordered=True
    )
    
    # Создание сводной таблицы для тепловой карты
    heatmap_pivot = pd.pivot_table(
        heatmap_df,
        values='days_late',
        index='loan_amount_range',
        columns=['year', 'month'],
        aggfunc='mean',
        fill_value=100,
        observed=True  # Добавлено observed=True для устранения FutureWarning
    )
    
    # Преобразование мульти-индекса столбцов
    heatmap_pivot.columns = [f"{year}-{month:02d}" for year, month in heatmap_pivot.columns]
    
    # Сброс индекса для подготовки к построению графика
    heatmap_pivot = heatmap_pivot.reset_index()
    
    # Преобразование датафрейма для построения тепловой карты
    heatmap_melted = pd.melt(
        heatmap_pivot,
        id_vars='loan_amount_range',
        var_name='period',
        value_name='avg_days_late'
    )
    
    # Создание тепловой карты
    fig = px.density_heatmap(
        heatmap_melted,
        x='period',
        y='loan_amount_range',
        z='avg_days_late',
        title='Средняя просрочка платежей по сумме займа и месяцу',
        labels={
            'period': 'Период',
            'loan_amount_range': 'Диапазон суммы займа',
            'avg_days_late': 'Средняя просрочка (дни)'
        },
        color_continuous_scale=px.colors.sequential.Reds
    )
    
    # Обновление макета
    fig.update_layout(
        height=500,
        xaxis_title="Период (Год-Месяц)",
        yaxis_title="Диапазон суммы займа",
        coloraxis_colorbar=dict(title="Средняя просрочка (дни)"),
        title={
            'text': "Тепловая карта просрочек по сумме займа",
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        annotations=[
            dict(
                text="<i>Тепловая карта показывает среднюю продолжительность просрочки (в днях) в зависимости от суммы займа и периода. Более темные цвета соответствуют более длительным просрочкам. Данные агрегированы по месяцам и диапазонам сумм займов.</i>",
                showarrow=False,
                xref="paper",
                yref="paper",
                x=0.5,
                y=-0.15,
                font=dict(size=12)
            )
        ]
    )
    
    return fig
