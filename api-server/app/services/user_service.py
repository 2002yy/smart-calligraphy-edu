from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories import EvaluationRepository, HomeworkRepository, UserRepository


class UserService:
    @staticmethod
    def get_user(db: Session, user_id: int, current_user: dict | None = None) -> dict:
        if current_user and current_user.get("role") == "student" and current_user["id"] != user_id:
            raise HTTPException(status_code=403, detail="学生只能查看自己的信息")
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="user not found")
        return {
            "id": user.id,
            "name": user.name,
            "role": user.role,
        }

    @staticmethod
    def get_growth(db: Session, user_id: int, current_user: dict | None = None) -> dict:
        if current_user and current_user.get("role") == "student" and current_user["id"] != user_id:
            raise HTTPException(status_code=403, detail="学生只能查看自己的成长数据")
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="user not found")

        homework_list = HomeworkRepository.list_homework(db, student_id=user_id)
        evaluations = EvaluationRepository.list_by_homework_ids(db, [item.id for item in homework_list])
        scores = [item.total_score for item in evaluations]
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0

        recent = list(reversed(evaluations[:5]))
        recent_scores = [e.total_score for e in recent]
        recent_labels = []
        for e in recent:
            if e.created_at:
                recent_labels.append(e.created_at.strftime("%m/%d"))
            else:
                recent_labels.append(f"#{e.homework_id}")

        return {
            "user_id": user_id,
            "avg_score": avg_score,
            "recent_scores": recent_scores,
            "recent_labels": recent_labels,
        }
