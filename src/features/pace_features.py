"""
ペース展開関連特徴量モジュール
"""
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

def calculate_pace_disadvantage(race_df, result_df):
    """
    前走ペース偏差（展開不利指標）を計算する関数
    
    各馬の前走の展開が不利だったかどうかを判断し、「展開負けで実力負けではない」馬を見出す特徴量
    
    Args:
        race_df (DataFrame): レース基本情報のDataFrame
        result_df (DataFrame): レース結果のDataFrame
    
    Returns:
        DataFrame: 前走ペース偏差のDataFrame
    """
    try:
        # レースIDの作成
        race_df['race_id'] = race_df['kaisai_nen'] + race_df['kaisai_tsukihi'] + race_df['keibajo_code'] + race_df['race_bango']
        result_df['race_id'] = result_df['kaisai_nen'] + result_df['kaisai_tsukihi'] + result_df['keibajo_code'] + result_df['race_bango']
        
        # データ結合
        df = pd.merge(result_df, race_df, on='race_id', suffixes=('', '_race'))
        
        # レース日付の作成
        df['race_date'] = pd.to_datetime(df['kaisai_nen'] + df['kaisai_tsukihi'], format='%Y%m%d')
        
        # 脚質の判定
        df['corner_01_tsuka_juni'] = pd.to_numeric(df['corner_01_tsuka_juni'], errors='coerce')
        df['corner_04_tsuka_juni'] = pd.to_numeric(df['corner_04_tsuka_juni'], errors='coerce')
        df['kakutei_chakujun'] = pd.to_numeric(df['kakutei_chakujun'], errors='coerce')
        
        # 先行率: (4コーナー通過順 - 最終着順) / 出走頭数
        df['shusso_tosu'] = pd.to_numeric(df['shusso_tosu'], errors='coerce')
        df['up_rate'] = (df['corner_04_tsuka_juni'] - df['kakutei_chakujun']) / df['shusso_tosu']
        
        # 脚質の判定
        conditions = [
            (df['corner_01_tsuka_juni'] <= 3),  # 第1コーナーで上位3番手以内なら逃げ・先行
            (df['corner_01_tsuka_juni'] > 3) & (df['up_rate'] > 0.2),  # 後方から上がってきたら差し
            (df['corner_01_tsuka_juni'] > 3) & (df['up_rate'] <= 0.2)  # それ以外なら追込
        ]
        choices = ['先行', '差し', '追込']
        df['running_style'] = np.select(conditions, choices, default='不明')
        
        # レースごとのペース判定
        # 先行馬の着順平均を計算し、先行有利（スロー）かハイペースかを判定
        race_pace = df.groupby('race_id').apply(
            lambda x: pd.Series({
                'lead_horse_count': sum(x['running_style'] == '先行'),
                'lead_horse_avg_rank': x.loc[x['running_style'] == '先行', 'kakutei_chakujun'].mean(),
                'closing_horse_count': sum(x['running_style'] == '差し'),
                'closing_horse_avg_rank': x.loc[x['running_style'] == '差し', 'kakutei_chakujun'].mean(),
                'race_date': x['race_date'].iloc[0],  # レース日付
                'shusso_tosu': x['shusso_tosu'].iloc[0]  # 出走頭数
            })
        ).reset_index()
        
        # ペース判定
        conditions = [
            (race_pace['lead_horse_avg_rank'] < race_pace['shusso_tosu'] / 2),  # 先行馬の平均着順が出走頭数の半分より良い
            (race_pace['lead_horse_avg_rank'] >= race_pace['shusso_tosu'] / 2)  # 先行馬の平均着順が出走頭数の半分以上
        ]
        choices = ['スロー', 'ハイ']
        race_pace['pace_type'] = np.select(conditions, choices, default='不明')
        
        # 脚質とペースの相性判定
        race_pace = race_pace[['race_id', 'pace_type']]
        df = pd.merge(df, race_pace, on='race_id')
        
        # 展開適性の判定
        conditions = [
            (df['running_style'] == '先行') & (df['pace_type'] == 'スロー'),
            (df['running_style'] == '差し') & (df['pace_type'] == 'ハイ'),
            (df['running_style'] == '先行') & (df['pace_type'] == 'ハイ'),
            (df['running_style'] == '差し') & (df['pace_type'] == 'スロー')
        ]
        choices = ['有利', '有利', '不利', '不利']
        df['pace_advantage'] = np.select(conditions, choices, default='中立')
        
        # 前走情報を取得
        # 各馬ごとにレース日付でソートし、前走の情報を取得
        horse_df = df.sort_values(['ketto_toroku_bango', 'race_date'])
        
        # 前走の展開と着順
        horse_df['prev_pace_advantage'] = horse_df.groupby('ketto_toroku_bango')['pace_advantage'].shift(1)
        horse_df['prev_finish_pos'] = horse_df.groupby('ketto_toroku_bango')['kakutei_chakujun'].shift(1)
        
        # 前走結果の区分
        conditions = [
            (horse_df['prev_finish_pos'] <= 3),
            (horse_df['prev_finish_pos'] <= 5),
            (horse_df['prev_finish_pos'] > 5)
        ]
        choices = ['好走', '凡走', '大敗']
        horse_df['prev_performance'] = np.select(conditions, choices, default='不明')
        
        # 展開不利と着順の組み合わせ
        conditions = [
            (horse_df['prev_pace_advantage'] == '不利') & (horse_df['prev_performance'] == '大敗'),
            (horse_df['prev_pace_advantage'] == '不利') & (horse_df['prev_performance'] == '凡走'),
            (horse_df['prev_pace_advantage'] == '不利') & (horse_df['prev_performance'] == '好走'),
            (horse_df['prev_pace_advantage'] == '有利') & (horse_df['prev_performance'] == '大敗'),
            (horse_df['prev_pace_advantage'] == '有利') & (horse_df['prev_performance'] == '好走')
        ]
        choices = ['展開不利→大敗', '展開不利→凡走', '展開不利→好走', '展開有利→大敗', '展開有利→好走']
        horse_df['prev_pattern'] = np.select(conditions, choices, default='中立')
        
        # 結果を整形
        result = horse_df[
            ['ketto_toroku_bango', 'bamei', 'race_id', 'race_date', 
             'running_style', 'pace_type', 'pace_advantage', 
             'prev_pace_advantage', 'prev_performance', 'prev_pattern']
        ].copy()
        
        return result.dropna(subset=['prev_pattern'])  # 前走情報がある馬のみを返す
    
    except Exception as e:
        logger.error(f"前走ペース偏差の計算中にエラーが発生しました: {e}")
        return pd.DataFrame()

