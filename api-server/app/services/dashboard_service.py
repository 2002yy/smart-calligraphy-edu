from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories import ClassMemberRepository, ClassroomRepository, EvaluationRepository, HomeworkRepository, TaskRepository


class DashboardService:
    @staticmethod
    def build_class_dashboard(db: Session, class_id: int) -> dict:
        classroom = ClassroomRepository.get_by_id(db, class_id)
        if not classroom:
            raise HTTPException(status_code=404, detail="class not found")

        tasks = TaskRepository.list_tasks(db, class_id=class_id)
        task_ids = [item.id for item in tasks]
        homework_list = HomeworkRepository.list_homework(db, task_ids=task_ids) if task_ids else []
        evaluations = EvaluationRepository.list_by_homework_ids(db, [item.id for item in homework_list])

        evaluation_map = {item.homework_id: item for item in evaluations}
        scored = [evaluation_map[item.id] for item in homework_list if item.id in evaluation_map]
        score_values = [item.total_score for item in scored]
        avg_score = round(sum(score_values) / len(score_values), 2) if score_values else 0.0

        members = ClassMemberRepository.list_members(db, class_id)
        expected_homework = len(members) * len(tasks)
        submit_rate = round(len(homework_list) / expected_homework, 2) if expected_homework else 0.0

        issue_pool: list[str] = []
        for item in scored:
            issue_pool.extend(item.issues_json or [])
        top_issues = sorted(set(issue_pool), key=lambda issue: issue_pool.count(issue), reverse=True)[:5]

        return {
            "class_id": classroom.id,
            "class_name": classroom.name,
            "student_count": len(members),
            "task_count": len(tasks),
            "homework_count": len(homework_list),
            "evaluated_count": len(scored),
            "avg_score": avg_score,
            "submit_rate": submit_rate,
            "top_issues": top_issues,
        }
