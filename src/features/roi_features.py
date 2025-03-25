"""
回収率(ROI)関連特徴量モジュール
"""
import pandas as pd
import numpy as np
import logging
from ..data.extraction import extract_horse_pedigree_data

logger = logging.getLogger(__name__)

def calculate_sire_track_roi(race_df, result_df, min_races=20):
    """
    種牡馬×馬場適性ROIを計算する関数
    
    種牡馬の産駒が特定の馬場条件でどれだけ回収率が高いかを計算する
    
    Args:
        race_df (DataFrame): レース基本情報のDataFrame
        result_df (DataFrame): レース結果のDataFrame
        min_races (int): 最低レース数の閾値
    
    Returns:
        DataFrame: 種牡馬×馬場適性ROIのDataFrame
    """
    try:
        # レースIDの作成
        race_df['race_id'] = race_df['kaisai_nen'] + race_df['kaisai_tsukihi'] + race_df['keibajo_code'] + race_df['race_bango']
        result_df['race_id'] = result_df['kaisai_nen'] + result_df['kaisai_tsukihi'] + result_df['keibajo_code'] + result_df['race_bango']
        
        # データ結合
        df = pd.merge(result_df, race_df, on='race_id', suffixes=('', '_race'))
        
        # 勝利フラグを追加
        df['win'] = (df['kakutei_chakujun'] == '01').astype(int)
        
        # 馬場状態の判定
        df['track_type'] = df['track_code'].apply(
            lambda x: '芝' if str(x).startswith('1') else 'ダート' if str(x).startswith('2') else 'その他'
        )
        
        df['track_condition'] = df['baba_jotai'].map(
            {'1': '良', '2': '稍重', '3': '重', '4': '不良', '0': '未設定'}
        )
        
        # 血統データ取得
        horse_ids = df['ketto_toroku_bango'].unique()
        logger.info(f"血統データを取得中 ({len(horse_ids)}頭)...")
        pedigree_df = extract_horse_pedigree_data(horse_ids)
        
        # 血統情報を結合
        df = pd.merge(df, pedigree_df[['ketto_toroku_bango', 'sire_id', 'sire_name']], 
                     on='ketto_toroku_bango', how='left')
        
        # 数値型への変換
        df['tansho_odds'] = pd.to_numeric(df['tansho_odds'], errors='coerce') / 10
        df['tansho_ninkijun'] = pd.to_numeric(df['tansho_ninkijun'], errors='coerce')
        
        # 種牡馬×トラック×馬場状態のグループ集計
        roi_data = df.groupby(['sire_id', 'sire_name', 'track_type', 'track_condition']).agg(
            race_count=('race_id', 'count'),
            win_count=('win', 'sum'),
            win_odds_sum=('tansho_odds', lambda x: df.loc[df['win'] == 1, 'tansho_odds'].sum()),
            avg_popularity=('tansho_ninkijun', 'mean')
        ).reset_index()
        
        # 勝率と回収率の計算
        roi_data['win_rate'] = roi_data['win_count'] / roi_data['race_count'] * 100
        roi_data['roi'] = roi_data['win_odds_sum'] / roi_data['race_count'] * 100
        
        # 平均勝利オッズの計算 (0除算回避)
        roi_data['avg_win_odds'] = roi_data.apply(
            lambda x: x['win_odds_sum'] / x['win_count'] if x['win_count'] > 0 else 0, 
            axis=1
        )
        
        # サンプル数の少ないものを除外
        roi_data = roi_data[roi_data['race_count'] >= min_races]
        
        # 回収率でソート
        roi_data = roi_data.sort_values('roi', ascending=False)
        
        return roi_data
    
    except Exception as e:
        logger.error(f"種牡馬×馬場適性ROI計算中にエラーが発生しました: {e}")
        return pd.DataFrame()

def calculate_jockey_course_odds(race_df, result_df, min_rides=10):
    """
    騎手のコース別平均配当を計算する関数
    
    各騎手が特定コースで勝利したときの平均配当を計算する
    
    Args:
        race_df (DataFrame): レース基本情報のDataFrame
        result_df (DataFrame): レース結果のDataFrame
        min_rides (int): 最低騎乗数の閾値
    
    Returns:
        DataFrame: 騎手のコース別平均配当のDataFrame
    """
    try:
        # レースIDの作成
        race_df['race_id'] = race_df['kaisai_nen'] + race_df['kaisai_tsukihi'] + race_df['keibajo_code'] + race_df['race_bango']
        result_df['race_id'] = result_df['kaisai_nen'] + result_df['kaisai_tsukihi'] + result_df['keibajo_code'] + result_df['race_bango']
        
        # データ結合
        df = pd.merge(result_df, race_df, on='race_id', suffixes=('', '_race'))
        
        # 勝利フラグを追加
        df['win'] = (df['kakutei_chakujun'] == '01').astype(int)
        
        # 競馬場名の変換
        df['course_name'] = df['keibajo_code'].map({
            '01': '札幌', '02': '函館', '03': '福島', '04': '新潟',
            '05': '東京', '06': '中山', '07': '中京', '08': '京都',
            '09': '阪神', '10': '小倉'
        })
        
        # トラックタイプの判定
        df['track_type'] = df['track_code'].apply(
            lambda x: '芝' if str(x).startswith('1') else 'ダート' if str(x).startswith('2') else 'その他'
        )
        
        # 距離区分の作成
        df['kyori'] = pd.to_numeric(df['kyori'], errors='coerce')
        df['distance_category'] = pd.cut(
            df['kyori'],
            bins=[0, 1400, 2000, 10000],
            labels=['短距離', '中距離', '長距離']
        )
        
        # 数値型への変換
        df['tansho_odds'] = pd.to_numeric(df['tansho_odds'], errors='coerce') / 10
        df['tansho_ninkijun'] = pd.to_numeric(df['tansho_ninkijun'], errors='coerce')
        
        # 騎手×コース×距離区分のグループ集計
        jockey_data = df.groupby([
            'kishu_code', 'kishumei_ryakusho', 'course_name', 'track_type', 'distance_category'
        ]).agg(
            ride_count=('race_id', 'count'),
            win_count=('win', 'sum'),
            win_odds_sum=('tansho_odds', lambda x: df.loc[df['win'] == 1, 'tansho_odds'].sum()),
            avg_popularity=('tansho_ninkijun', 'mean')
        ).reset_index()
        
        # 勝率と回収率の計算
        jockey_data['win_rate'] = jockey_data['win_count'] / jockey_data['ride_count'] * 100
        jockey_data['roi'] = jockey_data['win_odds_sum'] / jockey_data['ride_count'] * 100
        
        # 平均勝利オッズの計算 (0除算回避)
        jockey_data['avg_win_odds'] = jockey_data.apply(
            lambda x: x['win_odds_sum'] / x['win_count'] if x['win_count'] > 0 else 0, 
            axis=1
        )
        
        # サンプル数の少ないものを除外
        jockey_data = jockey_data[jockey_data['ride_count'] >= min_rides]
        
        # 回収率でソート
        jockey_data = jockey_data.sort_values('roi', ascending=False)
        
        return jockey_data
    
    except Exception as e:
        logger.error(f"騎手のコース別平均配当計算中にエラーが発生しました: {e}")
        return pd.DataFrame()