def calculate_pace_disadvantage_scores(pace_df):
    """
    前走ペース偏差データから各パターンのスコアを計算する関数
    
    各パターン（展開不利→大敗など）の次走での回収率やパフォーマンスを集計
    
    Args:
        pace_df (DataFrame): 前走ペース偏差のDataFrame
    
    Returns:
        DataFrame: パターン別のスコアデータ
    """
    try:
        # 必要なカラムがあるか確認
        required_columns = ['ketto_toroku_bango', 'prev_pattern', 'kakutei_chakujun', 'tansho_odds', 'tansho_ninkijun']
        missing_columns = [col for col in required_columns if col not in pace_df.columns]
        
        if missing_columns:
            logger.error(f"必要なカラムがありません: {missing_columns}")
            return pd.DataFrame()
        
        # 数値型への変換
        pace_df['kakutei_chakujun'] = pd.to_numeric(pace_df['kakutei_chakujun'], errors='coerce')
        pace_df['tansho_odds'] = pd.to_numeric(pace_df['tansho_odds'], errors='coerce') / 10
        pace_df['tansho_ninkijun'] = pd.to_numeric(pace_df['tansho_ninkijun'], errors='coerce')
        
        # 勝利フラグ
        pace_df['win'] = (pace_df['kakutei_chakujun'] == 1).astype(int)
        pace_df['top3'] = (pace_df['kakutei_chakujun'] <= 3).astype(int)
        
        # 人気以上の成績（着順 < 人気順）
        pace_df['over_popularity'] = (pace_df['kakutei_chakujun'] < pace_df['tansho_ninkijun']).astype(int)
        
        # パターン別の集計
        pattern_stats = pace_df.groupby('prev_pattern').agg(
            race_count=('race_id', 'count'),
            win_count=('win', 'sum'),
            top3_count=('top3', 'sum'),
            over_popularity_count=('over_popularity', 'sum'),
            win_odds_sum=('tansho_odds', lambda x: pace_df.loc[pace_df['win'] == 1, 'tansho_odds'].sum()),
            avg_popularity=('tansho_ninkijun', 'mean')
        ).reset_index()
        
        # 各種率の計算
        pattern_stats['win_rate'] = pattern_stats['win_count'] / pattern_stats['race_count'] * 100
        pattern_stats['top3_rate'] = pattern_stats['top3_count'] / pattern_stats['race_count'] * 100
        pattern_stats['over_popularity_rate'] = pattern_stats['over_popularity_count'] / pattern_stats['race_count'] * 100
        pattern_stats['roi'] = pattern_stats['win_odds_sum'] / pattern_stats['race_count'] * 100
        
        # スコアの計算（回収率に基づくスコア）
        # 100%を基準に、それより高いと正のスコア、低いと負のスコア
        pattern_stats['score'] = (pattern_stats['roi'] - 100) / 20  # 20%につき1ポイント
        
        # 人気対比の観点も加味（人気以上に走る率が高いほど高評価）
        pattern_stats['score'] = pattern_stats['score'] + (pattern_stats['over_popularity_rate'] - 50) / 10  # 10%につき1ポイント
        
        return pattern_stats
    
    except Exception as e:
        logger.error(f"ペース偏差スコアの計算中にエラーが発生しました: {e}")
        return pd.DataFrame()
