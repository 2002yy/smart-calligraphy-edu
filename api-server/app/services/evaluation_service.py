from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories import EvaluationRepository, HomeworkRepository, TaskRepository
from app.schemas.evaluation import EvaluationProvider
from app.services.file_storage_service import FileStorageService
from app.services.openai_evaluation_service import OpenAIEvaluationService  # DEPRECATED
from app.services.qwen_evaluation_service import QwenEvaluationService


class EvaluationService:
    @staticmethod
    def _serialize(evaluation) -> dict:
        tags = evaluation.issues_json or []
        return {
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
            "status": "finished",
            "created_at": evaluation.created_at,
        }

    @staticmethod
    def _resolve_provider(requested_provider: EvaluationProvider) -> EvaluationProvider:
        if requested_provider == EvaluationProvider.mock:
            return EvaluationProvider.mock

        if requested_provider == EvaluationProvider.qwen:
            if not QwenEvaluationService.is_configured():
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Qwen 评测未启用。请设置 QWEN_EVALUATION_ENABLED=true "
                        "并配置 QWEN_API_KEY（阿里云百炼 API Key）。"
                    ),
                )
            return EvaluationProvider.qwen

        # DEPRECATED: kept for reference
        if requested_provider == EvaluationProvider.openai:
            if not OpenAIEvaluationService.is_configured():
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "OpenAI evaluation is not enabled. Please set OPENAI_EVALUATION_ENABLED=true "
                        "and configure OPENAI_API_KEY."
                    ),
                )
            return EvaluationProvider.openai

        # auto: 优先使用 Qwen，其次 OpenAI（如果配置了），最后 Mock
        if QwenEvaluationService.is_configured():
            return EvaluationProvider.qwen
        if settings.evaluation_provider == EvaluationProvider.openai.value and OpenAIEvaluationService.is_configured():
            return EvaluationProvider.openai
        return EvaluationProvider.mock

    @staticmethod
    def _build_mock_result(homework_id: int, task, image_url: str = "") -> dict:
        # Mock 评分：使用 0-10 分制（保留一位小数），校准锚点与 Qwen prompt 对齐
        base = float((82 + homework_id % 8) / 10)
        structure_score = round(min(10, base + task.structure_weight * 0.008), 1)
        center_score = round(min(10, base + task.center_weight * 0.006 - 0.15), 1)
        stroke_order_score = round(min(10, base + task.stroke_order_weight * 0.007), 1)
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

        region_count = 3 + homework_id % 4
        char_examples = [
            "「永」「大」「木」「中」",
            "「人」「天」「心」「之」",
            "「山」「水」「日」「月」",
            "「上」「下」「左」「右」",
        ]
        example_chars = char_examples[homework_id % len(char_examples)]

        structure_obs = (
            "中宫收紧，横细竖粗特征明显，结构稳定性良好"
            if structure_score >= 9.0
            else "结构基本正确，但中宫略松，需加强横向笔画控制"
            if structure_score >= 8.5
            else "整体结构松散，建议重点练习中宫收紧与横平竖直"
        )
        center_obs = (
            "整体重心平稳，起笔收笔位置准确"
            if center_score >= 9.0
            else "重心略偏左约 2%，建议书写时注意起笔位置"
            if center_score >= 8.5
            else "重心明显偏左，起笔位置需整体右移"
        )
        stroke_obs = (
            "笔顺正确，运笔流畅，无需调整"
            if stroke_order_score >= 9.0
            else "笔顺基本正确，个别笔画顺序可优化"
            if stroke_order_score >= 8.5
            else "部分笔画顺序有误，建议参照标准笔顺练习"
        )

        thinking_steps = [
            {"step": 1, "title": "图像预处理", "detail": f"书法作业图像加载完成（作业 #{homework_id}）", "status": "done"},
            {"step": 2, "title": "文字区域检测", "detail": f"检测到 {region_count} 个练习字区域，已完成定位", "status": "done"},
            {"step": 3, "title": "单字分割", "detail": f"完成单字分割与对齐：{example_chars}", "status": "done"},
            {
                "step": 4, "title": "结构分析",
                "detail": f"结构评分为 {structure_score} 分，{structure_obs}",
                "status": "done", "score": structure_score,
            },
            {
                "step": 5, "title": "重心检测",
                "detail": f"重心评分为 {center_score} 分，{center_obs}",
                "status": "done", "score": center_score,
            },
            {
                "step": 6, "title": "笔顺验证",
                "detail": f"笔顺评分为 {stroke_order_score} 分，{stroke_obs}",
                "status": "done", "score": stroke_order_score,
            },
            {
                "step": 7, "title": "综合评分",
                "detail": f"综合评分为 {total_score} 分，生成最终评分与练习建议",
                "status": "done", "score": total_score,
            },
        ]

        return {
            "total_score": total_score,
            "structure_score": structure_score,
            "center_score": center_score,
            "stroke_order_score": stroke_order_score,
            "issues": tags,
            "advice_text": advice,
            "compare_image_url": image_url,
            "thinking_steps": thinking_steps,
        }

    @staticmethod
    def _build_qwen_result(db: Session, homework, task) -> dict:
        """调用 Qwen3.5-Plus 视觉模型进行书法评分，包含各维度观察与修改建议。"""
        image_path = FileStorageService.resolve_upload_url(homework.image_url)
        practice_chars = [item.character for item in TaskRepository.list_characters(db, task.id)]
        result = QwenEvaluationService.score(
            image_path=image_path,
            practice_chars=practice_chars,
            task_title=task.title,
        )

        def _clamp(val):
            try:
                return max(0, min(10, round(float(val), 1)))
            except (ValueError, TypeError):
                return 0.0

        def _safe_str(val, default=""):
            return str(val) if val else default

        total_score = _clamp(result["total_score"])
        structure_score = _clamp(result["structure_score"])
        center_score = _clamp(result["center_score"])
        stroke_order_score = _clamp(result["stroke_order_score"])
        structure_obs = _safe_str(result.get("structure_observation"))
        structure_sug = _safe_str(result.get("structure_suggestion"))
        center_obs = _safe_str(result.get("center_observation"))
        center_sug = _safe_str(result.get("center_suggestion"))
        stroke_obs = _safe_str(result.get("stroke_order_observation"))
        stroke_sug = _safe_str(result.get("stroke_order_suggestion"))

        tags = result.get("tags", [])
        if not isinstance(tags, list):
            tags = []

        advice = result.get("advice", "") or ""
        raw_steps = result.get("thinking_steps", [])

        # 将各维度的观察和建议拼入 thinking_steps 的 detail 中
        thinking_steps = None
        if raw_steps and isinstance(raw_steps, list):
            thinking_steps = []
            for s in raw_steps:
                step_num = int(s.get("step", 0))
                title = s.get("title", "")
                detail = s.get("detail", "")
                step_score = s.get("score")

                # 为结构/重心/笔顺三步补充观察+修改建议（合并到一条detail中）
                if step_num == 4:
                    parts = []
                    if structure_obs:
                        parts.append(f"观察：{structure_obs}")
                    if structure_sug:
                        parts.append(f"建议：{structure_sug}")
                    if parts:
                        detail = " | ".join(parts)
                if step_num == 5:
                    parts = []
                    if center_obs:
                        parts.append(f"观察：{center_obs}")
                    if center_sug:
                        parts.append(f"建议：{center_sug}")
                    if parts:
                        detail = " | ".join(parts)
                if step_num == 6:
                    parts = []
                    if stroke_obs:
                        parts.append(f"观察：{stroke_obs}")
                    if stroke_sug:
                        parts.append(f"建议：{stroke_sug}")
                    if parts:
                        detail = " | ".join(parts)

                step = {
                    "step": step_num,
                    "title": title,
                    "detail": detail,
                    "status": "done",
                }
                if step_score is not None:
                    try:
                        step["score"] = round(float(step_score), 1)
                    except (ValueError, TypeError):
                        pass
                thinking_steps.append(step)

        return {
            "total_score": total_score,
            "structure_score": structure_score,
            "center_score": center_score,
            "stroke_order_score": stroke_order_score,
            "issues": tags,
            "advice_text": advice,
            "compare_image_url": homework.image_url,
            "thinking_steps": thinking_steps,
        }

    @staticmethod
    def _build_openai_result(db: Session, homework, task) -> dict:
        # DEPRECATED: kept for reference. Use _build_qwen_result instead.
        image_path = FileStorageService.resolve_upload_url(homework.image_url)
        practice_chars = [item.character for item in TaskRepository.list_characters(db, task.id)]
        result = OpenAIEvaluationService.score(
            image_path=image_path,
            practice_chars=practice_chars,
            task_title=task.title,
        )
        rounded_score = round(result.score, 1)

        thinking_steps = None
        if result.thinking_steps:
            thinking_steps = [
                {
                    "step": s.step,
                    "title": s.title,
                    "detail": s.detail,
                    "status": "done",
                    **({"score": round(s.score, 1)} if s.score is not None else {}),
                }
                for s in result.thinking_steps
            ]

        return {
            "total_score": rounded_score,
            "structure_score": rounded_score,
            "center_score": rounded_score,
            "stroke_order_score": rounded_score,
            "issues": result.tags,
            "advice_text": result.advice,
            "compare_image_url": homework.image_url,
            "thinking_steps": thinking_steps,
        }

    @staticmethod
    def start(
        db: Session,
        homework_id: int,
        provider: EvaluationProvider = EvaluationProvider.auto,
        force_refresh: bool = False,
    ) -> dict:
        homework = HomeworkRepository.get_by_id(db, homework_id)
        if not homework:
            raise HTTPException(status_code=404, detail="homework not found")

        existing = EvaluationRepository.get_by_homework_id(db, homework_id)
        resolved_provider = EvaluationService._resolve_provider(provider)

        if existing and not force_refresh:
            return {
                "status": "finished",
                "homework_id": homework_id,
                "evaluation_id": existing.id,
                "provider": resolved_provider,
            }

        task = TaskRepository.get_by_id(db, homework.task_id)
        if not task:
            raise HTTPException(status_code=404, detail="task not found")

        if resolved_provider == EvaluationProvider.qwen:
            payload = EvaluationService._build_qwen_result(db, homework, task)
        elif resolved_provider == EvaluationProvider.openai:
            # DEPRECATED: kept for reference
            payload = EvaluationService._build_openai_result(db, homework, task)
        else:
            payload = EvaluationService._build_mock_result(homework_id, task, image_url=homework.image_url)

        if existing:
            evaluation = EvaluationRepository.update_evaluation(db, existing, **payload)
        else:
            evaluation = EvaluationRepository.create_evaluation(db, homework_id=homework_id, **payload)

        homework.status = "evaluated"
        HomeworkRepository.update_homework(db, homework)

        return {
            "status": "finished",
            "homework_id": homework_id,
            "evaluation_id": evaluation.id,
            "provider": resolved_provider,
        }

    @staticmethod
    def get(db: Session, homework_id: int) -> dict:
        evaluation = EvaluationRepository.get_by_homework_id(db, homework_id)
        if not evaluation:
            raise HTTPException(status_code=404, detail="evaluation not found")
        return EvaluationService._serialize(evaluation)
