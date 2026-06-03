"""Patch evaluation_service.py for async Qwen + providers endpoint"""
import os

fp = r"C:\Users\96967\Desktop\大创\code\api-server\app\services\evaluation_service.py"
with open(fp, encoding="utf-8") as f:
    content = f.read()

# 1. Add threading import
content = content.replace("import sqlite3", "import sqlite3\nimport threading")

# 2. _serialize: hardcoded finished -> evaluation.status
content = content.replace('"status": "finished",', '"status": evaluation.status,')

# 3. Replace start() async Qwen (use sentinel markers)
start_old = '''    @staticmethod
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

        # 生成叠加评分信息的 overlay 结果图
        overlay_url = FileStorageService.save_result_overlay(
            image_url=homework.image_url,
            scores={
                "total_score": payload["total_score"],
                "structure_score": payload["structure_score"],
                "center_score": payload["center_score"],
                "stroke_order_score": payload["stroke_order_score"],
            },
            tags=payload.get("issues", []),
        )
        if overlay_url != homework.image_url:
            payload["compare_image_url"] = overlay_url

        if existing:
            evaluation = EvaluationRepository.update_evaluation(db, existing, **payload)
        else:
            evaluation = EvaluationRepository.create_evaluation(db, homework_id=homework_id, **payload)

        homework.status = "evaluated"
        HomeworkRepository.update_homework(db, homework)

        # 自动创建批阅记录，让教师端立即可见
        existing_review = ReviewRepository.get_by_homework_id(db, homework_id)
        if not existing_review:
            ReviewRepository.create_review(
                db,
                homework_id=homework_id,
                teacher_id=task.created_by,
                comment=None,
                final_score=payload["total_score"],
                review_status="pending",
            )

        return {
            "status": "finished",
            "homework_id": homework_id,
            "evaluation_id": evaluation.id,
            "provider": resolved_provider,
        }'''

start_new = '''    @staticmethod
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
            return {"status": existing.status, "homework_id": homework_id, "evaluation_id": existing.id, "provider": resolved_provider}

        task = TaskRepository.get_by_id(db, homework.task_id)
        if not task:
            raise HTTPException(status_code=404, detail="task not found")

        # ── 同步路径（Mock / OpenAI / 旧版）──
        if resolved_provider != EvaluationProvider.qwen:
            if resolved_provider == EvaluationProvider.openai:
                payload = EvaluationService._build_openai_result(db, homework, task)
            else:
                payload = EvaluationService._build_mock_result(homework_id, task, image_url=homework.image_url)
            overlay_url = FileStorageService.save_result_overlay(
                image_url=homework.image_url,
                scores={k: payload[k] for k in ("total_score", "structure_score", "center_score", "stroke_order_score")},
                tags=payload.get("issues", []),
            )
            if overlay_url != homework.image_url:
                payload["compare_image_url"] = overlay_url
            if existing:
                evaluation = EvaluationRepository.update_evaluation(db, existing, status="finished", **payload)
            else:
                evaluation = EvaluationRepository.create_evaluation(db, homework_id=homework_id, status="finished", **payload)
            homework.status = "evaluated"
            HomeworkRepository.update_homework(db, homework)
            if not ReviewRepository.get_by_homework_id(db, homework_id):
                ReviewRepository.create_review(db, homework_id=homework_id, teacher_id=task.created_by, comment=None, final_score=payload["total_score"], review_status="pending")
            return {"status": "finished", "homework_id": homework_id, "evaluation_id": evaluation.id, "provider": resolved_provider}

        # ── Qwen 异步路径 ──
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
                    _ov = FileStorageService.save_result_overlay(
                        image_url=_hw.image_url,
                        scores={k: _payload[k] for k in ("total_score", "structure_score", "center_score", "stroke_order_score")},
                        tags=_payload.get("issues", []),
                    )
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

        threading.Thread(target=_run, daemon=True).start()
        return {"status": "processing", "homework_id": homework_id, "evaluation_id": evaluation.id, "provider": resolved_provider}'''

content = content.replace(start_old, start_new)

# 4. Add providers method before get()
old_get = '''    @staticmethod
    def get(db: Session, homework_id: int) -> dict:'''
new_get = '''    @staticmethod
    def get_providers() -> dict:
        return {
            "qwen": {"enabled": QwenEvaluationService.is_configured(), "configured": settings.qwen_evaluation_enabled},
            "mock": {"enabled": True},
            "openai": {"enabled": False, "deprecated": True},
        }

    @staticmethod
    def get(db: Session, homework_id: int) -> dict:'''
content = content.replace(old_get, new_get)

with open(fp, "w", encoding="utf-8") as f:
    f.write(content)
print("done")
