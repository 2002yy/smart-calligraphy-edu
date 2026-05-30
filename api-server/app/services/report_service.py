from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.database import utc_now
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
    def export_report(report_type: str, target_id: int, file_format: str) -> dict:
        return {
            "file_url": f"/reports/{report_type}_{target_id}.{file_format}",
            "generated_at": utc_now(),
        }
