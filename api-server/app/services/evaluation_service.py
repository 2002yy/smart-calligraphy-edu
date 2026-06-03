import sqlite3
import threading
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories import EvaluationRepository, HomeworkRepository, ReviewRepository, TaskRepository
from app.schemas.evaluation import EvaluationProvider
from app.services.file_storage_service import FileStorageService
from app.services.openai_evaluation_service import OpenAIEvaluationService  # DEPRECATED
from app.services.qwen_evaluation_service import QwenEvaluationService


def _query_calligraphy(character: str, top_k: int = 6) -> list[str]:
    """查询碑帖数据库，返回该字的图片 URL 列表"""
    db_path = Path(__file__).resolve().parents[2] / "smart_calligraphy.db"
    if not db_path.exists():
        return []
    try:
        conn = sqlite3.connect(str(db_path))
        rows = conn.execute(
            "SELECT image_path FROM calligraphy_db WHERE character = ? ORDER BY RANDOM() LIMIT ?",
            (character, top_k),
        ).fetchall()
        conn.close()
        return [row[0] for row in rows]
    except Exception:
        return []


class EvaluationService:
    @staticmethod
    def _serialize(evaluation, character: str | None = None) -> dict:
        tags = evaluation.issues_json or []
        result = {
            "id": evaluation.id,
            "homework_id": evaluation.homework_id,
            "score": evaluation.total_score,
            "total_score": evaluation.total_score,
            "structure_score": evaluation.structure_score,
            "center_score": evaluation.center_score,
            "stroke_order_score": evaluation.stroke_order_score,
            "tags": tags,
            "issues": tags,
            "advice": evaluation.advice_text,
            "compare_image_url": evaluation.compare_image_url,
            "thinking_steps": evaluation.thinking_steps,
            "status": evaluation.status,
            "created_at": evaluation.created_at,
            "calligraphy_images": _query_calligraphy(character) if character else [],
        }
        return result

    @staticmethod
    def _resolve_provider(requested_provider: EvaluationProvider) -> EvaluationProvider:
        if requested_provider == EvaluationProvider.mock:
            return EvaluationProvider.mock
        if requested_provider == EvaluationProvider.qwen:
            if not QwenEvaluationService.is_configured():
                raise HTTPException(status_code=400, detail="Qwen 评测未启用。请设置 QWEN_EVALUATION_ENABLED=true 并配置 QWEN_API_KEY（阿里云百炼 API Key）。")
            return EvaluationProvider.qwen
        if requested_provider == EvaluationProvider.openai:
            if not OpenAIEvaluationService.is_configured():
                raise HTTPException(status_code=400, detail="OpenAI evaluation is not enabled.")
            return EvaluationProvider.openai
        if QwenEvaluationService.is_configured():
            return EvaluationProvider.qwen
        if settings.evaluation_provider == EvaluationProvider.openai.value and OpenAIEvaluationService.is_configured():
            return EvaluationProvider.openai
        return EvaluationProvider.mock

    @staticmethod
    def _build_mock_result(homework_id: int, task, image_url: str = "") -> dict:
        base = 10.0 - (homework_id % 10) * 0.85
        structure_score = round(min(10, max(1, base + (task.structure_weight - 33) * 0.012)), 1)
        center_score = round(min(10, max(1, base + (task.center_weight - 33) * 0.01 - 0.3)), 1)
        stroke_order_score = round(min(10, max(1, base + (task.stroke_order_weight - 33) * 0.011)), 1)
        total_score = round((structure_score + center_score + stroke_order_score) / 3, 1)
        if total_score >= 8.5:
            tags = ["结构工整", "重心稳当", "笔法到位"]
            advice = "整体书写不错，结构稳定性和重心控制都比较好。注意主笔的舒展度和收放关系，多加练习让笔画更加流畅自然。"
        elif total_score >= 7.0:
            tags = ["结构基本正确", "重心略偏", "笔顺有待加强"]
            advice = "结构大体正确，但中宫略松，重心控制还有一些不稳定的地方。建议重点练习中宫收紧，注意各笔画之间的呼应关系。"
        elif total_score >= 5.0:
            tags = ["中宫松散", "重心不稳", "运笔生硬"]
            advice = "整体结构偏松散，重心不稳的问题比较明显。建议先从基本笔画入手，练习横平竖直，再逐步过渡到单字结构训练。"
        else:
            tags = ["结构失衡", "笔顺有误", "基础薄弱"]
            advice = "基础笔画和结构都需要从头打基础。建议从基本点画开始练习，先掌握正确的笔顺规则，再练习简单字形。"
        structure_obs = ("中宫收紧，横细竖粗特征明显" if structure_score >= 9.0 else "结构基本正确，但中宫略松" if structure_score >= 8.5 else "整体结构松散")
        center_obs = ("整体重心平稳，起笔收笔位置准确" if center_score >= 9.0 else "重心略偏左约 2%" if center_score >= 8.5 else "重心明显偏左")
        stroke_obs = ("笔顺正确，运笔流畅" if stroke_order_score >= 9.0 else "笔顺基本正确，个别笔画顺序可优化" if stroke_order_score >= 8.5 else "部分笔画顺序有误")
        thinking_steps = [
            {"step": 1, "title": "图像预处理", "detail": f"书法作业图像加载完成（作业 #{homework_id}）", "status": "done"},
            {"step": 2, "title": "文字区域检测", "detail": f"检测到 {3 + homework_id % 4} 个练习字区域", "status": "done"},
            {"step": 3, "title": "单字分割", "detail": "已完成", "status": "done"},
            {"step": 4, "title": "结构分析", "detail": structure_obs, "status": "done", "score": structure_score},
            {"step": 5, "title": "重心检测", "detail": center_obs, "status": "done", "score": center_score},
            {"step": 6, "title": "笔顺验证", "detail": stroke_obs, "status": "done", "score": stroke_order_score},
            {"step": 7, "title": "综合评分", "detail": f"综合评分为 {total_score} 分", "status": "done", "score": total_score},
        ]
        return {"total_score": total_score, "structure_score": structure_score, "center_score": center_score, "stroke_order_score": stroke_order_score, "issues": tags, "advice_text": advice, "compare_image_url": image_url, "thinking_steps": thinking_steps}

    @staticmethod
    def _build_qwen_result(db: Session, homework, task) -> dict:
        image_path = FileStorageService.resolve_upload_url(homework.image_url)
        practice_chars = [item.character for item in TaskRepository.list_characters(db, task.id)]
        result = QwenEvaluationService.score(image_path=image_path, practice_chars=practice_chars, task_title=task.title)
        def _clamp(v): return max(0, min(10, round(float(v), 1))) if v else 0.0
        def _safe(v): return str(v) if v else ""
        total_score = _clamp(result.get("total_score"))
        structure_score = _clamp(result.get("structure_score"))
        center_score = _clamp(result.get("center_score"))
        stroke_order_score = _clamp(result.get("stroke_order_score"))
        tags = result.get("tags", [])
        if not isinstance(tags, list):
            tags = []
        advice = result.get("advice", "") or ""
        raw_steps = result.get("thinking_steps", [])
        thinking_steps = None
        if raw_steps and isinstance(raw_steps, list):
            thinking_steps = []
            for s in raw_steps:
                step = {"step": int(s.get("step", 0)), "title": s.get("title", ""), "detail": s.get("detail", ""), "status": "done"}
                sc = s.get("score")
                if sc is not None:
                    try: step["score"] = round(float(sc), 1)
                    except: pass
                thinking_steps.append(step)
        return {"total_score": total_score, "structure_score": structure_score, "center_score": center_score, "stroke_order_score": stroke_order_score, "issues": tags, "advice_text": advice, "compare_image_url": homework.image_url, "thinking_steps": thinking_steps, "annotations": result.get("annotations", [])}

    @staticmethod
    def _build_openai_result(db: Session, homework, task) -> dict:
        # DEPRECATED: kept for reference
        image_path = FileStorageService.resolve_upload_url(homework.image_url)
        practice_chars = [item.character for item in TaskRepository.list_characters(db, task.id)]
        result = OpenAIEvaluationService.score(image_path=image_path, practice_chars=practice_chars, task_title=task.title)
        rounded_score = round(result.score, 1)
        thinking_steps = None
        if result.thinking_steps:
            thinking_steps = [{"step": s.step, "title": s.title, "detail": s.detail, "status": "done", **({"score": round(s.score, 1)} if s.score is not None else {})} for s in result.thinking_steps]
        return {"total_score": rounded_score, "structure_score": rounded_score, "center_score": rounded_score, "stroke_order_score": rounded_score, "issues": result.tags, "advice_text": result.advice, "compare_image_url": homework.image_url, "thinking_steps": thinking_steps}

    @staticmethod
    def start(db: Session, homework_id: int, provider: EvaluationProvider = EvaluationProvider.auto, force_refresh: bool = False) -> dict:
        homework = HomeworkRepository.get_by_id(db, homework_id)
        if not homework:
            raise HTTPException(status_code=404, detail="homework not found")
        existing = EvaluationRepository.get_by_homework_id(db, homework_id)
        resolved_provider = EvaluationService._resolve_provider(provider)
        if existing and not force_refresh:
            return {"status": existing.status, "homework_id": homework_id, "evaluation_id": existing.id, "provider": resolved_provider}
        task = TaskRepository.get_by_id(db, homework.task_id)
        if not task:
            raise HTTPException(status_code=404, detail="task not found")

        # 同步路径（Mock/OpenAI）
        if resolved_provider != EvaluationProvider.qwen:
            payload = EvaluationService._build_openai_result(db, homework, task) if resolved_provider == EvaluationProvider.openai else EvaluationService._build_mock_result(homework_id, task, image_url=homework.image_url)
            ov = FileStorageService.save_result_overlay(image_url=homework.image_url, scores={k: payload[k] for k in ("total_score", "structure_score", "center_score", "stroke_order_score")}, tags=payload.get("issues", []))
            if ov != homework.image_url:
                payload["compare_image_url"] = ov
            evaluation = EvaluationRepository.update_evaluation(db, existing, status="finished", **payload) if existing else EvaluationRepository.create_evaluation(db, homework_id=homework_id, status="finished", **payload)
            homework.status = "evaluated"
            HomeworkRepository.update_homework(db, homework)
            if not ReviewRepository.get_by_homework_id(db, homework_id):
                ReviewRepository.create_review(db, homework_id=homework_id, teacher_id=task.created_by, comment=None, final_score=payload["total_score"], review_status="pending")
            return {"status": "finished", "homework_id": homework_id, "evaluation_id": evaluation.id, "provider": resolved_provider}

        # 异步路径（Qwen）
        if existing:
            evaluation = EvaluationRepository.update_evaluation(db, existing, status="processing", total_score=0)
        else:
            evaluation = EvaluationRepository.create_evaluation(db, homework_id=homework_id, status="processing")

        def _run():
            try:
                from app.core.database import SessionLocal as _SL
                _db = _SL()
                try:
                    _hw = HomeworkRepository.get_by_id(_db, homework_id)
                    _task = TaskRepository.get_by_id(_db, homework.task_id)
                    if not _hw or not _task:
                        return
                    _payload = EvaluationService._build_qwen_result(_db, _hw, _task)
                    _ov = FileStorageService.save_result_overlay(image_url=_hw.image_url, scores={k: _payload[k] for k in ("total_score", "structure_score", "center_score", "stroke_order_score")}, tags=_payload.get("issues", []))
                    if _ov != _hw.image_url:
                        _payload["compare_image_url"] = _ov
                    _ev = EvaluationRepository.get_by_homework_id(_db, homework_id)
                    if _ev:
                        EvaluationRepository.update_evaluation(_db, _ev, status="finished", **_payload)
                        _hw.status = "evaluated"
                        HomeworkRepository.update_homework(_db, _hw)
                        if not ReviewRepository.get_by_homework_id(_db, homework_id):
                            ReviewRepository.create_review(_db, homework_id=homework_id, teacher_id=_task.created_by, comment=None, final_score=_payload["total_score"], review_status="pending")
                        _db.commit()
                finally:
                    _db.close()
            except Exception:
                import traceback; traceback.print_exc()
                try:
                    _ev2 = EvaluationRepository.get_by_homework_id(_db, homework_id)
                    if _ev2:
                        EvaluationRepository.update_evaluation(_db, _ev2, status="failed", advice_text="AI 评测异常，请稍后重试或切换 Mock 模式。")
                        _db.commit()
                except Exception:
                    pass

        threading.Thread(target=_run, daemon=True).start()
        return {"status": "processing", "homework_id": homework_id, "evaluation_id": evaluation.id, "provider": resolved_provider}

    @staticmethod
    def get_providers() -> dict:
        return {"qwen": {"enabled": QwenEvaluationService.is_configured(), "configured": settings.qwen_evaluation_enabled}, "mock": {"enabled": True}, "openai": {"enabled": False, "deprecated": True}}

    @staticmethod
    def get(db: Session, homework_id: int) -> dict:
        evaluation = EvaluationRepository.get_by_homework_id(db, homework_id)
        if not evaluation:
            raise HTTPException(status_code=404, detail="evaluation not found")
        homework = HomeworkRepository.get_by_id(db, homework_id)
        char = None
        if homework:
            task = TaskRepository.get_by_id(db, homework.task_id)
            if task:
                chars = [item.character for item in TaskRepository.list_characters(db, task.id)]
                char = chars[0] if chars else None
        return EvaluationService._serialize(evaluation, character=char)
