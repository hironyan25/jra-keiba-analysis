"""
JVDデータベースからのデータ抽出モジュール
"""
import pandas as pd
import numpy as np
import logging
from .database import get_engine, get_session

logger = logging.getLogger(__name__)

def extract_race_base_data(year_from=2010, year_to=2023, chunksize=None):
    """
    基本レース情報を抽出する関数
    
    Args:
        year_from (int): 抽出開始年
        year_to (int): 抽出終了年
        chunksize (int, optional): チャンクサイズ。指定するとジェネレータを返す
    
    Returns:
        DataFrame or Generator: レースデータのDataFrameまたはジェネレータ
    """
    query = f"""
    SELECT 
        r.kaisai_nen, r.kaisai_tsukihi, r.keibajo_code, r.race_bango,
        r.kyori, r.track_code, r.tenko_code, 
        CASE 
            WHEN SUBSTRING(r.track_code, 1, 1) = '1' THEN r.babajotai_code_shiba 
            ELSE r.babajotai_code_dirt 
        END as baba_jotai,
        r.shusso_tosu, r.grade_code, r.juryo_shubetsu_code
    FROM jvd_ra r
    WHERE r.kaisai_nen BETWEEN '{year_from}' AND '{year_to}'
    ORDER BY r.kaisai_nen, r.kaisai_tsukihi, r.keibajo_code, r.race_bango
    """
    
    engine = get_engine()
    
    try:
        if chunksize:
            return pd.read_sql_query(query, engine, chunksize=chunksize)
        else:
            return pd.read_sql_query(query, engine)
    except Exception as e:
        logger.error(f"レースデータ抽出中にエラーが発生しました: {e}")
        return pd.DataFrame()

def extract_horse_result_data(year_from=2010, year_to=2023, chunksize=None):
    """
    馬の出走結果データを抽出する関数
    
    Args:
        year_from (int): 抽出開始年
        year_to (int): 抽出終了年
        chunksize (int, optional): チャンクサイズ。指定するとジェネレータを返す
    
    Returns:
        DataFrame or Generator: 馬の結果データのDataFrameまたはジェネレータ
    """
    query = f"""
    SELECT 
        s.kaisai_nen, s.kaisai_tsukihi, s.keibajo_code, s.race_bango,
        s.ketto_toroku_bango, s.bamei, s.wakuban, s.umaban,
        s.barei, s.seibetsu_code, s.bataiju, s.zogen_fugo, s.zogen_sa,
        s.kishu_code, s.kishumei_ryakusho, 
        s.chokyoshi_code, s.chokyoshimei_ryakusho,
        s.kakutei_chakujun, s.soha_time, s.kohan_3f,
        s.tansho_odds, s.tansho_ninkijun,
        s.corner_01_tsuka_juni, s.corner_02_tsuka_juni, 
        s.corner_03_tsuka_juni, s.corner_04_tsuka_juni
    FROM jvd_se s
    WHERE s.kaisai_nen BETWEEN '{year_from}' AND '{year_to}'
    ORDER BY s.kaisai_nen, s.kaisai_tsukihi, s.keibajo_code, s.race_bango, s.umaban
    """
    
    engine = get_engine()
    
    try:
        if chunksize:
            return pd.read_sql_query(query, engine, chunksize=chunksize)
        else:
            return pd.read_sql_query(query, engine)
    except Exception as e:
        logger.error(f"馬結果データ抽出中にエラーが発生しました: {e}")
        return pd.DataFrame()

def extract_horse_pedigree_data(horse_ids=None):
    """
    馬の血統データを抽出する関数
    
    Args:
        horse_ids (list, optional): 馬IDのリスト。指定しない場合は全馬を取得
    
    Returns:
        DataFrame: 馬の血統データのDataFrame
    """
    if horse_ids:
        horse_id_list = ",".join([f"'{id}'" for id in horse_ids])
        where_clause = f"WHERE u.ketto_toroku_bango IN ({horse_id_list})"
    else:
        where_clause = ""
    
    query = f"""
    SELECT 
        u.ketto_toroku_bango,
        TRIM(u.bamei) AS bamei,
        u.seinengappi,
        u.seibetsu_code,
        u.ketto_joho_01a AS sire_id,
        TRIM(u.ketto_joho_01b) AS sire_name,
        u.ketto_joho_02a AS dam_id,
        TRIM(u.ketto_joho_02b) AS dam_name,
        u.ketto_joho_03a AS broodmare_sire_id,
        TRIM(u.ketto_joho_03b) AS broodmare_sire_name
    FROM jvd_um u
    {where_clause}
    """
    
    engine = get_engine()
    
    try:
        return pd.read_sql_query(query, engine)
    except Exception as e:
        logger.error(f"血統データ抽出中にエラーが発生しました: {e}")
        return pd.DataFrame()

def extract_race_payouts_data(year_from=2010, year_to=2023):
    """
    レース払戻情報を抽出する関数
    
    Args:
        year_from (int): 抽出開始年
        year_to (int): 抽出終了年
    
    Returns:
        DataFrame: レース払戻データのDataFrame
    """
    query = f"""
    SELECT 
        hr.kaisai_nen, hr.kaisai_tsukihi, hr.keibajo_code, hr.race_bango,
        hr.haraimodoshi_tansho_1, hr.haraimodoshi_tansho_2, hr.haraimodoshi_tansho_3,
        hr.haraimodoshi_fukusho_1, hr.haraimodoshi_fukusho_2, hr.haraimodoshi_fukusho_3,
        hr.haraimodoshi_fukusho_4, hr.haraimodoshi_fukusho_5,
        hr.haraimodoshi_wakuren_1, hr.haraimodoshi_wakuren_2, hr.haraimodoshi_wakuren_3,
        hr.haraimodoshi_umaren_1, hr.haraimodoshi_umaren_2, hr.haraimodoshi_umaren_3,
        hr.haraimodoshi_wide_1, hr.haraimodoshi_wide_2, hr.haraimodoshi_wide_3,
        hr.haraimodoshi_wide_4, hr.haraimodoshi_wide_5, hr.haraimodoshi_wide_6, hr.haraimodoshi_wide_7,
        hr.haraimodoshi_umatan_1, hr.haraimodoshi_umatan_2, hr.haraimodoshi_umatan_3,
        hr.haraimodoshi_sanrenfuku_1, hr.haraimodoshi_sanrenfuku_2, hr.haraimodoshi_sanrenfuku_3,
        hr.haraimodoshi_sanrentan_1, hr.haraimodoshi_sanrentan_2, hr.haraimodoshi_sanrentan_3
    FROM jvd_hr hr
    WHERE hr.kaisai_nen BETWEEN '{year_from}' AND '{year_to}'
    ORDER BY hr.kaisai_nen, hr.kaisai_tsukihi, hr.keibajo_code, hr.race_bango
    """
    
    engine = get_engine()
    
    try:
        return pd.read_sql_query(query, engine)
    except Exception as e:
        logger.error(f"払戻データ抽出中にエラーが発生しました: {e}")
        return pd.DataFrame()

def get_race_id(row):
    """レースIDを生成する関数"""
    return f"{row['kaisai_nen']}{row['kaisai_tsukihi']}{row['keibajo_code']}{row['race_bango']}"

def get_horse_race_id(row):
    """馬のレースIDを生成する関数"""
    return f"{row['kaisai_nen']}{row['kaisai_tsukihi']}{row['keibajo_code']}{row['race_bango']}_{row['ketto_toroku_bango']}"
