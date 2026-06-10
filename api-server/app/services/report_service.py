from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.database import utc_now
from collections import Counter

from app.core.evaluation_tags import ISSUE_TAGS, TAG_CATEGORIES
from app.repositories import ClassMemberRepository, ClassroomRepository, EvaluationRepository, HomeworkRepository, TaskRepository, UserRepository


class ReportService:
    @staticmethod
    def student_report(db: Session, student_id: int) -> dict:
        student = UserRepository.get_by_id(db, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="student not found")

        homework_list = HomeworkRepository.list_homework(db, student_id=student_id)
        evaluations = EvaluationRepository.list_by_homework_ids(db, [item.id for item in homework_list])
        scores = [item.total_score for item in evaluations]
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0

        return {
            "student_id": student_id,
            "homework_count": len(homework_list),
            "evaluated_count": len(evaluations),
            "avg_score": avg_score,
        }

    @staticmethod
    def class_report(db: Session, class_id: int) -> dict:
        classroom = ClassroomRepository.get_by_id(db, class_id)
        if not classroom:
            raise HTTPException(status_code=404, detail="class not found")

        members = ClassMemberRepository.list_members(db, class_id)
        tasks = TaskRepository.list_tasks(db, class_id=class_id)
        task_ids = [item.id for item in tasks]
        homework_list = HomeworkRepository.list_homework(db, task_ids=task_ids) if task_ids else []
        evaluations = EvaluationRepository.list_by_homework_ids(db, [item.id for item in homework_list])
        scores = [item.total_score for item in evaluations]
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0

        return {
            "class_id": class_id,
            "student_count": len(members),
            "task_count": len(tasks),
            "homework_count": len(homework_list),
            "evaluated_count": len(evaluations),
            "avg_score": avg_score,
        }

    @staticmethod
    def student_tag_trend(db: Session, student_id: int) -> dict:
        """获取学生标签变化趋势。

        返回按时间排序的评测记录、高频问题标签、以及有改善趋势的标签。
        """
        student = UserRepository.get_by_id(db, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="student not found")

        homework_list = HomeworkRepository.list_homework(db, student_id=student_id)
        evaluations = EvaluationRepository.list_by_homework_ids(db, [item.id for item in homework_list])

        # 按 submitted_at 排序（升序）
        eval_map = {ev.homework_id: ev for ev in evaluations}
        sorted_hw = sorted(homework_list, key=lambda h: h.submitted_at or h.created_at)
        records = []
        for hw in sorted_hw:
            ev = eval_map.get(hw.id)
            if ev and ev.status == "finished" and ev.issues_json:
                records.append({
                    "homework_id": hw.id,
                    "created_at": hw.submitted_at or hw.created_at,
                    "score": ev.total_score,
                    "tags": ev.issues_json,
                })

        # 高频问题标签（仅 issue 标签，按频次降序）
        issue_counter: Counter = Counter()
        for r in records:
            for tag in r["tags"]:
                if tag in ISSUE_TAGS:
                    issue_counter[tag] += 1
        frequent_issue_tags = [
            {"tag": tag, "count": count}
            for tag, count in issue_counter.most_common()
        ]

        # 改善分析：将记录分为前一半（早期）和后一半（近期）
        n = len(records)
        improved_tags = []
        if n >= 4:
            mid = n // 2
            early = records[:mid]
            recent = records[mid:]

            early_counter: Counter = Counter()
            recent_counter: Counter = Counter()
            for r in early:
                for tag in r["tags"]:
                    if tag in ISSUE_TAGS:
                        early_counter[tag] += 1
            for r in recent:
                for tag in r["tags"]:
                    if tag in ISSUE_TAGS:
                        recent_counter[tag] += 1

            # 只在早期出现过至少 2 次且后期次数减少的标签才视为"改善"
            for tag, early_count in early_counter.most_common():
                recent_count = recent_counter.get(tag, 0)
                if early_count >= 2 and recent_count < early_count:
                    improved_tags.append({
                        "tag": tag,
                        "previous_count": early_count,
                        "recent_count": recent_count,
                    })

        return {
            "student_id": student_id,
            "records": records,
            "frequent_issue_tags": frequent_issue_tags,
            "improved_tags": improved_tags,
        }

    @staticmethod
    def export_report(report_type: str, target_id: int, file_format: str) -> dict:
        return {
            "file_url": f"/reports/{report_type}_{target_id}.{file_format}",
            "generated_at": utc_now(),
        }
