import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import os
import time
from typing import List, Dict
from src.utils.fingerprint import fingerprint_file
from src.db.database import get_db
from src.db.matcher import match_song


class AgentEvaluator:
    """Agent 评估器"""

    def evaluate_recognition(self, test_cases: List[Dict]) -> Dict:
        """
        真实评估识别准确率。
        test_cases 格式：[{"audio": "data/songs/xxx.mp3", "expected": "歌曲名"}, ...]
        返回：Precision, Recall, F1
        """
        tp = 0  
        fp = 0  
        fn = 0  

        for tc in test_cases:
            audio_path = tc["audio"]
            expected = tc["expected"]

            if not os.path.exists(audio_path):
                print(f"  [跳过] 文件不存在: {audio_path}")
                fn += 1
                continue

            try:
                hashes = fingerprint_file(audio_path)
                db = next(get_db())
                result = match_song(db, hashes)
            except Exception as e:
                print(f"  [识别失败] {audio_path}: {e}")
                fn += 1
                continue

            if result is None:
                fn += 1
                print(f"  [漏报] {audio_path} 期望《{expected}》，未识别出结果")
            elif result["song_name"] == expected:
                tp += 1
                print(f"  [命中] {audio_path} -> 《{result['song_name']}》(score={result['match_score']})")
            else:
                fp += 1
                print(f"  [误报] {audio_path} 期望《{expected}》，实际识别为《{result['song_name']}》")

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        return {
            "tp": tp, "fp": fp, "fn": fn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4)
        }

    def evaluate_rag(self, queries: List[str], ground_truth: List[str], k: int = 5) -> Dict:
        """
        真实评估 RAG 检索质量。
        queries: 查询语句列表
        ground_truth: 每个查询对应的正确答案（歌曲名）列表
        """
        from src.utils.rag import hybrid_search

        hit = 0
        total = len(queries)

        for i, q in enumerate(queries):
            try:
                results = hybrid_search(q, top_k=k)
                returned_songs = [r["data"]["song_name"] for r in results]
                if ground_truth[i] in returned_songs:
                    hit += 1
                    print(f"  [命中] 查询「{q}」-> 前{k}中包含《{ground_truth[i]}》")
                else:
                    print(f"  [未命中] 查询「{q}」-> 前{k}中未包含《{ground_truth[i]}》，实际返回: {returned_songs}")
            except Exception as e:
                print(f"  [检索报错] 查询「{q}」: {e}")

        recall_at_k = hit / total if total > 0 else 0
        return {"recall@{}".format(k): round(recall_at_k, 4), "hit": hit, "total": total}


if __name__ == '__main__':
    evaluator = AgentEvaluator()

    print("=== 真实评估：听歌识曲识别准确率 ===")
    test_cases = [
        {"audio": "songfile.mp3", "expected": "第一首歌"},
    ]

    start = time.time()
    result = evaluator.evaluate_recognition(test_cases)
    elapsed = time.time() - start

    print(f"\n--- 评估结果（耗时 {elapsed:.2f} 秒）---")
    print(f"TP(命中)={result['tp']}, FP(误报)={result['fp']}, FN(漏报)={result['fn']}")
    print(f"Precision(查准率): {result['precision']}")
    print(f"Recall(查全率): {result['recall']}")
    print(f"F1 Score: {result['f1']}")