export interface CurrentUser {
  id: number;
  username: string;
  name: string;
  role: string;
  school_name?: string | null;
  avatar_url?: string | null;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: CurrentUser;
}

export interface StudentTask {
  id: number;
  course_id: number;
  class_id: number;
  title: string;
  description?: string | null;
  practice_chars: string[];
  structure_weight: number;
  center_weight: number;
  stroke_order_weight: number;
  deadline?: string | null;
  created_by: number;
  created_at?: string | null;
}

export interface Homework {
  id: number;
  task_id: number;
  student_id: number;
  status: string;
  image_url: string;
  processed_image_url?: string | null;
  submitted_at?: string | null;
}

export interface MobileResultDetail {
  name: string;
  score: number;
  comment: string;
}

export interface MobileResult {
  homework_id: number;
  score: number;
  level: string;
  summary: string;
  details: MobileResultDetail[];
  tags: string[];
  image_url?: string | null;
  status: string;
  created_at?: string | null;
}

export interface Growth {
  user_id: number;
  avg_score: number;
  recent_scores: number[];
  recent_labels: string[];
}

export interface EvaluationStart {
  status: string;
  homework_id: number;
  evaluation_id: number;
  provider: "auto" | "mock" | "openai" | "qwen";
}
