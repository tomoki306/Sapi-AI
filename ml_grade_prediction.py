"""
機械学習による成績予測システム (scikit-learn)
過去の成績データから将来の成績を予測する高精度モデル
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from logger import log_info, log_error
import json
import pickle
import os


class GradePredictionML:
    """機械学習ベースの成績予測クラス"""
    
    def __init__(self):
        self.models = {
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42),
            'linear_regression': LinearRegression(),
            'ridge': Ridge(alpha=1.0)
        }
        self.scaler = StandardScaler()
        self.best_model = None
        self.best_model_name = None
        self.feature_names = []
        
    def prepare_features(self, grades_data):
        """
        成績データから特徴量を抽出
        
        Args:
            grades_data: 成績データのリスト
            
        Returns:
            特徴量のDataFrame
        """
        if not grades_data or len(grades_data) < 3:
            return None
        
        # DataFrameに変換
        df = pd.DataFrame(grades_data)
        df['date'] = pd.to_datetime(df['date'], format='mixed')
        df = df.sort_values('date')
        
        features = []
        
        for i in range(len(df)):
            if i < 2:  # 最低3つのデータポイントが必要
                continue
            
            # 過去のデータ
            past_data = df.iloc[:i]
            current_row = df.iloc[i]
            
            # 特徴量の計算
            feature_dict = {
                # 基本統計量
                'mean_grade': past_data['grade'].mean(),
                'std_grade': past_data['grade'].std(),
                'min_grade': past_data['grade'].min(),
                'max_grade': past_data['grade'].max(),
                'median_grade': past_data['grade'].median(),
                
                # トレンド特徴
                'recent_avg_3': past_data['grade'].tail(3).mean() if len(past_data) >= 3 else past_data['grade'].mean(),
                'recent_avg_5': past_data['grade'].tail(5).mean() if len(past_data) >= 5 else past_data['grade'].mean(),
                'trend_slope': self._calculate_trend(past_data['grade'].values),
                
                # 変動性
                'coefficient_variation': (past_data['grade'].std() / past_data['grade'].mean()) if past_data['grade'].mean() > 0 else 0,
                
                # カウント
                'num_tests': len(past_data[past_data['type'] == 'テスト']),
                'num_assignments': len(past_data[past_data['type'] == '課題']),
                
                # 重み付き平均
                'weighted_avg': (past_data['grade'] * past_data['weight']).sum() / past_data['weight'].sum() if past_data['weight'].sum() > 0 else past_data['grade'].mean(),
                
                # 時系列特徴
                'days_since_first': (current_row['date'] - past_data['date'].min()) / np.timedelta64(1, 'D'),
                'avg_days_between': self._calculate_avg_interval(past_data['date'].values),
                
                # ターゲット（実際の成績）
                'target': current_row['grade']
            }
            
            features.append(feature_dict)
        
        return pd.DataFrame(features)
    
    def _calculate_trend(self, grades):
        """成績のトレンド（傾き）を計算"""
        if len(grades) < 2:
            return 0
        x = np.arange(len(grades))
        try:
            slope = np.polyfit(x, grades, 1)[0]
            return slope
        except:
            return 0
    
    def _calculate_avg_interval(self, dates):
        """平均日数間隔を計算"""
        if len(dates) < 2:
            return 0
        intervals = []
        for i in range(len(dates)-1):
            diff = dates[i+1] - dates[i]
            # numpy.timedelta64 を日数に変換
            days = diff / np.timedelta64(1, 'D')
            intervals.append(days)
        return np.mean(intervals) if intervals else 0
    
    def train(self, grades_data, subject_name):
        """
        モデルの訓練
        
        Args:
            grades_data: 成績データのリスト
            subject_name: 科目名
            
        Returns:
            訓練結果の辞書
        """
        try:
            # 特徴量の準備
            df = self.prepare_features(grades_data)
            
            if df is None or len(df) < 5:
                return {
                    'success': False,
                    'error': 'データが不足しています（最低5件の成績データが必要）'
                }
            
            # 特徴量とターゲットの分離
            X = df.drop('target', axis=1)
            y = df['target']
            self.feature_names = X.columns.tolist()
            
            # データサイズに応じてテストサイズを調整
            if len(df) < 10:
                test_size = 0.2  # 小さいデータセット
            elif len(df) < 20:
                test_size = 0.25  # 中程度
            else:
                test_size = 0.3  # 十分なデータ
            
            # データの分割
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, shuffle=True
            )
            
            # データの診断情報
            diagnosis = {
                'total_samples': len(df),
                'train_samples': len(X_train),
                'test_samples': len(X_test),
                'target_mean': float(y.mean()),
                'target_std': float(y.std()),
                'target_min': float(y.min()),
                'target_max': float(y.max()),
                'has_nan': X.isnull().any().any() or y.isnull().any(),
                'feature_count': len(self.feature_names)
            }
            
            # スケーリング
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # 各モデルの訓練と評価
            results = {}
            best_score = -float('inf')
            
            for name, model in self.models.items():
                # 訓練
                model.fit(X_train_scaled, y_train)
                
                # 予測
                y_pred = model.predict(X_test_scaled)
                
                # 評価指標
                mse = mean_squared_error(y_test, y_pred)
                rmse = np.sqrt(mse)
                mae = mean_absolute_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                
                # クロスバリデーション
                cv_scores = cross_val_score(
                    model, X_train_scaled, y_train, 
                    cv=min(5, len(X_train)), 
                    scoring='r2'
                )
                
                results[name] = {
                    'rmse': rmse,
                    'mae': mae,
                    'r2': r2,
                    'cv_mean': cv_scores.mean(),
                    'cv_std': cv_scores.std()
                }
                
                # 最良モデルの選択（R2スコアで判断）
                if r2 > best_score:
                    best_score = r2
                    self.best_model = model
                    self.best_model_name = name
            
            # モデルの保存
            self._save_model(subject_name)
            
            log_info(f"成績予測モデルを訓練しました: {subject_name} (ベストモデル: {self.best_model_name})", "ML_TRAINING")
            
            return {
                'success': True,
                'results': results,
                'best_model': self.best_model_name,
                'best_score': best_score,
                'feature_importance': self._get_feature_importance(),
                'diagnosis': diagnosis  # 診断情報を追加
            }
            
        except Exception as e:
            log_error(e, f"ML_TRAINING_ERROR: {subject_name}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def predict_next_grade(self, grades_data, num_predictions=3):
        """
        次の成績を予測
        
        Args:
            grades_data: 成績データのリスト
            num_predictions: 予測する数
            
        Returns:
            予測結果のリスト
        """
        if not self.best_model:
            return None
        
        try:
            df = pd.DataFrame(grades_data)
            df['date'] = pd.to_datetime(df['date'], format='mixed')
            df = df.sort_values('date')
            
            predictions = []
            
            for i in range(num_predictions):
                # 特徴量の計算
                feature_dict = {
                    'mean_grade': df['grade'].mean(),
                    'std_grade': df['grade'].std(),
                    'min_grade': df['grade'].min(),
                    'max_grade': df['grade'].max(),
                    'median_grade': df['grade'].median(),
                    'recent_avg_3': df['grade'].tail(3).mean() if len(df) >= 3 else df['grade'].mean(),
                    'recent_avg_5': df['grade'].tail(5).mean() if len(df) >= 5 else df['grade'].mean(),
                    'trend_slope': self._calculate_trend(df['grade'].values),
                    'coefficient_variation': (df['grade'].std() / df['grade'].mean()) if df['grade'].mean() > 0 else 0,
                    'num_tests': len(df[df['type'] == 'テスト']),
                    'num_assignments': len(df[df['type'] == '課題']),
                    'weighted_avg': (df['grade'] * df['weight']).sum() / df['weight'].sum() if df['weight'].sum() > 0 else df['grade'].mean(),
                    'days_since_first': (pd.Timestamp(datetime.now()) - df['date'].min()) / np.timedelta64(1, 'D'),
                    'avg_days_between': self._calculate_avg_interval(df['date'].values)
                }
                
                # 特徴量をDataFrameに変換
                X_pred = pd.DataFrame([feature_dict])
                
                # スケーリング
                X_pred_scaled = self.scaler.transform(X_pred)
                
                # 予測
                predicted_grade = self.best_model.predict(X_pred_scaled)[0]
                
                # 予測値を0-100の範囲に制限
                predicted_grade = max(0, min(100, predicted_grade))
                
                predictions.append({
                    'prediction_num': i + 1,
                    'predicted_grade': round(predicted_grade, 1),
                    'confidence_interval': self._calculate_confidence_interval(predicted_grade)
                })
                
                # 次の予測のために予測値をデータに追加
                next_date = df['date'].max() + timedelta(days=int(feature_dict['avg_days_between']))
                new_row = pd.DataFrame([{
                    'date': next_date,
                    'type': 'テスト',
                    'grade': predicted_grade,
                    'weight': df['weight'].mean()
                }])
                df = pd.concat([df, new_row], ignore_index=True)
            
            return predictions
            
        except Exception as e:
            log_error(e, "ML_PREDICTION_ERROR")
            return None
    
    def _calculate_confidence_interval(self, prediction, confidence=0.95):
        """信頼区間の計算（簡易版）"""
        # 標準誤差の推定
        std_error = 5.0  # 仮の値（実際のデータから計算すべき）
        margin = 1.96 * std_error  # 95%信頼区間
        
        return {
            'lower': max(0, round(prediction - margin, 1)),
            'upper': min(100, round(prediction + margin, 1))
        }
    
    def _get_feature_importance(self):
        """特徴量の重要度を取得"""
        if not self.best_model or not hasattr(self.best_model, 'feature_importances_'):
            return None
        
        importance = self.best_model.feature_importances_
        return dict(zip(self.feature_names, importance))
    
    def _save_model(self, subject_name):
        """モデルの保存"""
        try:
            model_dir = 'ml_models'
            os.makedirs(model_dir, exist_ok=True)
            
            model_path = os.path.join(model_dir, f'{subject_name}_model.pkl')
            
            with open(model_path, 'wb') as f:
                pickle.dump({
                    'model': self.best_model,
                    'scaler': self.scaler,
                    'model_name': self.best_model_name,
                    'feature_names': self.feature_names
                }, f)
            
            log_info(f"モデルを保存しました: {model_path}", "ML_SAVE")
            
        except Exception as e:
            log_error(e, "ML_SAVE_ERROR")
    
    def load_model(self, subject_name):
        """モデルの読み込み"""
        try:
            model_path = os.path.join('ml_models', f'{subject_name}_model.pkl')
            
            if not os.path.exists(model_path):
                return False
            
            with open(model_path, 'rb') as f:
                data = pickle.load(f)
            
            self.best_model = data['model']
            self.scaler = data['scaler']
            self.best_model_name = data['model_name']
            self.feature_names = data['feature_names']
            
            log_info(f"モデルを読み込みました: {model_path}", "ML_LOAD")
            return True
            
        except Exception as e:
            log_error(e, "ML_LOAD_ERROR")
            return False


def display_ml_grade_prediction():
    """機械学習による成績予測UIの表示"""
    st.header("🤖 機械学習による高精度成績予測")
    
    st.info("""
    **scikit-learn を使用した高精度予測システム**
    - ランダムフォレスト、勾配ブースティングなど複数のモデルを比較
    - 自動的に最良のモデルを選択
    - 過去の成績データから将来の成績を予測
    """)
    
    # 成績データの確認
    if 'grades' not in st.session_state or not st.session_state.grades:
        st.warning("成績データがありません。まず成績を記録してください。")
        return
    
    # 科目の選択
    subjects = list(st.session_state.grades.keys())
    selected_subject = st.selectbox("予測する科目を選択", subjects)
    
    if not selected_subject:
        return
    
    grades_data = st.session_state.grades[selected_subject]
    
    if len(grades_data) < 5:
        st.warning(f"⚠️ {selected_subject}の成績データが不足しています（現在{len(grades_data)}件、最低5件必要）")
        return
    
    # タブで機能を分割
    tab1, tab2, tab3 = st.tabs(["📊 モデル訓練", "🔮 成績予測", "📈 分析・可視化"])
    
    with tab1:
        st.subheader("モデルの訓練")
        
        st.write(f"**データ数**: {len(grades_data)}件")
        
        # データ品質の簡易チェック
        df_check = pd.DataFrame(grades_data)
        df_check['grade'] = pd.to_numeric(df_check['grade'], errors='coerce')
        
        grade_std = df_check['grade'].std()
        grade_mean = df_check['grade'].mean()
        coefficient_of_variation = (grade_std / grade_mean) if grade_mean > 0 else 0
        
        # データ品質の表示
        with st.expander("📋 データ品質チェック", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("平均点", f"{grade_mean:.1f}")
            with col2:
                st.metric("標準偏差", f"{grade_std:.1f}")
            with col3:
                cv_status = "安定" if coefficient_of_variation < 0.3 else "変動大"
                st.metric("変動係数", f"{coefficient_of_variation:.2f}", cv_status)
            
            # データ量の評価
            if len(grades_data) < 10:
                st.warning(f"⚠️ データが少ないです（現在{len(grades_data)}件）。精度向上のため、10件以上の記録を推奨します。")
            elif len(grades_data) < 20:
                st.info(f"💡 データは十分ですが、20件以上あるとより高精度になります。")
            else:
                st.success(f"✅ 十分なデータ量です！高精度な予測が期待できます。")
            
            # 変動の評価
            if coefficient_of_variation > 0.4:
                st.warning("⚠️ 成績の変動が大きいです。予測精度が低下する可能性があります。")
            elif coefficient_of_variation > 0.3:
                st.info("💡 成績に適度な変動があります。")
            else:
                st.success("✅ 成績が安定しています。")
        
        if st.button("🚀 モデルを訓練", type="primary"):
            with st.spinner("モデルを訓練中..."):
                ml_predictor = GradePredictionML()
                result = ml_predictor.train(grades_data, selected_subject)
                
                if result['success']:
                    best_score = result['best_score']
                    
                    # R²スコアの評価と説明
                    if best_score >= 0.8:
                        score_emoji = "⭐⭐⭐⭐⭐"
                        score_text = "非常に優秀"
                        score_color = "green"
                    elif best_score >= 0.6:
                        score_emoji = "⭐⭐⭐⭐"
                        score_text = "良好"
                        score_color = "green"
                    elif best_score >= 0.4:
                        score_emoji = "⭐⭐⭐"
                        score_text = "普通"
                        score_color = "orange"
                    elif best_score >= 0:
                        score_emoji = "⭐⭐"
                        score_text = "改善が必要"
                        score_color = "orange"
                    else:
                        score_emoji = "⭐"
                        score_text = "要改善（データ不足または不規則）"
                        score_color = "red"
                    
                    st.success(f"✅ 訓練完了！ベストモデル: **{result['best_model']}**")
                    
                    # R²スコアの説明ボックス
                    if best_score < 0:
                        # 診断情報の取得
                        diag = result.get('diagnosis', {})
                        
                        # 具体的な問題点を診断
                        issues = []
                        recommendations = []
                        
                        # データ量の確認
                        if diag.get('total_samples', 0) < 15:
                            issues.append(f"✗ データが少ない（{diag.get('total_samples', 0)}件 → 推奨: 20件以上）")
                            recommendations.append("📊 より多くの成績データを記録してください")
                        
                        # 変動の確認
                        target_std = diag.get('target_std', 0)
                        target_mean = diag.get('target_mean', 0)
                        if target_mean > 0:
                            cv = target_std / target_mean
                            if cv > 0.4:
                                issues.append(f"✗ 成績の変動が大きい（変動係数: {cv:.2f}）")
                                recommendations.append("📈 学習方法を安定させて、成績の変動を抑えてください")
                        
                        # 成績範囲の確認
                        target_range = diag.get('target_max', 100) - diag.get('target_min', 0)
                        if target_range < 20:
                            issues.append(f"✗ 成績の範囲が狭い（{target_range:.1f}点）")
                            recommendations.append("💡 データが似た値ばかりだと予測が難しくなります")
                        
                        # テストサンプル数の確認
                        if diag.get('test_samples', 0) < 3:
                            issues.append(f"✗ テストデータが少ない（{diag.get('test_samples', 0)}件）")
                            recommendations.append("📝 全体のデータ数を増やしてください")
                        
                        # 診断結果の表示
                        st.error(f"""
                        ### {score_emoji} R²スコア: {best_score:.3f} ({score_text})
                        
                        **⚠️ 負のR²スコアについて:**
                        R²スコアが負の値（{best_score:.3f}）は、モデルの予測が「平均値を使うより悪い」ことを意味します。
                        
                        **🔍 検出された問題点:**
                        {chr(10).join(issues) if issues else '- 特定の問題は検出されませんでした'}
                        
                        **💡 具体的な改善方法:**
                        {chr(10).join(recommendations) if recommendations else '1. より多くのデータを追加してください'}
                        
                        **📊 データ診断:**
                        - 訓練データ: {diag.get('train_samples', 0)}件
                        - テストデータ: {diag.get('test_samples', 0)}件
                        - 成績平均: {diag.get('target_mean', 0):.1f}点
                        - 成績範囲: {diag.get('target_min', 0):.1f}〜{diag.get('target_max', 100):.1f}点
                        
                        **現状での使用:**
                        予測機能は使用できますが、精度が低いため参考程度にしてください。
                        """)
                    elif best_score < 0.4:
                        st.warning(f"""
                        ### {score_emoji} R²スコア: {best_score:.3f} ({score_text})
                        
                        **📊 スコアの意味:**
                        モデルは動作しますが、予測精度は低めです。
                        
                        **改善方法:**
                        - より多くのデータを追加（現在: {len(grades_data)}件 → 推奨: 15件以上）
                        - データの変動を確認
                        """)
                    else:
                        st.info(f"""
                        ### {score_emoji} R²スコア: {best_score:.3f} ({score_text})
                        
                        **📊 スコアの意味:**
                        R²スコアは「モデルがどれだけデータを説明できるか」を示します（0〜1が正常範囲）。
                        
                        - **1.0**: 完璧な予測
                        - **0.8以上**: 非常に優秀 ⭐⭐⭐⭐⭐
                        - **0.6-0.8**: 良好 ⭐⭐⭐⭐
                        - **0.4-0.6**: 普通 ⭐⭐⭐
                        - **0.4未満**: 改善が必要 ⭐⭐
                        """)
                    
                    # モデルの性能比較
                    st.subheader("📊 モデル性能比較")
                    
                    comparison_data = []
                    for model_name, metrics in result['results'].items():
                        comparison_data.append({
                            'モデル': model_name,
                            'R² スコア': f"{metrics['r2']:.3f}",
                            'RMSE': f"{metrics['rmse']:.2f}",
                            'MAE': f"{metrics['mae']:.2f}",
                            'CV平均': f"{metrics['cv_mean']:.3f}",
                            'CV標準偏差': f"{metrics['cv_std']:.3f}"
                        })
                    
                    df_comparison = pd.DataFrame(comparison_data)
                    st.dataframe(df_comparison, use_container_width=True)
                    
                    # 特徴量の重要度
                    if result.get('feature_importance'):
                        st.subheader("🎯 特徴量の重要度")
                        importance_df = pd.DataFrame(
                            list(result['feature_importance'].items()),
                            columns=['特徴量', '重要度']
                        ).sort_values('重要度', ascending=False)
                        
                        fig = px.bar(
                            importance_df.head(10),
                            x='重要度',
                            y='特徴量',
                            orientation='h',
                            title='上位10の重要な特徴量'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                else:
                    st.error(f"❌ 訓練失敗: {result['error']}")
    
    with tab2:
        st.subheader("成績予測")
        
        # モデルの読み込み
        ml_predictor = GradePredictionML()
        if not ml_predictor.load_model(selected_subject):
            st.warning("⚠️ 保存されたモデルがありません。まず「モデル訓練」タブでモデルを訓練してください。")
            return
        
        st.success(f"✅ モデル読み込み完了: {ml_predictor.best_model_name}")
        
        num_predictions = st.slider("予測する回数", 1, 10, 3)
        
        if st.button("🔮 予測を実行", type="primary"):
            with st.spinner("予測中..."):
                predictions = ml_predictor.predict_next_grade(grades_data, num_predictions)
                
                if predictions:
                    st.subheader("📊 予測結果")
                    
                    for pred in predictions:
                        col1, col2 = st.columns([1, 2])
                        
                        with col1:
                            st.metric(
                                f"予測 {pred['prediction_num']}",
                                f"{pred['predicted_grade']:.1f}点"
                            )
                        
                        with col2:
                            ci = pred['confidence_interval']
                            st.write(f"**95%信頼区間**: {ci['lower']:.1f} ~ {ci['upper']:.1f}点")
                            
                            # プログレスバー風の可視化
                            progress = pred['predicted_grade'] / 100
                            st.progress(progress)
                    
                    # 予測の可視化
                    st.subheader("📈 予測の可視化")
                    
                    # 過去のデータ
                    df_history = pd.DataFrame(grades_data)
                    df_history['date'] = pd.to_datetime(df_history['date'], format='mixed')
                    df_history = df_history.sort_values('date')
                    df_history['type_label'] = '実績'
                    
                    # 予測データ
                    last_date = df_history['date'].max()
                    avg_interval = ml_predictor._calculate_avg_interval(df_history['date'].values)
                    
                    pred_data = []
                    for i, pred in enumerate(predictions):
                        pred_date = last_date + timedelta(days=int(avg_interval * (i + 1)))
                        pred_data.append({
                            'date': pred_date,
                            'grade': pred['predicted_grade'],
                            'type_label': '予測'
                        })
                    
                    df_pred = pd.DataFrame(pred_data)
                    
                    # グラフ作成
                    fig = go.Figure()
                    
                    # 実績データ
                    fig.add_trace(go.Scatter(
                        x=df_history['date'],
                        y=df_history['grade'],
                        mode='lines+markers',
                        name='実績',
                        line=dict(color='blue', width=2),
                        marker=dict(size=8)
                    ))
                    
                    # 予測データ
                    fig.add_trace(go.Scatter(
                        x=df_pred['date'],
                        y=df_pred['grade'],
                        mode='lines+markers',
                        name='予測',
                        line=dict(color='red', width=2, dash='dash'),
                        marker=dict(size=8, symbol='star')
                    ))
                    
                    fig.update_layout(
                        title='成績の推移と予測',
                        xaxis_title='日付',
                        yaxis_title='成績',
                        yaxis=dict(range=[0, 100]),
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                else:
                    st.error("予測に失敗しました")
    
    with tab3:
        st.subheader("分析・可視化")
        
        # 基本統計
        df = pd.DataFrame(grades_data)
        df['date'] = pd.to_datetime(df['date'], format='mixed')
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("平均点", f"{df['grade'].mean():.1f}")
        with col2:
            st.metric("標準偏差", f"{df['grade'].std():.1f}")
        with col3:
            st.metric("最高点", f"{df['grade'].max():.0f}")
        with col4:
            st.metric("最低点", f"{df['grade'].min():.0f}")
        
        # 成績分布
        st.subheader("📊 成績分布")
        fig_hist = px.histogram(
            df,
            x='grade',
            nbins=20,
            title='成績の分布',
            labels={'grade': '成績', 'count': '度数'}
        )
        st.plotly_chart(fig_hist, use_container_width=True)
        
        # トレンド分析
        st.subheader("📈 トレンド分析")
        ml_predictor = GradePredictionML()
        trend_slope = ml_predictor._calculate_trend(df['grade'].values)
        
        if trend_slope > 0.5:
            st.success(f"📈 上昇トレンド（傾き: {trend_slope:.2f}）- 成績が向上しています！")
        elif trend_slope < -0.5:
            st.warning(f"📉 下降トレンド（傾き: {trend_slope:.2f}）- 改善の余地があります")
        else:
            st.info(f"➡️ 安定（傾き: {trend_slope:.2f}）- 安定した成績を維持しています")


if __name__ == "__main__":
    # テスト用
    display_ml_grade_prediction()