def calculate_horse_course_roi(race_df, result_df, min_races=3):
    """
    馬のコース実績ROIを計算する関数
    
    各馬が特定コースでどれだけ回収率が高いかを計算する
    
    Args:
        race_df (DataFrame): レース基本情報のDataFrame
        result_df (DataFrame): レース結果のDataFrame
        min_races (int): 最低レース数の閾値
    
    Returns:
        DataFrame: 馬のコース実績ROIのDataFrame
    """
    try:
        # レースIDの作成
        race_df['race_id'] = race_df['kaisai_nen'] + race_df['kaisai_tsukihi'] + race_df['keibajo_code'] + race_df['race_bango']
        result_df['race_id'] = result_df['kaisai_nen'] + result_df['kaisai_tsukihi'] + result_df['keibajo_code'] + result_df['race_bango']
        
        # データ結合
        df = pd.merge(result_df, race_df, on='race_id', suffixes=('', '_race'))
        
        # 勝利フラグを追加
        df['win'] = (df['kakutei_chakujun'] == '01').astype(int)
        
        # 競馬場名の変換
        df['course_name'] = df['keibajo_code'].map({
            '01': '札幌', '02': '函館', '03': '福島', '04': '新潟',
            '05': '東京', '06': '中山', '07': '中京', '08': '京都',
            '09': '阪神', '10': '小倉'
        })
        
        # トラックタイプの判定
        df['track_type'] = df['track_code'].apply(
            lambda x: '芝' if str(x).startswith('1') else 'ダート' if str(x).startswith('2') else 'その他'
        )
        
        # 距離区分の作成
        df['kyori'] = pd.to_numeric(df['kyori'], errors='coerce')
        df['distance_category'] = pd.cut(
            df['kyori'],
            bins=[0, 1400, 2000, 10000],
            labels=['短距離', '中距離', '長距離']
        )
        
        # 数値型への変換
        df['tansho_odds'] = pd.to_numeric(df['tansho_odds'], errors='coerce') / 10
        df['tansho_ninkijun'] = pd.to_numeric(df['tansho_ninkijun'], errors='coerce')
        
        # 馬×コース×トラック×距離区分のグループ集計
        horse_data = df.groupby([
            'ketto_toroku_bango', 'bamei', 'course_name', 'track_type', 'distance_category'
        ]).agg(
            race_count=('race_id', 'count'),
            win_count=('win', 'sum'),
            win_odds_sum=('tansho_odds', lambda x: df.loc[df['win'] == 1, 'tansho_odds'].sum()),
            avg_popularity=('tansho_ninkijun', 'mean')
        ).reset_index()
        
        # 勝率と回収率の計算
        horse_data['win_rate'] = horse_data['win_count'] / horse_data['race_count'] * 100
        horse_data['roi'] = horse_data['win_odds_sum'] / horse_data['race_count'] * 100
        
        # 平均勝利オッズの計算 (0除算回避)
        horse_data['avg_win_odds'] = horse_data.apply(
            lambda x: x['win_odds_sum'] / x['win_count'] if x['win_count'] > 0 else 0, 
            axis=1
        )
        
        # サンプル数の少ないものを除外
        horse_data = horse_data[horse_data['race_count'] >= min_races]
        
        # リピーターレベルの判定
        horse_data['repeater_level'] = pd.cut(
            horse_data['win_rate'],
            bins=[-0.1, 10, 15, 25, 100],
            labels=['WEAK_REPEATER', 'AVERAGE_REPEATER', 'GOOD_REPEATER', 'STRONG_REPEATER']
        )
        
        # 回収率でソート
        horse_data = horse_data.sort_values('roi', ascending=False)
        
        return horse_data
    
    except Exception as e:
        logger.error(f"馬のコース実績ROI計算中にエラーが発生しました: {e}")
        return pd.DataFrame()
